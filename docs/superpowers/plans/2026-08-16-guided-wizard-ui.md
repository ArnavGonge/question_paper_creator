# Guided Wizard UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing Streamlit app into a hand-held, step-by-step workflow with progress, clear completion status, upload feedback, and guarded navigation.

**Architecture:** Keep the existing AI, validation, editor, and docx export modules unchanged. Add small pure helper functions in `app.py` for wizard metadata, step readiness, and upload summaries, then update the Streamlit rendering functions to show one step at a time with progress and status messaging.

**Tech Stack:** Python 3.14, Streamlit, Pydantic, PyMuPDF, python-docx, pytest, ruff.

## Global Constraints

- Hosted Streamlit app.
- Single shared password.
- English only.
- No database or permanent storage in v1.
- Topic selection remains a checklist only; teachers cannot rename or add topics.
- Output remains `.docx` only.
- Preserve the existing AI generation, section editor, regeneration, validation, and Word export behavior.
- Use 8 wizard steps: Start, Upload PDFs, Extract Topics, Choose Topics, Paper Details, Question Sections, Generate and Review, Download Word Document.
- Upload guidance must show allowed file type, a suggested maximum number of PDFs, extraction success, page counts, and errors.
- Navigation must prevent moving forward when required previous work is incomplete.

---

### Task 1: Wizard State Helpers

**Files:**
- Modify: `app.py`
- Test: `tests/test_app_config.py`

**Interfaces:**
- Produces: `WIZARD_STEPS: tuple[str, ...]`
- Produces: `MAX_UPLOAD_PDFS: int`
- Produces: `clamp_step(step: int) -> int`
- Produces: `wizard_progress(step: int) -> float`
- Produces: `wizard_step_label(step: int) -> str`
- Produces: `uploaded_pdf_limit_message(file_count: int) -> str | None`
- Produces: `document_upload_summary(documents: list) -> tuple[int, int]`
- Produces: `step_ready(step: int, *, documents: list, topics: list[Topic], blueprint: PaperBlueprint, paper: GeneratedPaper | None) -> tuple[bool, str]`

- [ ] **Step 1: Write failing tests**

Add tests to `tests/test_app_config.py`:

```python
from app import (
    MAX_UPLOAD_PDFS,
    WIZARD_STEPS,
    clamp_step,
    document_upload_summary,
    step_ready,
    uploaded_pdf_limit_message,
    wizard_progress,
    wizard_step_label,
)
from qpc.schemas import SourceDocument, SourcePage


def test_wizard_steps_are_fixed_for_guided_flow():
    assert WIZARD_STEPS == (
        "Start",
        "Upload PDFs",
        "Extract Topics",
        "Choose Topics",
        "Paper Details",
        "Question Sections",
        "Generate and Review",
        "Download Word Document",
    )
    assert wizard_step_label(1) == "Step 2 of 8: Upload PDFs"
    assert wizard_progress(3) == 4 / 8
    assert clamp_step(-1) == 0
    assert clamp_step(99) == 7


def test_upload_limit_message_only_warns_above_suggested_limit():
    assert uploaded_pdf_limit_message(MAX_UPLOAD_PDFS) is None
    assert uploaded_pdf_limit_message(MAX_UPLOAD_PDFS + 1) == (
        f"You uploaded {MAX_UPLOAD_PDFS + 1} PDFs. For best results, use "
        f"{MAX_UPLOAD_PDFS} or fewer at a time."
    )


def test_document_upload_summary_counts_documents_and_pages():
    documents = [
        SourceDocument(filename="a.pdf", pages=[SourcePage(page_number=1, text="A")]),
        SourceDocument(
            filename="b.pdf",
            pages=[
                SourcePage(page_number=1, text="B"),
                SourcePage(page_number=2, text="C"),
            ],
        ),
    ]

    assert document_upload_summary(documents) == (2, 3)


def test_step_ready_guides_incomplete_flow():
    blueprint = default_blueprint()

    ready, message = step_ready(
        2,
        documents=[],
        topics=[],
        blueprint=blueprint,
        paper=None,
    )

    assert ready is False
    assert message == "Upload and extract at least one PDF first."
```

- [ ] **Step 2: Verify red**

Run: `env PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_config.py -v`

Expected: FAIL because helper names are not defined.

- [ ] **Step 3: Implement helpers**

Add constants and pure helper functions near the top of `app.py`, after `load_secret`.

- [ ] **Step 4: Verify green**

Run: `env PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_config.py -v`

Expected: PASS.

### Task 2: Step-by-Step Streamlit Flow

**Files:**
- Modify: `app.py`
- Test: `tests/test_app_config.py`

**Interfaces:**
- Consumes Task 1 helpers.
- Produces Streamlit session state key: `wizard_step: int`.
- Produces rendering helpers: `render_wizard_progress() -> None`, `navigation_controls() -> None`, `show_step_status() -> None`.

- [ ] **Step 1: Write failing tests**

Add tests to `tests/test_app_config.py`:

```python
def test_step_ready_requires_selected_topics_before_paper_details():
    blueprint = default_blueprint()
    topics = [
        Topic(
            id="weather",
            document_filename="weather.pdf",
            name="Weather",
            summary="Weather systems",
            source_pages=[1],
            selected=False,
        )
    ]
    documents = [SourceDocument(filename="weather.pdf", pages=[SourcePage(page_number=1, text="A")])]

    ready, message = step_ready(
        4,
        documents=documents,
        topics=topics,
        blueprint=blueprint,
        paper=None,
    )

    assert ready is False
    assert message == "Select at least one topic first."


def test_step_ready_requires_generated_paper_before_download():
    blueprint = default_blueprint()
    topics = [
        Topic(
            id="weather",
            document_filename="weather.pdf",
            name="Weather",
            summary="Weather systems",
            source_pages=[1],
            selected=True,
        )
    ]
    documents = [SourceDocument(filename="weather.pdf", pages=[SourcePage(page_number=1, text="A")])]

    ready, message = step_ready(
        7,
        documents=documents,
        topics=topics,
        blueprint=blueprint,
        paper=None,
    )

    assert ready is False
    assert message == "Generate a valid question paper first."
```

- [ ] **Step 2: Verify red**

Run: `env PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_config.py -v`

Expected: FAIL until step gating covers selected topics and generated paper.

- [ ] **Step 3: Implement wizard rendering**

Update `ensure_state`, `main`, and the step functions so only the active step renders. Add simple explanatory text and status messages per step. Add progress bar and Back/Next controls. Use `st.spinner` around PDF extraction, topic extraction, full generation, and section regeneration.

- [ ] **Step 4: Verify green**

Run: `env PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_config.py -v`

Expected: PASS.

### Task 3: Final Verification

**Files:**
- No production edits expected.

- [ ] **Step 1: Run full tests**

Run: `env PYTHONPATH=src .venv/bin/python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 2: Run lint**

Run: `env PYTHONPATH=src .venv/bin/ruff check src tests app.py`

Expected: all checks pass.

- [ ] **Step 3: Smoke test Streamlit**

Run: `env STREAMLIT_BROWSER_GATHER_USAGE_STATS=false APP_PASSWORD=dummy-password PYTHONPATH=src .venv/bin/python -m streamlit run app.py --server.headless true --server.port 8501`

Expected: server starts and `curl -I http://localhost:8501` returns `HTTP/1.1 200 OK`.
