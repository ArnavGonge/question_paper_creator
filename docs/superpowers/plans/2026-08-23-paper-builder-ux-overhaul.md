# Paper Builder UX Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current six-step Streamlit wizard into a friendly, resilient paper-building workflow with calculated marks, complete section controls, neutral styling, and operator-only technical diagnostics.

**Architecture:** Keep extraction, generation, validation, and DOCX export as domain modules. Move pure workflow transformations and error reporting into focused modules, add a small Streamlit presentation module, and leave `app.py` responsible for session orchestration and step composition. Section-derived totals flow from `PaperBlueprint.total_marks()` to the prompt, UI, and exporter.

**Tech Stack:** Python 3.13, Streamlit 1.61.1, Pydantic 2.13.4, OpenAI 3.1.0, PyMuPDF 1.28.2, python-docx 1.2.0, pytest 9.1.1, Ruff 0.16.3.

**Spec:** `docs/superpowers/specs/2026-08-23-paper-builder-ux-overhaul-design.md`

## Global Constraints

- Keep the existing six-step wizard and current AI, PDF, validation, and DOCX pipeline.
- Keep the application chrome visually neutral and school-agnostic.
- Use section configuration as the only source of truth for grand total marks.
- Never render raw exception messages, stack traces, API payloads, keys, passwords, or document contents.
- Log full tracebacks with a reference ID to server logs without logging secrets or source document contents.
- Preserve successful session state after recoverable failures.
- Require confirmation before deleting a section and never allow deletion of the final section.
- Do not add a database, persistent projects, accounts, a new frontend framework, or new runtime dependencies.
- Keep text and controls usable at desktop and narrow viewport widths.

---

### Task 1: Make Marks a Derived Domain Value

**Files:**
- Modify: `src/qpc/schemas.py`
- Modify: `src/qpc/demo_data.py`
- Modify: `src/qpc/question_generator.py`
- Modify: `src/qpc/docx_exporter.py`
- Modify: `src/qpc/validators.py`
- Modify: `app.py`
- Modify: `tests/test_schemas.py`
- Modify: `tests/test_demo_data.py`
- Modify: `tests/test_prompt_builders.py`
- Modify: `tests/test_docx_exporter.py`
- Modify: `tests/test_validators.py`
- Modify: `tests/test_app_config.py`

**Interfaces:**
- Produces: `PaperBlueprint.total_marks() -> int` as the only paper-total API.
- Produces: strict `PaperMetadata.date` validation for `DD.MM.YYYY` values.
- Removes: `PaperMetadata.max_marks`.
- Removes: `validate_blueprint(blueprint)` and total-mismatch gating.

- [ ] **Step 1: Write failing schema and consumer tests**

Update `tests/test_schemas.py` so `PaperMetadata` constructors omit `max_marks`, then add:

```python
def test_paper_metadata_rejects_an_invalid_header_date():
    with pytest.raises(ValidationError):
        PaperMetadata(
            grade="VII",
            subject="Social Science",
            exam_name="First Periodic Assessment 2026-27",
            date="2026-07-17",
            duration="2 Hours",
        )


def test_paper_metadata_has_no_independent_max_marks_field():
    metadata = PaperMetadata(
        grade="VII",
        subject="Social Science",
        exam_name="Assessment",
        date="17.07.2026",
        duration="2 Hours",
    )

    assert "max_marks" not in metadata.model_dump()
```

Update `tests/test_prompt_builders.py::test_build_question_prompt_includes_selected_topics_and_blueprint` with:

```python
assert "Paper total: 4 marks" in prompt
```

Rename the first DOCX test to `test_render_docx_uses_calculated_total_in_header`, configure one answered question worth 7 marks, and assert:

```python
assert "M.M. 7        Time- 2 Hour" in text
```

Delete `test_validate_blueprint_detects_total_mismatch`; update every test fixture to construct `PaperMetadata` without `max_marks`.

Replace the fallback date test in `tests/test_app_config.py` with:

```python
def test_metadata_date_parser_rejects_unparseable_existing_value():
    with pytest.raises(ValueError):
        parse_metadata_date("not-a-date")
```

- [ ] **Step 2: Run the focused tests and verify red**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_schemas.py tests\test_prompt_builders.py tests\test_docx_exporter.py tests\test_validators.py tests\test_demo_data.py -v
```

Expected: FAIL because `max_marks` still exists, invalid date strings are accepted, the prompt lacks a calculated total, and the exporter reads metadata marks.

- [ ] **Step 3: Implement the domain migration**

In `src/qpc/schemas.py`, remove `max_marks` and validate dates at the schema boundary:

```python
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class PaperMetadata(BaseModel):
    grade: str
    subject: str
    exam_name: str
    date: str
    duration: str
    school_name: str = "ZENITH PUBLIC SCHOOL"
    school_address: str = "Plot no 13 & 14, Sector 5, Airoli, Navi Mumbai 400708"
    affiliation: str = "CBSE Affiliation No.- 1131335"

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        datetime.strptime(value, "%d.%m.%Y")
        return value
```

Remove `max_marks` from `default_metadata()`. Add `Paper total: {blueprint.total_marks()} marks` immediately before the section blueprint in `build_question_prompt()`. Change the DOCX header to:

```python
table.cell(2, 1).text = (
    f"M.M. {blueprint.total_marks()}        Time- {metadata.duration}"
)
```

Delete `validate_blueprint()` from `src/qpc/validators.py`, remove its import and calls in `app.py`, remove the Maximum marks input and mismatch warning from `paper_details_step()`, and show the current total as read-only text:

```python
st.metric("Calculated marks", blueprint.total_marks())
```

Change `parse_metadata_date()` to `return datetime.strptime(value, "%d.%m.%Y").date()` so invalid state is never silently rewritten. Keep `step_ready()` dependent only on documents, selected topics, and generated-paper presence. Update all test fixtures and demo assertions to remove `max_marks`.

- [ ] **Step 4: Run the full suite**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest -v
```

Expected: PASS.

- [ ] **Step 5: Commit the derived-total migration**

```powershell
git add app.py src/qpc/schemas.py src/qpc/demo_data.py src/qpc/question_generator.py src/qpc/docx_exporter.py src/qpc/validators.py tests
git commit -m "refactor: calculate paper marks from sections"
```

---

### Task 2: Add Pure Workflow and Section Operations

**Files:**
- Create: `src/qpc/workflow.py`
- Create: `tests/test_workflow.py`
- Modify: `app.py`
- Modify: `tests/test_app_config.py`

**Interfaces:**
- Produces: `documents_after_extraction(previous_documents: list[SourceDocument], extracted_documents: list[SourceDocument]) -> list[SourceDocument]`.
- Produces: `move_section(sections: list[SectionBlueprint], index: int, offset: int) -> list[SectionBlueprint]`.
- Produces: `delete_section(sections: list[SectionBlueprint], index: int) -> list[SectionBlueprint]`.
- Produces: `append_default_section(sections: list[SectionBlueprint]) -> list[SectionBlueprint]`.
- Produces: `next_section_label(sections: list[SectionBlueprint]) -> str`.

- [ ] **Step 1: Write failing workflow tests**

Create `tests/test_workflow.py`:

```python
import pytest

from qpc.demo_data import default_sections
from qpc.schemas import QuestionType, SectionBlueprint, SourceDocument, SourcePage
from qpc.workflow import (
    append_default_section,
    delete_section,
    documents_after_extraction,
    move_section,
    next_section_label,
)


def section(label: str) -> SectionBlueprint:
    return SectionBlueprint(
        label=label,
        heading=f"{label} heading",
        question_type=QuestionType.SHORT,
        questions_to_generate=2,
        questions_to_answer=2,
        marks_per_question=2,
    )


def test_failed_reextraction_keeps_previous_documents():
    previous = [
        SourceDocument(
            filename="working.pdf",
            pages=[SourcePage(page_number=1, text="Working text")],
        )
    ]

    assert documents_after_extraction(previous, []) == previous


def test_successful_reextraction_replaces_previous_documents():
    previous = [SourceDocument(filename="old.pdf", pages=[])]
    extracted = [SourceDocument(filename="new.pdf", pages=[])]

    assert documents_after_extraction(previous, extracted) == extracted


def test_move_section_returns_reordered_copies_without_relabelling():
    sections = [section("Section A"), section("Section B"), section("Section C")]

    moved = move_section(sections, 1, -1)

    assert [item.label for item in moved] == ["Section B", "Section A", "Section C"]
    assert [item.label for item in sections] == ["Section A", "Section B", "Section C"]


def test_delete_section_rejects_deleting_the_last_section():
    with pytest.raises(ValueError, match="at least one section"):
        delete_section(default_sections(), 0)


def test_new_section_uses_first_available_label_after_a_gap():
    sections = [section("Section A"), section("Section C")]

    assert next_section_label(sections) == "Section B"
    assert append_default_section(sections)[-1].label == "Section B"
```

- [ ] **Step 2: Run the workflow tests and verify red**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_workflow.py -v
```

Expected: FAIL because `qpc.workflow` does not exist.

- [ ] **Step 3: Implement immutable workflow helpers**

Create `src/qpc/workflow.py`. Every returned section is a deep copy; reject invalid indexes and offsets explicitly:

```python
from qpc.schemas import QuestionType, SectionBlueprint, SourceDocument


def documents_after_extraction(
    previous_documents: list[SourceDocument],
    extracted_documents: list[SourceDocument],
) -> list[SourceDocument]:
    source = extracted_documents or previous_documents
    return [document.model_copy(deep=True) for document in source]


def move_section(
    sections: list[SectionBlueprint], index: int, offset: int
) -> list[SectionBlueprint]:
    target = index + offset
    if offset not in {-1, 1} or index not in range(len(sections)):
        raise ValueError("invalid section move")
    if target not in range(len(sections)):
        raise ValueError("section cannot move beyond the list")
    result = [section.model_copy(deep=True) for section in sections]
    result[index], result[target] = result[target], result[index]
    return result


def delete_section(
    sections: list[SectionBlueprint], index: int
) -> list[SectionBlueprint]:
    if len(sections) == 1:
        raise ValueError("at least one section is required")
    if index not in range(len(sections)):
        raise ValueError("invalid section index")
    return [
        section.model_copy(deep=True)
        for position, section in enumerate(sections)
        if position != index
    ]


def next_section_label(sections: list[SectionBlueprint]) -> str:
    used = {section.label.casefold() for section in sections}
    candidate_index = 0
    while True:
        suffix = chr(65 + candidate_index) if candidate_index < 26 else str(candidate_index + 1)
        candidate = f"Section {suffix}"
        if candidate.casefold() not in used:
            return candidate
        candidate_index += 1


def append_default_section(
    sections: list[SectionBlueprint],
) -> list[SectionBlueprint]:
    return [
        *[section.model_copy(deep=True) for section in sections],
        SectionBlueprint(
            label=next_section_label(sections),
            heading="Short Answer Based Questions",
            question_type=QuestionType.SHORT,
            questions_to_generate=3,
            questions_to_answer=3,
            marks_per_question=2,
        ),
    ]
```

Import `documents_after_extraction` from `qpc.workflow` in `app.py` and delete the local helper. Update the old app test so an empty extraction expects previous documents to remain.

- [ ] **Step 4: Run focused and full tests**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_workflow.py tests\test_app_config.py -v
.\.venv-win\Scripts\python.exe -m pytest -v
```

Expected: PASS for both commands.

- [ ] **Step 5: Commit workflow operations**

```powershell
git add app.py src/qpc/workflow.py tests/test_workflow.py tests/test_app_config.py
git commit -m "feat: add safe paper workflow operations"
```

---

### Task 3: Centralize Safe Error Reporting

**Files:**
- Create: `src/qpc/error_reporting.py`
- Create: `tests/test_error_reporting.py`
- Modify: `app.py`

**Interfaces:**
- Produces: `AppConfigurationError(ValueError)` for missing server configuration.
- Produces: `ErrorReport(user_message: str, reference_id: str)`.
- Produces: `report_operation_error(operation: str, error: Exception, *, context: dict[str, str] | None = None, logger: logging.Logger | None = None) -> ErrorReport`.
- Operation names: `pdf_extraction`, `topic_extraction`, `paper_generation`, `section_generation`, `document_export`.

- [ ] **Step 1: Write failing error-reporting tests**

Create `tests/test_error_reporting.py`:

```python
import logging

from qpc.error_reporting import AppConfigurationError, report_operation_error


def test_configuration_error_is_safe_and_logged_with_reference(caplog):
    logger = logging.getLogger("qpc.test.configuration")
    error = AppConfigurationError("openai")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        report = report_operation_error("topic_extraction", error, logger=logger)

    assert report.user_message == (
        "AI features are not configured on this server. Contact the app administrator."
    )
    assert report.reference_id in caplog.text


def test_unexpected_error_hides_exception_from_user_and_logs_traceback(caplog):
    logger = logging.getLogger("qpc.test.unexpected")
    error = RuntimeError("provider payload must remain private")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        report = report_operation_error("paper_generation", error, logger=logger)

    assert "provider payload" not in report.user_message
    assert report.user_message == (
        "The paper could not be generated. Please try again in a moment."
    )
    assert report.reference_id in caplog.text
    assert "provider payload" not in caplog.text
    assert "Traceback" in caplog.text


def test_timeout_gets_specific_retry_guidance(caplog):
    class APITimeoutError(Exception):
        pass

    logger = logging.getLogger("qpc.test.timeout")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        report = report_operation_error(
            "paper_generation",
            APITimeoutError("private provider detail"),
            logger=logger,
        )

    assert report.user_message == (
        "The AI service did not respond in time. Please try again."
    )


def test_error_log_context_does_not_require_document_content(caplog):
    logger = logging.getLogger("qpc.test.pdf")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        report_operation_error(
            "pdf_extraction",
            ValueError("broken xref"),
            context={"filename": "chapter.pdf"},
            logger=logger,
        )

    assert "chapter.pdf" in caplog.text
    assert "document_text" not in caplog.text
```

- [ ] **Step 2: Run the tests and verify red**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_error_reporting.py -v
```

Expected: FAIL because `qpc.error_reporting` does not exist.

- [ ] **Step 3: Implement safe reports and structured logging**

Create `src/qpc/error_reporting.py` with operation-specific copy and explicit traceback logging:

```python
from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass
from uuid import uuid4


LOGGER = logging.getLogger("qpc")


class AppConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class ErrorReport:
    user_message: str
    reference_id: str


OPERATION_MESSAGES = {
    "pdf_extraction": "This PDF could not be read. Check that it opens normally and is not password protected.",
    "topic_extraction": "Topics could not be found right now. Please try again in a moment.",
    "paper_generation": "The paper could not be generated. Please try again in a moment.",
    "section_generation": "This section could not be regenerated. Please try again in a moment.",
    "document_export": "The Word document could not be prepared. Please try again.",
}


def report_operation_error(
    operation: str,
    error: Exception,
    *,
    context: dict[str, str] | None = None,
    logger: logging.Logger | None = None,
) -> ErrorReport:
    reference_id = uuid4().hex[:8].upper()
    error_type = type(error).__name__
    if isinstance(error, AppConfigurationError) or error_type == "AuthenticationError":
        message = (
            "AI features are not configured on this server. "
            "Contact the app administrator."
        )
    elif error_type in {"APITimeoutError", "APIConnectionError"}:
        message = "The AI service did not respond in time. Please try again."
    elif error_type == "RateLimitError":
        message = "The AI service is busy right now. Please wait a moment and retry."
    elif error_type in {"JSONDecodeError", "ValidationError"} and operation in {
        "topic_extraction",
        "paper_generation",
        "section_generation",
    }:
        message = "The AI response was incomplete. Please generate it again."
    else:
        message = OPERATION_MESSAGES.get(
            operation,
            "Something went wrong. Please try again.",
        )
    active_logger = logger or LOGGER
    active_logger.error(
        (
            "operation_failed reference_id=%s operation=%s context=%r "
            "error_type=%s\nTraceback:\n%s"
        ),
        reference_id,
        operation,
        context or {},
        error_type,
        "".join(traceback.format_tb(error.__traceback__)),
    )
    return ErrorReport(user_message=message, reference_id=reference_id)
```

In `app.py`, add a temporary `show_error_report(report: ErrorReport) -> None` that renders only:

```python
st.error(f"{report.user_message} Reference: {report.reference_id}")
```

Replace missing-key `ValueError` instances with `AppConfigurationError`. Replace every `st.error(f"... {exc}")` operation catch with `report_operation_error(...)` followed by `show_error_report(...)`. Wrap `render_docx()` in the same boundary. Never pass API keys or document text in `context`. The logger records the exception type and all traceback frames but deliberately omits `str(error)`, because provider exceptions may embed response payloads or credentials in their messages.

- [ ] **Step 4: Run error and regression tests**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_error_reporting.py tests\test_app_config.py -v
.\.venv-win\Scripts\python.exe -m pytest -v
```

Expected: PASS, and no app-rendered message interpolates an exception.

- [ ] **Step 5: Commit error reporting**

```powershell
git add app.py src/qpc/error_reporting.py tests/test_error_reporting.py
git commit -m "feat: hide technical errors behind references"
```

---

### Task 4: Build the Neutral Presentation Foundation

**Files:**
- Create: `src/qpc/presentation.py`
- Create: `tests/test_presentation.py`
- Modify: `app.py`

**Interfaces:**
- Produces: `STEP_COPY: dict[str, StepCopy]`.
- Produces: `QUESTION_TYPE_LABELS: dict[QuestionType, str]`.
- Produces: `section_header(section: SectionBlueprint) -> str`.
- Produces: `apply_app_theme() -> None`.
- Produces: `render_step_heading(step_name: str, *, summary: str = "") -> None`.
- Produces: `render_error_report(report: ErrorReport) -> None`.

- [ ] **Step 1: Write failing presentation tests**

Create `tests/test_presentation.py`:

```python
from qpc.demo_data import default_sections
from qpc.presentation import APP_CSS, STEP_COPY, section_header


def test_every_wizard_step_has_concise_copy():
    assert set(STEP_COPY) == {
        "Upload PDFs",
        "Topics",
        "Paper Details",
        "Question Sections",
        "Generate and Review",
        "Download Word Document",
    }
    assert all(item.title and item.prompt for item in STEP_COPY.values())


def test_section_header_contains_type_count_and_marks():
    assert section_header(default_sections()[0]) == (
        "Section A | Multiple Choice | Answer 4 | 1 mark each | 4 marks"
    )


def test_theme_defines_neutral_and_semantic_colors():
    assert "--qpc-primary: #0f766e" in APP_CSS
    assert "--qpc-warning: #b45309" in APP_CSS
    assert "--qpc-danger: #b42318" in APP_CSS
    assert "@media (max-width: 700px)" in APP_CSS
```

- [ ] **Step 2: Run presentation tests and verify red**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_presentation.py -v
```

Expected: FAIL because `qpc.presentation` does not exist.

- [ ] **Step 3: Implement presentation helpers and scoped theme**

Create `src/qpc/presentation.py` with this frozen model and copy for all six steps:

```python
@dataclass(frozen=True)
class StepCopy:
    title: str
    prompt: str


STEP_COPY = {
    "Upload PDFs": StepCopy(
        "Add source material",
        "Choose the textbook PDFs this paper should use.",
    ),
    "Topics": StepCopy(
        "Choose topics",
        "Select the extracted topics that belong in this paper.",
    ),
    "Paper Details": StepCopy(
        "Set paper details",
        "Check the information that will appear in the document header.",
    ),
    "Question Sections": StepCopy(
        "Build question sections",
        "Set the question mix and marks for each part of the paper.",
    ),
    "Generate and Review": StepCopy(
        "Generate and review",
        "Create the paper, then review each section before export.",
    ),
    "Download Word Document": StepCopy(
        "Download the paper",
        "Check the final summary and prepare the Word document.",
    ),
}
```

Define explicit teacher-facing question type labels so abbreviations remain readable:

```python
QUESTION_TYPE_LABELS = {
    QuestionType.MCQ: "Multiple Choice",
    QuestionType.VERY_SHORT: "Very Short Answer",
    QuestionType.SHORT: "Short Answer",
    QuestionType.LONG: "Long Answer",
    QuestionType.FILL_BLANKS: "Fill in the Blanks",
    QuestionType.TRUE_FALSE: "True or False",
    QuestionType.MATCH: "Match the Following",
    QuestionType.CASE_STUDY: "Case Study",
    QuestionType.MAP_DIAGRAM: "Map or Diagram",
}
```

`section_header()` uses this mapping and singular/plural marks. `apply_app_theme()` injects `APP_CSS` using `st.markdown(..., unsafe_allow_html=True)`. `render_error_report()` imports `ErrorReport` and renders only its safe message and reference.

The CSS must define these tokens and apply them to Streamlit's main container, sidebar, buttons, inputs, alerts, expanders, metrics, and narrow layouts:

```css
:root {
  --qpc-canvas: #f5f7f8;
  --qpc-surface: #ffffff;
  --qpc-text: #17202a;
  --qpc-muted: #5f6b76;
  --qpc-border: #d9e0e4;
  --qpc-primary: #0f766e;
  --qpc-warning: #b45309;
  --qpc-danger: #b42318;
  --qpc-success: #18794e;
}

@media (max-width: 700px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; }
}
```

Keep corners at 8px or less, avoid gradients, and do not turn full page sections into floating cards. Replace the temporary app-level `show_error_report()` with `render_error_report()`.

- [ ] **Step 4: Apply the shell in `app.py`**

Call `apply_app_theme()` immediately after `st.set_page_config()`. Replace per-step `st.subheader()` calls with `render_step_heading()`. Update the sidebar to use concise state labels and a clear current-step marker while preserving existing readiness logic. Give primary action buttons `type="primary"` and keep Back secondary.

- [ ] **Step 5: Run tests and lint**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_presentation.py tests\test_app_config.py -v
.\.venv-win\Scripts\python.exe -m ruff check src tests app.py
```

Expected: PASS.

- [ ] **Step 6: Commit the presentation foundation**

```powershell
git add app.py src/qpc/presentation.py tests/test_presentation.py
git commit -m "feat: add guided neutral app styling"
```

---

### Task 5: Improve Upload, Topics, and Details States

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_config.py`

**Interfaces:**
- Consumes: `documents_after_extraction()` from Task 2.
- Consumes: `report_operation_error()` and `render_error_report()` from Tasks 3-4.
- Produces: `upload_result_summary(success_count: int, failure_count: int) -> str`.
- Produces session state: `upload_errors: list[ErrorReport]`.

- [ ] **Step 1: Write failing state-copy tests**

Add to `tests/test_app_config.py`:

```python
def test_upload_result_summary_handles_partial_success():
    assert upload_result_summary(2, 1) == "2 PDFs ready; 1 PDF needs attention."


def test_upload_result_summary_handles_complete_failure():
    assert upload_result_summary(0, 2) == (
        "No new PDFs were extracted; your previous sources are still available."
    )
```

- [ ] **Step 2: Run the app-config tests and verify red**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_app_config.py -v
```

Expected: FAIL because `upload_result_summary()` does not exist and old date fallback behavior remains.

- [ ] **Step 3: Rework upload feedback and recovery**

Implement `upload_result_summary()`. During extraction, collect successful documents and safe `ErrorReport` objects independently. Apply `documents_after_extraction()` only after all selected files have been attempted. Clear topics and generated paper only when the resulting document snapshot actually changes. Render successful filenames/page counts separately from failures and never render `str(exc)`.

Use singular-aware result copy:

```python
def upload_result_summary(success_count: int, failure_count: int) -> str:
    if success_count == 0 and failure_count:
        return "No new PDFs were extracted; your previous sources are still available."
    if failure_count == 0:
        return f"{metric_text(success_count, 'PDF')} ready."
    return (
        f"{metric_text(success_count, 'PDF')} ready; "
        f"{metric_text(failure_count, 'PDF')} needs attention."
    )
```

- [ ] **Step 4: Rework topics and paper details**

Group topics by `document_filename` with one source heading per group, a selected-count summary, and responsive checkbox columns. Keep previous topics when refresh fails. In Paper Details, use two rows of fields, retain `date_input()` now that the schema guarantees a valid stored date, and show calculated marks as a read-only metric with the caption `Change this total in Question Sections.`

Use friendly empty/loading/success copy from `STEP_COPY`. Missing API configuration must produce an `AppConfigurationError` report rather than expose an environment variable name.

- [ ] **Step 5: Run focused and full tests**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_app_config.py tests\test_error_reporting.py -v
.\.venv-win\Scripts\python.exe -m pytest -v
```

Expected: PASS.

- [ ] **Step 6: Commit the guided input steps**

```powershell
git add app.py tests/test_app_config.py
git commit -m "feat: improve source and paper detail guidance"
```

---

### Task 6: Rebuild the Section Editor

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_config.py`
- Modify: `tests/test_workflow.py`

**Interfaces:**
- Consumes: `append_default_section()`, `delete_section()`, and `move_section()` from Task 2.
- Consumes: `section_header()` from Task 4.
- Produces: `clear_section_widget_state(state: MutableMapping[str, Any]) -> None`.
- Produces session state: `pending_section_delete: int | None`.

- [ ] **Step 1: Write failing widget-state and invalidation tests**

Add to `tests/test_app_config.py`:

```python
def test_clear_section_widget_state_removes_only_section_editor_keys():
    state = {
        "label_0": "Section A",
        "heading_0": "MCQ",
        "marks_0": 1,
        "topic_weather": True,
    }

    clear_section_widget_state(state)

    assert state == {"topic_weather": True}
```

Extend `tests/test_workflow.py` with invalid-index, first-item move-up, and last-item move-down assertions so every rejected operation has an exact error.

- [ ] **Step 2: Run focused tests and verify red**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_workflow.py tests\test_app_config.py -v
```

Expected: FAIL because section widget cleanup and the new edge-case expectations are absent.

- [ ] **Step 3: Implement section action state**

Add these editor prefixes in `app.py`:

```python
from collections.abc import MutableMapping


SECTION_WIDGET_PREFIXES = (
    "label_",
    "heading_",
    "type_",
    "instruction_",
    "gen_",
    "ans_",
    "marks_",
)


def clear_section_widget_state(state: MutableMapping[str, Any]) -> None:
    for key in list(state):
        if key.startswith(SECTION_WIDGET_PREFIXES):
            del state[key]
```

Initialize `pending_section_delete` in `ensure_state()`. For add, move, or confirmed delete: snapshot the old blueprint, apply the pure workflow operation, assign a new `PaperBlueprint`, clear section widget state, call `clear_paper_if_blueprint_changed()`, and rerun.

- [ ] **Step 4: Build scannable section panels and confirmation**

Render each section with `section_header(section)` and an action row containing Move up, Move down, and Delete buttons with Streamlit Material icons and `help` text. Disable boundary moves and disable Delete when only one section remains. Use `@st.dialog("Delete section?")` to name the pending section, explain that generated output will need regeneration, and provide Cancel and Delete section actions.

Inside the editor, keep label/heading, type/instruction, and generation/answer/marks controls. Constrain answer count to generation count. Show the section subtotal adjacent to numeric controls and the paper total in a persistent summary above Add section.

- [ ] **Step 5: Run tests and lint**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_workflow.py tests\test_app_config.py -v
.\.venv-win\Scripts\python.exe -m ruff check src tests app.py
```

Expected: PASS.

- [ ] **Step 6: Commit the complete section lifecycle**

```powershell
git add app.py tests/test_app_config.py tests/test_workflow.py
git commit -m "feat: add section reorder and delete controls"
```

---

### Task 7: Polish Generation, Review, and Download

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_config.py`

**Interfaces:**
- Consumes: calculated `PaperBlueprint.total_marks()`.
- Consumes: safe error boundary and presentation helpers.
- Preserves: `build_generation_inputs_snapshot()`, `paper_is_stale()`, `validate_export_ready_paper()`, and per-section regeneration.
- Produces: `invalidate_generated_paper(reason: str) -> None`.
- Produces session state: `paper_stale_notice: str`.

- [ ] **Step 1: Write failing readiness-summary tests**

Add a pure helper and tests in `tests/test_app_config.py`:

```python
def test_generation_summary_reports_all_inputs():
    blueprint = default_blueprint()

    assert generation_summary(2, 5, blueprint) == {
        "Sources": "2 PDFs",
        "Topics": "5 selected",
        "Sections": "1",
        "Total": "4 marks",
    }


def test_stale_paper_notice_is_teacher_facing():
    assert stale_paper_notice("sections") == (
        "Your section setup changed. Generate the paper again before downloading."
    )
```

Add a stale-paper assertion showing that a section reorder changes the blueprint snapshot and therefore makes `paper_is_stale(...)` return `True`.

- [ ] **Step 2: Run app tests and verify red**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_app_config.py -v
```

Expected: FAIL because `generation_summary()` is absent.

- [ ] **Step 3: Implement the generation and review layout**

Implement `generation_summary()` and `stale_paper_notice(reason)` using these exact definitions:

```python
def generation_summary(
    source_count: int,
    topic_count: int,
    blueprint: PaperBlueprint,
) -> dict[str, str]:
    return {
        "Sources": f"{source_count} PDFs",
        "Topics": f"{topic_count} selected",
        "Sections": str(len(blueprint.sections)),
        "Total": f"{blueprint.total_marks()} marks",
    }


STALE_PAPER_MESSAGES = {
    "sources": "Your source PDFs changed. Choose topics and generate the paper again.",
    "topics": "Your topic selection changed. Generate the paper again before downloading.",
    "details": "Your paper details changed. Generate the paper again before downloading.",
    "sections": "Your section setup changed. Generate the paper again before downloading.",
}


def stale_paper_notice(reason: str) -> str:
    return STALE_PAPER_MESSAGES[reason]
```

Render the four summary values in a compact row. Add `paper_stale_notice = ""` in `ensure_state()` and centralize paper clearing in `invalidate_generated_paper(reason)`: when a paper exists, set the notice from `stale_paper_notice(reason)`, then clear `paper` and `paper_inputs`. Replace direct clearing after source, topic, metadata, and section changes with this helper. Clear the notice after a successful full generation.

Show `paper_stale_notice` above generation readiness and on the download step. Keep the existing diagnostics data but place paper-wide issues above section editors and section-specific issues inside their matching section. Route full generation and per-section regeneration exceptions through safe reports. Keep manual passage, question, option, pair, and sub-question editing behavior intact.

- [ ] **Step 4: Implement the final download state**

Show exam name, grade/subject, source count, section count, and calculated marks before the download action. Keep export blocked when generated-paper validation fails. Wrap `render_docx()` in `try/except`, report `document_export` failures safely, and only render `st.download_button()` after bytes are created successfully.

- [ ] **Step 5: Run focused and full tests**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_app_config.py tests\test_docx_exporter.py tests\test_error_reporting.py -v
.\.venv-win\Scripts\python.exe -m pytest -v
```

Expected: PASS.

- [ ] **Step 6: Commit review and download polish**

```powershell
git add app.py tests/test_app_config.py
git commit -m "feat: polish paper review and export flow"
```

---

### Task 8: Verify the Complete Windows Workflow

**Files:**
- Create: `tests/test_app_smoke.py`
- Modify only if verification exposes a defect: `app.py`, `src/qpc/presentation.py`, or the directly affected test.

**Interfaces:**
- No new production interface.

- [ ] **Step 1: Add Streamlit smoke tests for the working surfaces**

Create `tests/test_app_smoke.py`:

```python
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_FILE = Path(__file__).parents[1] / "app.py"


def authenticated_app(step: int) -> AppTest:
    app = AppTest.from_file(APP_FILE, default_timeout=10)
    app.session_state["authenticated"] = True
    app.session_state["wizard_step"] = step
    return app.run()


def test_upload_step_renders_without_an_exception():
    app = authenticated_app(0)

    assert not app.exception
    assert len(app.file_uploader) == 1
    assert any(button.label == "Extract text" for button in app.button)


def test_section_editor_renders_complete_controls_for_default_section():
    app = authenticated_app(3)

    assert not app.exception
    labels = [button.label for button in app.button]
    assert "Move up" in labels
    assert "Move down" in labels
    assert "Delete" in labels
    assert "Add section" in labels
    delete_button = next(button for button in app.button if button.label == "Delete")
    assert delete_button.disabled is True
```

- [ ] **Step 2: Run the Streamlit smoke tests**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest tests\test_app_smoke.py -v
```

Expected: PASS with no Streamlit exceptions.

- [ ] **Step 3: Run all automated tests**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m pytest -v
```

Expected: all tests pass with no warnings caused by the changes.

- [ ] **Step 4: Run Ruff**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m ruff check src tests app.py
```

Expected: `All checks passed!`

- [ ] **Step 5: Search for leaked exception rendering and obsolete marks**

Run:

```powershell
rg -n "st\.error\(f.*exc|max_marks|validate_blueprint" app.py src tests
```

Expected: no matches.

- [ ] **Step 6: Start Streamlit on Windows**

Run:

```powershell
.\.venv-win\Scripts\python.exe -m streamlit run app.py --server.headless true --server.port 8501
```

Expected: Streamlit reports local URL `http://localhost:8501` and stays running without a traceback.

- [ ] **Step 7: Smoke-test desktop and narrow layouts**

At `http://localhost:8501`, verify at approximately 1440 x 900 and 390 x 844:

- Password view does not expose configuration details.
- All six sidebar states are readable and the current step is unmistakable.
- Upload success and partial failure remain distinguishable.
- Topics are selectable without clipped labels.
- Paper Details shows calculated marks and no editable maximum.
- Sections can be added, moved, and deleted after confirmation; the last cannot be deleted.
- Totals update immediately and generated work becomes stale after blueprint edits.
- Generate/retry errors show only friendly copy plus a reference ID.
- Review controls do not overlap or resize unpredictably.
- Download summary and DOCX header show the calculated total.

- [ ] **Step 8: Stop the verification server and commit any fixes**

Stop the foreground server with `Ctrl+C`. If verification required changes, rerun Steps 1-3 and commit only those fixes:

```powershell
git add app.py src/qpc/presentation.py tests
git commit -m "fix: resolve paper builder smoke test issues"
```
