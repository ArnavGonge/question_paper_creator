### Task 4: PDF Extraction

**Files:**
- Create: `src/qpc/pdf_extractor.py`
- Create: `tests/test_pdf_extractor.py`

**Interfaces:**
- Consumes: `SourceDocument`, `SourcePage` from Task 2.
- Produces: `extract_pdf_bytes(filename: str, data: bytes) -> SourceDocument`.
- Produces: `clean_page_text(text: str) -> str`.

- [ ] **Step 1: Write extraction tests**

`tests/test_pdf_extractor.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src pytest tests/test_pdf_extractor.py -v
```

Expected: FAIL because `qpc.pdf_extractor` does not exist.

- [ ] **Step 3: Implement extractor**

`src/qpc/pdf_extractor.py`:

```python
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
```

- [ ] **Step 4: Run extraction tests**

```bash
PYTHONPATH=src pytest tests/test_pdf_extractor.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit when git exists**

```bash
git add src/qpc/pdf_extractor.py tests/test_pdf_extractor.py
git commit -m "feat: extract chapter text from pdfs"
```

---

