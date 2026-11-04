"""Text normalization and boilerplate removal for articles."""

import re
from typing import Optional, Tuple

# Patterns for boilerplate removal
BOILERPLATE_PATTERNS = [
    r"업무\s*고민\s*나누면,\s*해결책이\s*온다!.*?(?=[\r\n]|$)",
    r"퍼블리\s*뉴스레터\s*로\s*꾸준히\s*성장하기.*?(?=[\r\n]|$)",
    r"프로필\s*더\s*보기.*?(?=[\r\n]|$)",
    r"©\s*모든\s*저작권은\s*해당\s*콘텐츠\s*제공자\s*또는.*?(?=[\r\n]|$)",
    r"이\s*콘텐츠의\s*저작권은.*?(?=[\r\n]|$)",
    r"무단\s*전재\s*및\s*재배포를\s*금합니다.*?(?=[\r\n]|$)",
    r"^\s*\d+\s*/\s*\d+\s*$",  # Page numbers like "1 / 15"
    r"^\s*-\s*\d+\s*-\s*$",    # Page numbers like "- 1 -"
]

AUTHOR_PATTERNS = [
    r"(?:저자|작성자|글|에디터|Author)[:\s]+([^\r\n,]+)",
    r"\[(?:저자|작성자|글)[:\s]*([^\]]+)\]",
]

DATE_PATTERNS = [
    r"(?:발행일|콘텐츠\s*발행일|게시일|Published)[:\s*]*(\d{4}[.-]\d{1,2}[.-]\d{1,2})",
    r"\[(?:콘텐츠\s*)?발행일[:\s]*(\d{4}[.-]\d{1,2}[.-]\d{1,2})\]",
    r"\*?\s*발행일[:\s]*(\d{4}[.-]\d{1,2}[.-]\d{1,2})",
]


def clean_boilerplate(text: str) -> str:
    """Strip repeated newsletter banners, footers, and copyright notices."""
    cleaned = text
    for pat in BOILERPLATE_PATTERNS:
        cleaned = re.sub(pat, "", cleaned, flags=re.MULTILINE | re.IGNORECASE)

    # Normalize multiple blank lines to double newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_author_and_date(text: str) -> Tuple[str, str]:
    """Extract author and published date from header text."""
    author = ""
    published_date = ""

    # Check first 1500 chars (header region)
    header_sample = text[:1500]

    for pat in AUTHOR_PATTERNS:
        m = re.search(pat, header_sample)
        if m:
            author = m.group(1).strip()
            # Clean trailing details like company / role if needed
            author = re.sub(r"[\|\(].*$", "", author).strip()
            break

    for pat in DATE_PATTERNS:
        m = re.search(pat, header_sample)
        if m:
            raw_date = m.group(1).strip().replace(".", "-")
            # Normalize to YYYY-MM-DD
            parts = raw_date.split("-")
            if len(parts) == 3:
                published_date = f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
            break

    return author, published_date


def normalize_markdown(raw_content: str, fallback_title: str = "") -> Tuple[str, str, str, str]:
    """
    Normalize raw markdown/text into clean markdown.
    Returns (cleaned_text, title, author, published_date).
    """
    cleaned = raw_content.replace("\r\n", "\n").replace("\r", "\n")
    author, published_date = extract_author_and_date(cleaned)
    cleaned = clean_boilerplate(cleaned)

    # Extract title from first markdown H1 (# Title)
    title = fallback_title
    h1_match = re.search(r"^#\s+(.+)$", cleaned, flags=re.MULTILINE)
    if h1_match:
        title = h1_match.group(1).strip()

    return cleaned, title, author, published_date
