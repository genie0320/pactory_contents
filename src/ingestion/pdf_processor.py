"""PDF multimodal processor: text extraction, boilerplate cleaning, and image/caption extraction."""

from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple
import io
import re
from PIL import Image
from pypdf import PdfReader

from src.config import ImageFilterSettings
from src.ingestion.text_normalizer import clean_boilerplate, extract_author_and_date
from src.models import VisualAssetItem


class PDFProcessor:
    """Extracts cleaned text and visual assets (images/charts) with captions from PDF articles."""

    def __init__(self, image_filter: Optional[ImageFilterSettings] = None):
        self.filter = image_filter or ImageFilterSettings()

    def process_pdf(
        self,
        pdf_path: Path,
        doc_id: str,
        assets_output_dir: Path,
    ) -> Tuple[str, str, str, str, List[VisualAssetItem]]:
        """
        Process a PDF article.
        Returns:
            (cleaned_markdown, title, author, published_date, visual_assets)
        """
        reader = PdfReader(str(pdf_path))
        num_pages = len(reader.pages)

        page_texts: List[str] = []
        visual_assets: List[VisualAssetItem] = []
        assets_output_dir.mkdir(parents=True, exist_ok=True)
        for old_png in assets_output_dir.glob("*.png"):
            try:
                old_png.unlink()
            except Exception:
                pass

        full_raw_text = ""

        # First pass: collect raw texts and extract author/date from page 1
        for page_idx, page in enumerate(reader.pages):
            raw_text = page.extract_text() or ""
            full_raw_text += f"\n{raw_text}"
            page_texts.append(raw_text)

        author, published_date = extract_author_and_date(full_raw_text)

        # Infer title from page 1 or document metadata
        doc_title = ""
        if reader.metadata and reader.metadata.title:
            doc_title = str(reader.metadata.title).strip()

        if not doc_title and page_texts:
            first_page_lines = [line.strip() for line in page_texts[0].split("\n") if line.strip()]
            for line in first_page_lines:
                if len(line) > 3 and not any(kw in line for kw in ["저자", "발행일", "콘텐츠", "뉴스레터", "http"]):
                    doc_title = line
                    break

        # Second pass: process each page for images and captions
        final_pages_md: List[str] = []
        seen_image_hashes: set[str] = set()

        for page_idx, page in enumerate(reader.pages):
            page_no = page_idx + 1
            page_raw = page_texts[page_idx]
            cleaned_page_text = clean_boilerplate(page_raw)

            # Find potential captions on this page: lines with '║' or '©'
            candidate_captions: List[str] = []
            for line in cleaned_page_text.split("\n"):
                stripped = line.strip()
                if "║" in stripped or ("©" in stripped and len(stripped) < 80):
                    candidate_captions.append(stripped)

            page_images = self._extract_page_images(
                page=page,
                page_no=page_no,
                doc_id=doc_id,
                assets_dir=assets_output_dir,
                candidate_captions=candidate_captions,
                seen_image_hashes=seen_image_hashes,
            )
            visual_assets.extend(page_images)

            # Inject image markdown links into page text
            page_md = cleaned_page_text
            if page_images:
                img_md_blocks = []
                for img in page_images:
                    # Markdown link with relative path to assets
                    rel_path = f"../assets/{doc_id}/{Path(img.file_path).name}"
                    caption_text = img.caption or f"이미지 p{page_no}"
                    img_md_blocks.append(f"\n![{caption_text}]({rel_path})\n*{caption_text}*\n")

                page_md = "\n".join(img_md_blocks) + "\n" + page_md

            final_pages_md.append(page_md)

        full_cleaned_text = "\n\n---\n\n".join(final_pages_md).strip()

        # If document title still empty, fallback
        if not doc_title:
            doc_title = f"Article_{doc_id}"

        return full_cleaned_text, doc_title, author, published_date, visual_assets

    def _extract_page_images(
        self,
        page,
        page_no: int,
        doc_id: str,
        assets_dir: Path,
        candidate_captions: List[str],
        seen_image_hashes: Optional[set] = None,
    ) -> List[VisualAssetItem]:
        """Extract valid embedded images matching size and aspect ratio thresholds, deduplicating identical images."""
        import hashlib

        extracted: List[VisualAssetItem] = []
        img_idx = 1
        caption_idx = 0

        # Attempt to read images from page.images (pypdf feature)
        try:
            images = list(getattr(page, "images", []))
        except Exception:
            images = []

        for img_obj in images:
            try:
                # Content MD5 deduplication: skip if identical image was already extracted in this document
                img_data = img_obj.data
                img_hash = hashlib.md5(img_data).hexdigest()
                if seen_image_hashes is not None and img_hash in seen_image_hashes:
                    continue

                # Open with Pillow
                pil_img = Image.open(BytesIO(img_data))
                width, height = pil_img.size

                # Size & aspect ratio filters
                if width < self.filter.min_width or height < self.filter.min_height:
                    continue

                aspect_ratio = width / float(height) if height > 0 else 0
                if aspect_ratio < self.filter.min_aspect_ratio or aspect_ratio > self.filter.max_aspect_ratio:
                    continue

                asset_id = f"img_p{page_no:02d}_{img_idx:02d}"
                file_name = f"{asset_id}.png"
                save_path = assets_dir / file_name

                # Convert to RGB if RGBA/P for consistent PNG saving
                if pil_img.mode in ("RGBA", "P"):
                    pil_img = pil_img.convert("RGBA")
                else:
                    pil_img = pil_img.convert("RGB")

                pil_img.save(save_path, format="PNG")

                if seen_image_hashes is not None:
                    seen_image_hashes.add(img_hash)

                # Match caption if available
                caption = ""
                if caption_idx < len(candidate_captions):
                    caption = candidate_captions[caption_idx]
                    caption_idx += 1

                extracted.append(
                    VisualAssetItem(
                        asset_id=asset_id,
                        page_no=page_no,
                        file_path=f"{doc_id}/{file_name}",
                        caption=caption,
                        width=width,
                        height=height,
                    )
                )
                img_idx += 1
            except Exception:
                continue

        return extracted
