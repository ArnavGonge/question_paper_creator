from pathlib import Path

from qpc.pdf_extractor import clean_page_text, extract_pdf_bytes

DATA_DIR = Path("data")


def test_clean_page_text_removes_reprint_and_indd_lines():
    raw = "Weather and its Elements\n\nReprint 2026-27\n\nChapter 2.indd 28 08-04-2025"

    assert clean_page_text(raw) == "Weather and its Elements"


def test_extracts_weather_pdf_text():
    pdf_path = DATA_DIR / "gees102 Understanding the Weather.pdf"
    document = extract_pdf_bytes(pdf_path.name, pdf_path.read_bytes())

    combined = document.combined_text()

    assert document.filename == pdf_path.name
    assert len(document.pages) >= 10
    assert "Weather and its Elements" in combined
    assert "Temperature" in combined


def test_extracts_geography_pdf_text():
    pdf_path = DATA_DIR / "gees101 Geographical Diversity of India.pdf"
    document = extract_pdf_bytes(pdf_path.name, pdf_path.read_bytes())

    combined = document.combined_text()

    assert len(document.pages) >= 10
    assert "The Himalayas" in combined
    assert "Northern Plains" in combined
