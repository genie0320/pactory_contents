"""Tests for Ingestion Scanner and Multimodal PDF Processor (Milestone 2)."""

from pathlib import Path
import pytest
from PIL import Image, ImageDraw

from pypdf import PdfWriter
from src.config import AppConfig, ImageFilterSettings, PathSettings
from src.ingestion.pdf_processor import PDFProcessor
from src.ingestion.scanner import IngestionScanner
from src.ingestion.text_normalizer import clean_boilerplate, extract_author_and_date
from src.models import ArticleStatus
from src.storage.db import init_db
from src.storage.repository import StorageRepository


def create_sample_pdf_with_image(
    file_path: Path,
    title: str,
    author: str,
    published_date: str,
    include_image: bool = True,
    img_width: int = 400,
    img_height: int = 300,
) -> None:
    """Helper to generate a real PDF article with text, boilerplate, and embedded images."""
    # Create image file
    images = []
    if include_image:
        img = Image.new("RGB", (img_width, img_height), color=(73, 109, 137))
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), f"Sample Chart for {title}", fill=(255, 255, 0))
        images.append(img)
    else:
        # 1x1 dummy to make a valid 1-page PDF if needed
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        images.append(img)

    temp_img_pdf = file_path.parent / f"tmp_{file_path.name}"
    images[0].save(temp_img_pdf, "PDF", resolution=100.0)

    # Wrap with reader/writer and add metadata/annotation text
    writer = PdfWriter()
    with open(temp_img_pdf, "rb") as f:
        writer.append(f)

    # Set metadata
    writer.add_metadata({
        "/Title": title,
        "/Author": author,
    })

    with open(file_path, "wb") as f_out:
        writer.write(f_out)

    if temp_img_pdf.exists():
        temp_img_pdf.unlink()


def test_boilerplate_stripping():
    raw_text = """
저자: 김철수
발행일: 2025.03.15

업무 고민 나누면, 해결책이 온다! 퍼블리 뉴스레터 로 꾸준히 성장하기
본문 시작합니다. 이것은 중요한 아티클 내용입니다.
프로필 더 보기
© 모든 저작권은 해당 콘텐츠 제공자 또는 회사에 있습니다.
"""
    cleaned = clean_boilerplate(raw_text)
    assert "퍼블리 뉴스레터" not in cleaned
    assert "프로필 더 보기" not in cleaned
    assert "저작권은 해당 콘텐츠" not in cleaned
    assert "본문 시작합니다. 이것은 중요한 아티클 내용입니다." in cleaned

    author, date = extract_author_and_date(raw_text)
    assert author == "김철수"
    assert date == "2025-03-15"


def test_filename_parsing():
    doc_id, title = IngestionScanner.parse_filename("8219_그때 그거 어디서 정했죠.pdf")
    assert doc_id == "8219"
    assert title == "그때 그거 어디서 정했죠"

    doc_id2, title2 = IngestionScanner.parse_filename("unprefixed_article.md")
    assert doc_id2 is None
    assert title2 == "unprefixed_article"


def test_10_sample_articles_ingestion(tmp_path: Path):
    """
    Milestone 2 Verification Criteria:
    샘플 PDF 10종 투입 시 data/processed/texts/{doc_id}.md와
    data/processed/assets/{doc_id}/에 정제 본문 및 이미지가 누락 없이 분리 저장됨
    """
    inbox_dir = tmp_path / "inbox"
    archive_dir = tmp_path / "archive"
    processed_dir = tmp_path / "processed"
    index_dir = tmp_path / "index"
    db_path = index_dir / "catalog.db"

    init_db(db_path)
    config = AppConfig(
        paths=PathSettings(
            data_dir=tmp_path,
            inbox_dir=inbox_dir,
            archive_dir=archive_dir,
            processed_dir=processed_dir,
            texts_dir=processed_dir / "texts",
            metadata_dir=processed_dir / "metadata",
            assets_dir=processed_dir / "assets",
            index_dir=index_dir,
            db_path=db_path,
            outputs_dir=tmp_path / "outputs",
        ),
        image_filter=ImageFilterSettings(min_width=250, min_height=150),
    )
    config.ensure_directories()
    repo = StorageRepository(db_path=db_path, processed_dir=processed_dir)
    scanner = IngestionScanner(config=config, repo=repo)

    # Create 10 sample PDF articles in inbox
    sample_docs = []
    for i in range(1, 11):
        doc_id = f"820{i}"
        title = f"테스트 아티클 제목 {i}"
        author = f"저자 {i}"
        date = f"2025-02-{i:02d}"
        file_name = f"{doc_id}_{title}.pdf"
        file_path = inbox_dir / file_name

        # Even-numbered articles include an eligible visual asset (> 250x150)
        has_image = (i % 2 == 0)
        create_sample_pdf_with_image(
            file_path=file_path,
            title=title,
            author=author,
            published_date=date,
            include_image=has_image,
            img_width=400 if has_image else 100,  # 100 will be filtered out by min_width=250
            img_height=300 if has_image else 100,
        )
        sample_docs.append((doc_id, title, has_image))

    # Run inbox scanner
    records = scanner.scan_inbox(inbox_dir=inbox_dir, move_archive=False)

    assert len(records) == 10

    # Verification: check all 10 articles in texts/ and assets/
    for doc_id, title, has_image in sample_docs:
        # 1. Cleaned text exists in data/processed/texts/{doc_id}.md
        text_file = processed_dir / "texts" / f"{doc_id}.md"
        assert text_file.exists(), f"Text file missing for {doc_id}"

        # 2. Database record exists and status is INGESTED
        article_record = repo.get_article(doc_id)
        assert article_record is not None
        assert article_record.status == ArticleStatus.INGESTED
        assert article_record.title == title

        # 3. Assets directory and manifest.json if image was valid
        if has_image:
            doc_assets_dir = processed_dir / "assets" / doc_id
            manifest_file = doc_assets_dir / "manifest.json"
            assert doc_assets_dir.exists(), f"Assets dir missing for {doc_id}"
            assert manifest_file.exists(), f"Manifest file missing for {doc_id}"
            assert article_record.image_count >= 1

    # Test duplicate check: re-scanning inbox without force should return existing without re-processing
    re_records = scanner.scan_inbox(inbox_dir=inbox_dir, force=False)
    assert len(re_records) == 10
