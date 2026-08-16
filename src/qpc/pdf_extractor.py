import re

import fitz

from qpc.schemas import SourceDocument, SourcePage

NOISE_PATTERNS = [
    re.compile(r"^\s*Reprint 2026-27\s*$", re.IGNORECASE),
    re.compile(r"^\s*Chapter\s+\d+\.indd\b.*$", re.IGNORECASE),
]


def clean_page_text(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(pattern.match(line) for pattern in NOISE_PATTERNS):
            continue
        lines.append(line)
    return "\n".join(lines)


def extract_pdf_bytes(filename: str, data: bytes) -> SourceDocument:
    pdf = fitz.open(stream=data, filetype="pdf")
    pages: list[SourcePage] = []
    try:
        for index, page in enumerate(pdf, start=1):
            text = page.get_text("text")
            pages.append(SourcePage(page_number=index, text=clean_page_text(text)))
    finally:
        pdf.close()
    return SourceDocument(filename=filename, pages=pages)
