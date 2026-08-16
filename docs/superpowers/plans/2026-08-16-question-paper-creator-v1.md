# Question Paper Creator V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a hosted Streamlit app that turns uploaded chapter PDFs into an editable English question-paper draft and exports a fixed-layout Word `.docx`.

**Architecture:** Use a small Python package under `src/qpc/` for extraction, schemas, validation, AI orchestration, and DOCX rendering, with `app.py` kept as a thin Streamlit workflow layer. Store runtime state only in Streamlit session state; keep the OpenAI key and app password server-side in secrets. Generate AI output as structured JSON, validate it, then render the reviewed structure into Word.

**Tech Stack:** Python 3.11, Streamlit, OpenAI Python SDK, PyMuPDF, python-docx, Pydantic v2, pytest, Ruff.

## Global Constraints

- Hosted Streamlit web app.
- Single shared password only.
- `APP_PASSWORD` and `OPENAI_API_KEY` are server-side secrets.
- No database in v1.
- No permanent file storage in v1.
- English output only.
- Uploaded PDFs are the only source material.
- Topic selection is checklist-only; teachers cannot add, rename, or edit topics.
- Each section has exactly one question type.
- No answer key.
- Output format is `.docx` only.
- DOCX layout must match the structure of `data/Grade 7 PA 1 QP 26-27.pdf`.
- Map/diagram sections generate prompt text only, not embedded maps.
- The workspace is currently not a git repository; commit steps are included for future repo use and should be skipped until git is initialized.

---

## File Structure

- `app.py`: Streamlit entrypoint and guided workflow.
- `requirements.txt`: runtime and test dependencies.
- `.streamlit/secrets.example.toml`: documented secret names.
- `.gitignore`: local Python, Streamlit, and generated artifact ignores.
- `src/qpc/__init__.py`: package marker.
- `src/qpc/schemas.py`: Pydantic models and enums for documents, topics, blueprint sections, generated questions, and papers.
- `src/qpc/validators.py`: blueprint, generated paper, and topic-scope validation.
- `src/qpc/pdf_extractor.py`: PDF byte extraction using PyMuPDF, with text cleanup and page metadata.
- `src/qpc/topic_extractor.py`: OpenAI prompt construction and topic JSON parsing.
- `src/qpc/question_generator.py`: OpenAI prompt construction and generated-paper JSON parsing.
- `src/qpc/docx_exporter.py`: Word document rendering.
- `src/qpc/demo_data.py`: sample defaults for the paper metadata and sections.
- `tests/test_schemas.py`: schema behavior tests.
- `tests/test_validators.py`: validator tests.
- `tests/test_pdf_extractor.py`: extraction tests against sample PDFs.
- `tests/test_docx_exporter.py`: DOCX rendering tests.
- `tests/test_prompt_builders.py`: deterministic prompt/content tests for AI modules without network calls.

---

### Task 1: Project Scaffold And Tooling

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `.streamlit/secrets.example.toml`
- Create: `src/qpc/__init__.py`
- Create: `tests/test_imports.py`

**Interfaces:**
- Produces: importable package `qpc`.
- Produces: dependency list for Streamlit, PDF extraction, OpenAI calls, DOCX export, validation, and tests.

- [ ] **Step 1: Create dependency and config files**

`requirements.txt`:

```text
streamlit==1.37.1
openai==1.99.1
pymupdf==1.24.9
python-docx==1.1.2
pydantic==2.8.2
pytest==8.3.2
ruff==0.5.7
```

`.streamlit/secrets.example.toml`:

```toml
APP_PASSWORD = "replace-with-a-client-password"
OPENAI_API_KEY = "sk-replace-with-real-key"
OPENAI_MODEL = "gpt-4.1-mini"
```

`.gitignore`:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.venv/
venv/
.env
.streamlit/secrets.toml
generated/
*.docx
```

`src/qpc/__init__.py`:

```python
"""Question Paper Creator application package."""
```

- [ ] **Step 2: Write the import smoke test**

`tests/test_imports.py`:

```python
def test_package_imports():
    import qpc

    assert qpc.__doc__
```

- [ ] **Step 3: Run test to verify scaffold**

Run:

```bash
PYTHONPATH=src pytest tests/test_imports.py -v
```

Expected: PASS.

- [ ] **Step 4: Run lint**

Run:

```bash
PYTHONPATH=src ruff check src tests
```

Expected: PASS.

- [ ] **Step 5: Commit when git exists**

Run only after initializing git:

```bash
git add requirements.txt .gitignore .streamlit/secrets.example.toml src/qpc/__init__.py tests/test_imports.py
git commit -m "chore: scaffold question paper app"
```

---

### Task 2: Schemas

**Files:**
- Create: `src/qpc/schemas.py`
- Create: `tests/test_schemas.py`

**Interfaces:**
- Produces: `QuestionType` enum.
- Produces: `SourcePage`, `SourceDocument`, `Topic`, `TopicSet`, `PaperMetadata`, `SectionBlueprint`, `PaperBlueprint`.
- Produces: `GeneratedQuestion`, `GeneratedSection`, `GeneratedPaper`.
- Produces: `SectionBlueprint.section_marks() -> int`.
- Produces: `PaperBlueprint.total_marks() -> int`.

- [ ] **Step 1: Write schema tests**

`tests/test_schemas.py`:

```python
import pytest
from pydantic import ValidationError

from qpc.schemas import (
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperBlueprint,
    PaperMetadata,
    QuestionType,
    SectionBlueprint,
)


def test_section_and_paper_marks_are_calculated():
    metadata = PaperMetadata(
        grade="VII",
        subject="Social Science",
        exam_name="First Periodic Assessment 2026-27",
        date="17.07.2026",
        max_marks=30,
        duration="2 Hour",
    )
    sections = [
        SectionBlueprint(
            label="Section A",
            heading="Multiple Choice Based Questions",
            question_type=QuestionType.MCQ,
            questions_to_generate=4,
            questions_to_answer=4,
            marks_per_question=1,
        ),
        SectionBlueprint(
            label="Section B",
            heading="Very Short Answer Based Questions",
            question_type=QuestionType.VERY_SHORT,
            questions_to_generate=3,
            questions_to_answer=2,
            marks_per_question=2,
        ),
    ]

    blueprint = PaperBlueprint(metadata=metadata, sections=sections)

    assert sections[0].section_marks() == 4
    assert sections[1].section_marks() == 4
    assert blueprint.total_marks() == 8


def test_section_rejects_answer_count_greater_than_generated():
    with pytest.raises(ValidationError):
        SectionBlueprint(
            label="Section C",
            heading="Short Answer Based Questions",
            question_type=QuestionType.SHORT,
            questions_to_generate=2,
            questions_to_answer=3,
            marks_per_question=3,
        )


def test_generated_question_accepts_mcq_options():
    question = GeneratedQuestion(
        question_type=QuestionType.MCQ,
        text="Which element tells us the amount of water vapour in the air?",
        options=["Rainfall", "Humidity", "Temperature", "Wind"],
    )

    assert question.options[1] == "Humidity"


def test_generated_paper_round_trips_from_dict():
    paper = GeneratedPaper.model_validate(
        {
            "sections": [
                {
                    "label": "Section A",
                    "heading": "Multiple Choice Based Questions",
                    "question_type": "mcq",
                    "questions": [
                        {
                            "question_type": "mcq",
                            "text": "What is weather?",
                            "options": ["Air only", "State of atmosphere", "Ocean current", "Rock layer"],
                        }
                    ],
                }
            ]
        }
    )

    assert paper.sections[0].questions[0].question_type is QuestionType.MCQ
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=src pytest tests/test_schemas.py -v
```

Expected: FAIL because `qpc.schemas` does not exist.

- [ ] **Step 3: Implement schemas**

`src/qpc/schemas.py`:

```python
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


class QuestionType(StrEnum):
    MCQ = "mcq"
    VERY_SHORT = "very_short"
    SHORT = "short"
    LONG = "long"
    FILL_BLANKS = "fill_blanks"
    TRUE_FALSE = "true_false"
    MATCH = "match"
    CASE_STUDY = "case_study"
    MAP_DIAGRAM = "map_diagram"


class SourcePage(BaseModel):
    page_number: int = Field(ge=1)
    text: str


class SourceDocument(BaseModel):
    filename: str
    pages: list[SourcePage]

    def combined_text(self) -> str:
        return "\n\n".join(f"[Page {page.page_number}]\n{page.text}" for page in self.pages if page.text.strip())


class Topic(BaseModel):
    id: str
    document_filename: str
    name: str
    summary: str
    source_pages: list[int] = Field(default_factory=list)
    selected: bool = True


class TopicSet(BaseModel):
    topics: list[Topic]


class PaperMetadata(BaseModel):
    grade: str
    subject: str
    exam_name: str
    date: str
    max_marks: int = Field(gt=0)
    duration: str
    school_name: str = "ZENITH PUBLIC SCHOOL"
    school_address: str = "Plot no 13 & 14, Sector 5, Airoli, Navi Mumbai 400708"
    affiliation: str = "CBSE Affiliation No.- 1131335"


class SectionBlueprint(BaseModel):
    label: str
    heading: str
    question_type: QuestionType
    questions_to_generate: int = Field(gt=0)
    questions_to_answer: int = Field(gt=0)
    marks_per_question: int = Field(gt=0)
    instruction: str = ""

    @model_validator(mode="after")
    def answer_count_cannot_exceed_generated(self) -> "SectionBlueprint":
        if self.questions_to_answer > self.questions_to_generate:
            raise ValueError("questions_to_answer cannot exceed questions_to_generate")
        return self

    def section_marks(self) -> int:
        return self.questions_to_answer * self.marks_per_question


class PaperBlueprint(BaseModel):
    metadata: PaperMetadata
    sections: list[SectionBlueprint]

    @field_validator("sections")
    @classmethod
    def sections_cannot_be_empty(cls, value: list[SectionBlueprint]) -> list[SectionBlueprint]:
        if not value:
            raise ValueError("at least one section is required")
        return value

    def total_marks(self) -> int:
        return sum(section.section_marks() for section in self.sections)


class GeneratedQuestion(BaseModel):
    question_type: QuestionType
    text: str
    options: list[str] = Field(default_factory=list)
    pairs: list[tuple[str, str]] = Field(default_factory=list)
    sub_questions: list[str] = Field(default_factory=list)


class GeneratedSection(BaseModel):
    label: str
    heading: str
    question_type: QuestionType
    passage: str = ""
    questions: list[GeneratedQuestion]


class GeneratedPaper(BaseModel):
    sections: list[GeneratedSection]
```

- [ ] **Step 4: Run schema tests**

Run:

```bash
PYTHONPATH=src pytest tests/test_schemas.py -v
```

Expected: PASS.

- [ ] **Step 5: Run lint**

Run:

```bash
PYTHONPATH=src ruff check src/qpc/schemas.py tests/test_schemas.py
```

Expected: PASS.

- [ ] **Step 6: Commit when git exists**

```bash
git add src/qpc/schemas.py tests/test_schemas.py
git commit -m "feat: define question paper schemas"
```

---

### Task 3: Validators

**Files:**
- Create: `src/qpc/validators.py`
- Create: `tests/test_validators.py`

**Interfaces:**
- Consumes: schemas from Task 2.
- Produces: `ValidationIssue` dataclass.
- Produces: `validate_blueprint(blueprint: PaperBlueprint) -> list[ValidationIssue]`.
- Produces: `validate_generated_paper(blueprint: PaperBlueprint, paper: GeneratedPaper) -> list[ValidationIssue]`.

- [ ] **Step 1: Write validator tests**

`tests/test_validators.py`:

```python
from qpc.schemas import (
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperBlueprint,
    PaperMetadata,
    QuestionType,
    SectionBlueprint,
)
from qpc.validators import validate_blueprint, validate_generated_paper


def make_blueprint() -> PaperBlueprint:
    return PaperBlueprint(
        metadata=PaperMetadata(
            grade="VII",
            subject="Social Science",
            exam_name="First Periodic Assessment 2026-27",
            date="17.07.2026",
            max_marks=4,
            duration="2 Hour",
        ),
        sections=[
            SectionBlueprint(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions_to_generate=4,
                questions_to_answer=4,
                marks_per_question=1,
            )
        ],
    )


def test_validate_blueprint_detects_total_mismatch():
    blueprint = make_blueprint()
    blueprint.metadata.max_marks = 5

    issues = validate_blueprint(blueprint)

    assert [issue.code for issue in issues] == ["paper_total_mismatch"]


def test_validate_generated_paper_accepts_valid_mcq_section():
    blueprint = make_blueprint()
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions=[
                    GeneratedQuestion(question_type=QuestionType.MCQ, text=f"Question {i}", options=["A", "B", "C", "D"])
                    for i in range(1, 5)
                ],
            )
        ]
    )

    assert validate_generated_paper(blueprint, paper) == []


def test_validate_generated_paper_detects_missing_mcq_options():
    blueprint = make_blueprint()
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions=[
                    GeneratedQuestion(question_type=QuestionType.MCQ, text="Question 1", options=["A", "B"]),
                    GeneratedQuestion(question_type=QuestionType.MCQ, text="Question 2", options=["A", "B", "C", "D"]),
                    GeneratedQuestion(question_type=QuestionType.MCQ, text="Question 3", options=["A", "B", "C", "D"]),
                    GeneratedQuestion(question_type=QuestionType.MCQ, text="Question 4", options=["A", "B", "C", "D"]),
                ],
            )
        ]
    )

    issues = validate_generated_paper(blueprint, paper)

    assert "mcq_option_count" in {issue.code for issue in issues}


def test_validate_generated_paper_detects_wrong_question_count():
    blueprint = make_blueprint()
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions=[
                    GeneratedQuestion(question_type=QuestionType.MCQ, text="Question 1", options=["A", "B", "C", "D"])
                ],
            )
        ]
    )

    issues = validate_generated_paper(blueprint, paper)

    assert "question_count_mismatch" in {issue.code for issue in issues}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src pytest tests/test_validators.py -v
```

Expected: FAIL because `qpc.validators` does not exist.

- [ ] **Step 3: Implement validators**

`src/qpc/validators.py`:

```python
from dataclasses import dataclass

from qpc.schemas import GeneratedPaper, PaperBlueprint, QuestionType


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    section_label: str = ""


def validate_blueprint(blueprint: PaperBlueprint) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    total = blueprint.total_marks()
    if total != blueprint.metadata.max_marks:
        issues.append(
            ValidationIssue(
                code="paper_total_mismatch",
                message=f"Configured sections total {total} marks, but max marks is {blueprint.metadata.max_marks}.",
            )
        )
    return issues


def validate_generated_paper(blueprint: PaperBlueprint, paper: GeneratedPaper) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    expected_by_label = {section.label: section for section in blueprint.sections}
    generated_by_label = {section.label: section for section in paper.sections}

    for blueprint_section in blueprint.sections:
        generated_section = generated_by_label.get(blueprint_section.label)
        if generated_section is None:
            issues.append(
                ValidationIssue(
                    code="missing_section",
                    message=f"{blueprint_section.label} is missing from generated paper.",
                    section_label=blueprint_section.label,
                )
            )
            continue

        if generated_section.question_type != blueprint_section.question_type:
            issues.append(
                ValidationIssue(
                    code="section_type_mismatch",
                    message=f"{blueprint_section.label} should be {blueprint_section.question_type}.",
                    section_label=blueprint_section.label,
                )
            )

        if len(generated_section.questions) != blueprint_section.questions_to_generate:
            issues.append(
                ValidationIssue(
                    code="question_count_mismatch",
                    message=(
                        f"{blueprint_section.label} should contain "
                        f"{blueprint_section.questions_to_generate} questions."
                    ),
                    section_label=blueprint_section.label,
                )
            )

        if blueprint_section.question_type is QuestionType.CASE_STUDY and not generated_section.passage.strip():
            issues.append(
                ValidationIssue(
                    code="missing_case_study_passage",
                    message=f"{blueprint_section.label} needs a case-study passage.",
                    section_label=blueprint_section.label,
                )
            )

        for question in generated_section.questions:
            if len(question.text.strip()) < 8:
                issues.append(
                    ValidationIssue(
                        code="question_too_short",
                        message=f"{blueprint_section.label} contains an empty or too-short question.",
                        section_label=blueprint_section.label,
                    )
                )
            if blueprint_section.question_type is QuestionType.MCQ and len(question.options) != 4:
                issues.append(
                    ValidationIssue(
                        code="mcq_option_count",
                        message=f"{blueprint_section.label} MCQs must have exactly four options.",
                        section_label=blueprint_section.label,
                    )
                )
            if question.question_type != blueprint_section.question_type:
                issues.append(
                    ValidationIssue(
                        code="question_type_mismatch",
                        message=f"{blueprint_section.label} contains a question with the wrong type.",
                        section_label=blueprint_section.label,
                    )
                )

    extra_labels = set(generated_by_label) - set(expected_by_label)
    for label in sorted(extra_labels):
        issues.append(
            ValidationIssue(
                code="unexpected_section",
                message=f"{label} was generated but is not in the blueprint.",
                section_label=label,
            )
        )

    return issues
```

- [ ] **Step 4: Run validator tests**

```bash
PYTHONPATH=src pytest tests/test_validators.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit when git exists**

```bash
git add src/qpc/validators.py tests/test_validators.py
git commit -m "feat: validate question paper structures"
```

---

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

### Task 5: Prompt Builders And AI Adapters

**Files:**
- Create: `src/qpc/topic_extractor.py`
- Create: `src/qpc/question_generator.py`
- Create: `tests/test_prompt_builders.py`

**Interfaces:**
- Consumes: schemas from Task 2.
- Produces: `build_topic_prompt(documents: list[SourceDocument]) -> str`.
- Produces: `parse_topic_response(payload: dict) -> TopicSet`.
- Produces: `extract_topics_with_ai(documents: list[SourceDocument], api_key: str, model: str) -> TopicSet`.
- Produces: `build_question_prompt(documents: list[SourceDocument], selected_topics: list[Topic], blueprint: PaperBlueprint) -> str`.
- Produces: `parse_generated_paper_response(payload: dict) -> GeneratedPaper`.
- Produces: `generate_questions_with_ai(documents: list[SourceDocument], selected_topics: list[Topic], blueprint: PaperBlueprint, api_key: str, model: str) -> GeneratedPaper`.

- [ ] **Step 1: Write prompt builder tests**

`tests/test_prompt_builders.py`:

```python
from qpc.question_generator import build_question_prompt, parse_generated_paper_response
from qpc.schemas import PaperBlueprint, PaperMetadata, QuestionType, SectionBlueprint, SourceDocument, SourcePage, Topic
from qpc.topic_extractor import build_topic_prompt, parse_topic_response


def test_build_topic_prompt_includes_document_text():
    document = SourceDocument(
        filename="weather.pdf",
        pages=[SourcePage(page_number=1, text="Weather is a state of the Earth's atmosphere.")],
    )

    prompt = build_topic_prompt([document])

    assert "weather.pdf" in prompt
    assert "Weather is a state" in prompt
    assert "Return JSON" in prompt


def test_parse_topic_response_returns_topic_set():
    payload = {
        "topics": [
            {
                "id": "weather-elements",
                "document_filename": "weather.pdf",
                "name": "Elements of weather",
                "summary": "Temperature, precipitation, pressure, wind, and humidity.",
                "source_pages": [2, 3],
            }
        ]
    }

    topic_set = parse_topic_response(payload)

    assert topic_set.topics[0].selected is True
    assert topic_set.topics[0].name == "Elements of weather"


def test_build_question_prompt_includes_selected_topics_and_blueprint():
    document = SourceDocument(
        filename="weather.pdf",
        pages=[SourcePage(page_number=1, text="Humidity is the amount of water vapour in the air.")],
    )
    topic = Topic(
        id="humidity",
        document_filename="weather.pdf",
        name="Humidity",
        summary="Water vapour in air.",
        source_pages=[1],
    )
    blueprint = PaperBlueprint(
        metadata=PaperMetadata(
            grade="VII",
            subject="Social Science",
            exam_name="First Periodic Assessment 2026-27",
            date="17.07.2026",
            max_marks=4,
            duration="2 Hour",
        ),
        sections=[
            SectionBlueprint(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions_to_generate=4,
                questions_to_answer=4,
                marks_per_question=1,
            )
        ],
    )

    prompt = build_question_prompt([document], [topic], blueprint)

    assert "Humidity" in prompt
    assert "Section A" in prompt
    assert "exactly four options" in prompt
    assert "Do not generate an answer key" in prompt


def test_parse_generated_paper_response_returns_paper():
    payload = {
        "sections": [
            {
                "label": "Section A",
                "heading": "Multiple Choice Based Questions",
                "question_type": "mcq",
                "questions": [
                    {
                        "question_type": "mcq",
                        "text": "Which element tells us the amount of water vapour in the air?",
                        "options": ["Rainfall", "Humidity", "Temperature", "Wind"],
                    }
                ],
            }
        ]
    }

    paper = parse_generated_paper_response(payload)

    assert paper.sections[0].questions[0].options[1] == "Humidity"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src pytest tests/test_prompt_builders.py -v
```

Expected: FAIL because the AI modules do not exist.

- [ ] **Step 3: Implement topic extractor**

`src/qpc/topic_extractor.py`:

```python
import json

from openai import OpenAI

from qpc.schemas import SourceDocument, TopicSet


def build_topic_prompt(documents: list[SourceDocument]) -> str:
    document_blocks = "\n\n".join(
        f"DOCUMENT: {document.filename}\n{document.combined_text()[:16000]}" for document in documents
    )
    return f"""
You extract question-paper topics from textbook chapter text.

Rules:
- Return JSON only.
- Return topics grounded in the provided text.
- Do not invent topics.
- Use concise topic names.
- Include a short summary.
- Include source_pages when page markers show the topic location.

Return JSON with this shape:
{{
  "topics": [
    {{
      "id": "stable-kebab-case-id",
      "document_filename": "source filename",
      "name": "Topic name",
      "summary": "One sentence summary",
      "source_pages": [1, 2]
    }}
  ]
}}

Source material:
{document_blocks}
""".strip()


def parse_topic_response(payload: dict) -> TopicSet:
    return TopicSet.model_validate(payload)


def extract_topics_with_ai(documents: list[SourceDocument], api_key: str, model: str) -> TopicSet:
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=build_topic_prompt(documents),
        text={"format": {"type": "json_object"}},
    )
    payload = json.loads(response.output_text)
    return parse_topic_response(payload)
```

- [ ] **Step 4: Implement question generator**

`src/qpc/question_generator.py`:

```python
import json

from openai import OpenAI

from qpc.schemas import GeneratedPaper, PaperBlueprint, SourceDocument, Topic


def build_question_prompt(
    documents: list[SourceDocument],
    selected_topics: list[Topic],
    blueprint: PaperBlueprint,
) -> str:
    topic_lines = "\n".join(
        f"- {topic.name} ({topic.document_filename}, pages {topic.source_pages}): {topic.summary}"
        for topic in selected_topics
    )
    section_lines = "\n".join(
        (
            f"- {section.label}: {section.heading}; type={section.question_type.value}; "
            f"generate={section.questions_to_generate}; answer={section.questions_to_answer}; "
            f"marks_each={section.marks_per_question}; instruction={section.instruction or 'none'}"
        )
        for section in blueprint.sections
    )
    source_blocks = "\n\n".join(
        f"DOCUMENT: {document.filename}\n{document.combined_text()[:16000]}" for document in documents
    )
    return f"""
You generate an English school question paper from selected textbook topics.

Rules:
- Use only the selected topics and source material below.
- Do not generate an answer key.
- Do not include unsupported topics.
- Each section must use exactly its configured question type.
- MCQ questions must include exactly four options.
- Case study sections must include a passage and the configured number of sub-questions.
- Map/diagram sections generate prompt text only; do not ask for an embedded image.
- Return JSON only.

Selected topics:
{topic_lines}

Section blueprint:
{section_lines}

Return JSON with this shape:
{{
  "sections": [
    {{
      "label": "Section A",
      "heading": "Multiple Choice Based Questions",
      "question_type": "mcq",
      "passage": "",
      "questions": [
        {{
          "question_type": "mcq",
          "text": "Question text",
          "options": ["A", "B", "C", "D"],
          "pairs": [],
          "sub_questions": []
        }}
      ]
    }}
  ]
}}

Source material:
{source_blocks}
""".strip()


def parse_generated_paper_response(payload: dict) -> GeneratedPaper:
    return GeneratedPaper.model_validate(payload)


def generate_questions_with_ai(
    documents: list[SourceDocument],
    selected_topics: list[Topic],
    blueprint: PaperBlueprint,
    api_key: str,
    model: str,
) -> GeneratedPaper:
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=build_question_prompt(documents, selected_topics, blueprint),
        text={"format": {"type": "json_object"}},
    )
    payload = json.loads(response.output_text)
    return parse_generated_paper_response(payload)
```

- [ ] **Step 5: Run prompt tests**

```bash
PYTHONPATH=src pytest tests/test_prompt_builders.py -v
```

Expected: PASS without network access.

- [ ] **Step 6: Commit when git exists**

```bash
git add src/qpc/topic_extractor.py src/qpc/question_generator.py tests/test_prompt_builders.py
git commit -m "feat: build ai prompts for topics and questions"
```

---

### Task 6: DOCX Exporter

**Files:**
- Create: `src/qpc/docx_exporter.py`
- Create: `tests/test_docx_exporter.py`

**Interfaces:**
- Consumes: `PaperMetadata`, `PaperBlueprint`, `GeneratedPaper`.
- Produces: `render_docx(blueprint: PaperBlueprint, paper: GeneratedPaper) -> bytes`.

- [ ] **Step 1: Write DOCX tests**

`tests/test_docx_exporter.py`:

```python
from io import BytesIO

from docx import Document

from qpc.docx_exporter import render_docx
from qpc.schemas import (
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperBlueprint,
    PaperMetadata,
    QuestionType,
    SectionBlueprint,
)


def test_render_docx_contains_header_and_questions():
    blueprint = PaperBlueprint(
        metadata=PaperMetadata(
            grade="VII",
            subject="Social Science",
            exam_name="First Periodic Assessment 2026-27",
            date="17.07.2026",
            max_marks=4,
            duration="2 Hour",
        ),
        sections=[
            SectionBlueprint(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions_to_generate=1,
                questions_to_answer=1,
                marks_per_question=4,
            )
        ],
    )
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions=[
                    GeneratedQuestion(
                        question_type=QuestionType.MCQ,
                        text="Which physical feature is known as the storehouse of water?",
                        options=["Coastal Plains", "Himalayas", "Deccan Plateau", "Islands"],
                    )
                ],
            )
        ]
    )

    data = render_docx(blueprint, paper)
    document = Document(BytesIO(data))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)

    assert "ZENITH PUBLIC SCHOOL" in text
    assert "First Periodic Assessment 2026-27" in text
    assert "Section A" in text
    assert "Which physical feature" in text
    assert "*****" in text
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src pytest tests/test_docx_exporter.py -v
```

Expected: FAIL because `qpc.docx_exporter` does not exist.

- [ ] **Step 3: Implement exporter**

`src/qpc/docx_exporter.py`:

```python
from io import BytesIO

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from qpc.schemas import GeneratedPaper, PaperBlueprint, QuestionType, SectionBlueprint


def render_docx(blueprint: PaperBlueprint, paper: GeneratedPaper) -> bytes:
    document = Document()
    style = document.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)

    _add_header(document, blueprint)
    sections_by_label = {section.label: section for section in paper.sections}
    for section_blueprint in blueprint.sections:
        generated_section = sections_by_label[section_blueprint.label]
        _add_section(document, section_blueprint, generated_section)

    end = document.add_paragraph("*****")
    end.alignment = WD_ALIGN_PARAGRAPH.CENTER

    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _add_header(document: Document, blueprint: PaperBlueprint) -> None:
    metadata = blueprint.metadata
    school = document.add_paragraph(metadata.school_name)
    school.alignment = WD_ALIGN_PARAGRAPH.CENTER
    school.runs[0].bold = True
    school.runs[0].font.size = Pt(14)

    address = document.add_paragraph(metadata.school_address)
    address.alignment = WD_ALIGN_PARAGRAPH.CENTER
    affiliation = document.add_paragraph(f"({metadata.affiliation})")
    affiliation.alignment = WD_ALIGN_PARAGRAPH.CENTER

    exam = document.add_paragraph(metadata.exam_name)
    exam.alignment = WD_ALIGN_PARAGRAPH.CENTER
    exam.runs[0].bold = True

    table = document.add_table(rows=3, cols=2)
    table.cell(0, 0).text = f"Grade: {metadata.grade}"
    table.cell(0, 1).text = f"Subject: - {metadata.subject}"
    table.cell(1, 0).text = "Name: -_____________________________"
    table.cell(1, 1).text = f"Date: - {metadata.date}"
    table.cell(2, 0).text = "Roll No: - _______"
    table.cell(2, 1).text = f"M.M. {metadata.max_marks}        Time- {metadata.duration}"


def _section_summary(section: SectionBlueprint) -> str:
    total = section.section_marks()
    if section.questions_to_answer < section.questions_to_generate:
        return f"{section.heading} (Any {section.questions_to_answer}) ({section.questions_to_answer}x{section.marks_per_question}={total})"
    return f"{section.heading} ({section.questions_to_answer}x{section.marks_per_question}={total})"


def _add_section(document: Document, section_blueprint: SectionBlueprint, generated_section) -> None:
    label = document.add_paragraph(section_blueprint.label)
    label.alignment = WD_ALIGN_PARAGRAPH.CENTER
    label.runs[0].bold = True

    summary = document.add_paragraph(_section_summary(section_blueprint))
    summary.alignment = WD_ALIGN_PARAGRAPH.CENTER
    summary.runs[0].bold = True

    if generated_section.passage.strip():
        document.add_paragraph(generated_section.passage.strip())

    for index, question in enumerate(generated_section.questions, start=1):
        document.add_paragraph(f"{index}. {question.text.strip()}")
        if section_blueprint.question_type is QuestionType.MCQ:
            options = " ".join(f"{chr(97 + option_index)}) {option}" for option_index, option in enumerate(question.options))
            document.add_paragraph(options)
        elif section_blueprint.question_type is QuestionType.MATCH:
            for left, right in question.pairs:
                document.add_paragraph(f"{left} — {right}")
        for sub_index, sub_question in enumerate(question.sub_questions, start=1):
            document.add_paragraph(f"({sub_index}) {sub_question}")
```

- [ ] **Step 4: Run DOCX tests**

```bash
PYTHONPATH=src pytest tests/test_docx_exporter.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit when git exists**

```bash
git add src/qpc/docx_exporter.py tests/test_docx_exporter.py
git commit -m "feat: render question paper docx"
```

---

### Task 7: Demo Defaults

**Files:**
- Create: `src/qpc/demo_data.py`
- Create: `tests/test_demo_data.py`

**Interfaces:**
- Consumes: schemas from Task 2.
- Produces: `default_metadata() -> PaperMetadata`.
- Produces: `default_sections() -> list[SectionBlueprint]`.
- Produces: `default_blueprint() -> PaperBlueprint`.

- [ ] **Step 1: Write default tests**

`tests/test_demo_data.py`:

```python
from qpc.demo_data import default_blueprint
from qpc.schemas import QuestionType


def test_default_blueprint_matches_sample_total():
    blueprint = default_blueprint()

    assert blueprint.metadata.max_marks == 30
    assert blueprint.total_marks() == 30
    assert [section.question_type for section in blueprint.sections] == [
        QuestionType.MCQ,
        QuestionType.VERY_SHORT,
        QuestionType.SHORT,
        QuestionType.LONG,
        QuestionType.CASE_STUDY,
        QuestionType.MAP_DIAGRAM,
    ]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src pytest tests/test_demo_data.py -v
```

Expected: FAIL because `qpc.demo_data` does not exist.

- [ ] **Step 3: Implement defaults**

`src/qpc/demo_data.py`:

```python
from qpc.schemas import PaperBlueprint, PaperMetadata, QuestionType, SectionBlueprint


def default_metadata() -> PaperMetadata:
    return PaperMetadata(
        grade="VII",
        subject="Social Science",
        exam_name="First Periodic Assessment 2026-27",
        date="17.07.2026",
        max_marks=30,
        duration="2 Hour",
    )


def default_sections() -> list[SectionBlueprint]:
    return [
        SectionBlueprint(
            label="Section A",
            heading="Multiple Choice Based Questions",
            question_type=QuestionType.MCQ,
            questions_to_generate=4,
            questions_to_answer=4,
            marks_per_question=1,
        ),
        SectionBlueprint(
            label="Section B",
            heading="Very Short Answer Based Questions",
            question_type=QuestionType.VERY_SHORT,
            questions_to_generate=3,
            questions_to_answer=2,
            marks_per_question=2,
        ),
        SectionBlueprint(
            label="Section C",
            heading="Short Answer Based Questions",
            question_type=QuestionType.SHORT,
            questions_to_generate=4,
            questions_to_answer=3,
            marks_per_question=3,
        ),
        SectionBlueprint(
            label="Section D",
            heading="Long Answer Questions",
            question_type=QuestionType.LONG,
            questions_to_generate=3,
            questions_to_answer=2,
            marks_per_question=5,
        ),
        SectionBlueprint(
            label="Section E",
            heading="Case Study Based Questions",
            question_type=QuestionType.CASE_STUDY,
            questions_to_generate=2,
            questions_to_answer=2,
            marks_per_question=1,
        ),
        SectionBlueprint(
            label="Section F",
            heading="Map Based Question",
            question_type=QuestionType.MAP_DIAGRAM,
            questions_to_generate=1,
            questions_to_answer=1,
            marks_per_question=1,
        ),
    ]


def default_blueprint() -> PaperBlueprint:
    return PaperBlueprint(metadata=default_metadata(), sections=default_sections())
```

- [ ] **Step 4: Run default tests**

```bash
PYTHONPATH=src pytest tests/test_demo_data.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit when git exists**

```bash
git add src/qpc/demo_data.py tests/test_demo_data.py
git commit -m "feat: add sample paper defaults"
```

---

### Task 8: Streamlit App Workflow

**Files:**
- Create: `app.py`
- Create: `tests/test_app_config.py`

**Interfaces:**
- Consumes: all modules from earlier tasks.
- Produces: `load_secret(name: str, default: str = "") -> str`.
- Produces: hosted Streamlit UI with password, upload, topics, paper config, generation, review, and DOCX download.

- [ ] **Step 1: Write config test**

`tests/test_app_config.py`:

```python
from app import load_secret


def test_load_secret_returns_default_for_missing_value(monkeypatch):
    class EmptySecrets(dict):
        def get(self, key, default=None):
            return default

    monkeypatch.setattr("streamlit.secrets", EmptySecrets())

    assert load_secret("MISSING", "fallback") == "fallback"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
PYTHONPATH=src pytest tests/test_app_config.py -v
```

Expected: FAIL because `app.py` does not exist.

- [ ] **Step 3: Implement Streamlit app**

`app.py`:

```python
from __future__ import annotations

import os

import streamlit as st

from qpc.demo_data import default_blueprint
from qpc.docx_exporter import render_docx
from qpc.pdf_extractor import extract_pdf_bytes
from qpc.question_generator import generate_questions_with_ai
from qpc.schemas import GeneratedPaper, PaperBlueprint, QuestionType, SectionBlueprint, Topic
from qpc.topic_extractor import extract_topics_with_ai
from qpc.validators import validate_blueprint, validate_generated_paper


def load_secret(name: str, default: str = "") -> str:
    return str(st.secrets.get(name, os.environ.get(name, default)))


def ensure_state() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "documents" not in st.session_state:
        st.session_state.documents = []
    if "topics" not in st.session_state:
        st.session_state.topics = []
    if "blueprint" not in st.session_state:
        st.session_state.blueprint = default_blueprint()
    if "paper" not in st.session_state:
        st.session_state.paper = None


def password_gate() -> bool:
    if st.session_state.authenticated:
        return True
    st.title("Question Paper Creator")
    password = st.text_input("Password", type="password")
    if st.button("Enter"):
        if password and password == load_secret("APP_PASSWORD"):
            st.session_state.authenticated = True
            st.rerun()
        st.error("Incorrect password.")
    return False


def upload_step() -> None:
    st.header("1. Upload chapter PDFs")
    files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)
    if st.button("Extract text", disabled=not files):
        st.session_state.documents = [extract_pdf_bytes(file.name, file.getvalue()) for file in files]
        st.session_state.topics = []
        st.session_state.paper = None
    for document in st.session_state.documents:
        st.write(f"{document.filename}: {len(document.pages)} pages")


def topic_step() -> None:
    st.header("2. Select topics")
    api_key = load_secret("OPENAI_API_KEY")
    model = load_secret("OPENAI_MODEL", "gpt-4.1-mini")
    if st.button("Extract topics with AI", disabled=not st.session_state.documents):
        topic_set = extract_topics_with_ai(st.session_state.documents, api_key=api_key, model=model)
        st.session_state.topics = topic_set.topics

    updated_topics: list[Topic] = []
    for topic in st.session_state.topics:
        selected = st.checkbox(
            f"{topic.name} — {topic.summary}",
            value=topic.selected,
            key=f"topic_{topic.id}",
        )
        updated_topics.append(topic.model_copy(update={"selected": selected}))
    st.session_state.topics = updated_topics


def configure_step() -> None:
    st.header("3. Configure paper")
    blueprint: PaperBlueprint = st.session_state.blueprint
    metadata = blueprint.metadata

    metadata.grade = st.text_input("Grade", metadata.grade)
    metadata.subject = st.text_input("Subject", metadata.subject)
    metadata.exam_name = st.text_input("Exam name", metadata.exam_name)
    metadata.date = st.text_input("Date", metadata.date)
    metadata.duration = st.text_input("Time", metadata.duration)
    metadata.max_marks = st.number_input("Maximum marks", min_value=1, value=metadata.max_marks, step=1)

    st.subheader("Sections")
    sections: list[SectionBlueprint] = []
    for index, section in enumerate(blueprint.sections):
        with st.expander(section.label, expanded=True):
            label = st.text_input("Section label", section.label, key=f"label_{index}")
            heading = st.text_input("Heading", section.heading, key=f"heading_{index}")
            question_type = st.selectbox(
                "Question type",
                list(QuestionType),
                index=list(QuestionType).index(section.question_type),
                format_func=lambda value: value.value.replace("_", " ").title(),
                key=f"type_{index}",
            )
            generate = st.number_input("Questions to generate", min_value=1, value=section.questions_to_generate, key=f"gen_{index}")
            answer = st.number_input("Questions to answer", min_value=1, max_value=generate, value=min(section.questions_to_answer, generate), key=f"ans_{index}")
            marks = st.number_input("Marks per question", min_value=1, value=section.marks_per_question, key=f"marks_{index}")
            instruction = st.text_input("Optional instruction", section.instruction, key=f"instruction_{index}")
            sections.append(
                SectionBlueprint(
                    label=label,
                    heading=heading,
                    question_type=question_type,
                    questions_to_generate=generate,
                    questions_to_answer=answer,
                    marks_per_question=marks,
                    instruction=instruction,
                )
            )

    if st.button("Add section"):
        sections.append(
            SectionBlueprint(
                label=f"Section {chr(65 + len(sections))}",
                heading="Short Answer Based Questions",
                question_type=QuestionType.SHORT,
                questions_to_generate=3,
                questions_to_answer=3,
                marks_per_question=2,
            )
        )

    st.session_state.blueprint = PaperBlueprint(metadata=metadata, sections=sections)
    issues = validate_blueprint(st.session_state.blueprint)
    st.write(f"Calculated marks: {st.session_state.blueprint.total_marks()}")
    for issue in issues:
        st.warning(issue.message)


def generation_step() -> None:
    st.header("4. Generate and review")
    selected_topics = [topic for topic in st.session_state.topics if topic.selected]
    api_key = load_secret("OPENAI_API_KEY")
    model = load_secret("OPENAI_MODEL", "gpt-4.1-mini")
    disabled = not st.session_state.documents or not selected_topics or bool(validate_blueprint(st.session_state.blueprint))
    if st.button("Generate paper", disabled=disabled):
        paper = generate_questions_with_ai(
            st.session_state.documents,
            selected_topics,
            st.session_state.blueprint,
            api_key=api_key,
            model=model,
        )
        issues = validate_generated_paper(st.session_state.blueprint, paper)
        if issues:
            for issue in issues:
                st.error(issue.message)
        else:
            st.session_state.paper = paper

    paper: GeneratedPaper | None = st.session_state.paper
    if paper is None:
        return

    for section_index, section in enumerate(paper.sections):
        st.subheader(section.label)
        if section.passage:
            section.passage = st.text_area("Passage", section.passage, key=f"passage_{section_index}")
        for question_index, question in enumerate(section.questions):
            question.text = st.text_area(
                f"Question {question_index + 1}",
                question.text,
                key=f"question_{section_index}_{question_index}",
            )
            if question.question_type is QuestionType.MCQ:
                question.options = [
                    st.text_input(
                        f"Option {option_index + 1}",
                        option,
                        key=f"option_{section_index}_{question_index}_{option_index}",
                    )
                    for option_index, option in enumerate(question.options)
                ]


def download_step() -> None:
    st.header("5. Download")
    if st.session_state.paper is None:
        st.info("Generate a valid paper before downloading.")
        return
    data = render_docx(st.session_state.blueprint, st.session_state.paper)
    st.download_button(
        "Download Word document",
        data=data,
        file_name="question-paper.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def main() -> None:
    st.set_page_config(page_title="Question Paper Creator", layout="wide")
    ensure_state()
    if not password_gate():
        return
    upload_step()
    topic_step()
    configure_step()
    generation_step()
    download_step()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run config test**

```bash
PYTHONPATH=src pytest tests/test_app_config.py -v
```

Expected: PASS.

- [ ] **Step 5: Run full test suite**

```bash
PYTHONPATH=src pytest -v
```

Expected: PASS.

- [ ] **Step 6: Run app locally**

Run:

```bash
PYTHONPATH=src streamlit run app.py
```

Expected: Streamlit starts and shows the password screen.

- [ ] **Step 7: Commit when git exists**

```bash
git add app.py tests/test_app_config.py
git commit -m "feat: add streamlit workflow"
```

---

### Task 9: Deployment Notes And Final Verification

**Files:**
- Create: `README.md`
- Create: `docs/deployment.md`

**Interfaces:**
- Consumes: completed app from prior tasks.
- Produces: operator instructions for local run, secrets, tests, and hosted deployment.

- [ ] **Step 1: Create README**

`README.md`:

```markdown
# Question Paper Creator

Hosted Streamlit app for generating editable Word question papers from uploaded chapter PDFs.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
PYTHONPATH=src streamlit run app.py
```

Set real values in `.streamlit/secrets.toml` before using AI generation.

## Tests

```bash
PYTHONPATH=src pytest -v
PYTHONPATH=src ruff check src tests app.py
```

## V1 Limits

- Single shared password.
- No saved history.
- No answer key.
- English only.
- DOCX export only.
```

- [ ] **Step 2: Create deployment doc**

`docs/deployment.md`:

```markdown
# Deployment

## Streamlit Community Cloud

1. Push the repository to GitHub.
2. Create a Streamlit Community Cloud app from the repository.
3. Set the main file path to `app.py`.
4. Add secrets:

```toml
APP_PASSWORD = "client-password"
OPENAI_API_KEY = "real-openai-key"
OPENAI_MODEL = "gpt-4.1-mini"
```

5. Deploy the app.
6. Share the Streamlit app URL and password with the client.

## Render Or Railway

Use this route when stronger privacy or operational control is needed. Configure the same environment variables as secrets and run:

```bash
PYTHONPATH=src streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

## Operational Notes

- Rotate `APP_PASSWORD` if the URL is shared beyond the intended client.
- Track OpenAI API usage in the OpenAI dashboard.
- Do not commit `.streamlit/secrets.toml`.
- The app is session-based and does not preserve generated papers.
```

- [ ] **Step 3: Run full verification**

```bash
PYTHONPATH=src pytest -v
PYTHONPATH=src ruff check src tests app.py
```

Expected: PASS.

- [ ] **Step 4: Manual local smoke test**

Run:

```bash
PYTHONPATH=src streamlit run app.py
```

Manual checks:

- Password screen appears.
- Correct password unlocks the app.
- `data/gees101 Geographical Diversity of India.pdf` uploads.
- `data/gees102 Understanding the Weather.pdf` uploads.
- Text extraction reports page counts.
- Topic extraction works when `OPENAI_API_KEY` is configured.
- Blueprint marks total displays correctly.
- Paper generation works when topics are selected.
- Review fields appear.
- DOCX downloads and opens in Word or LibreOffice.

- [ ] **Step 5: Commit when git exists**

```bash
git add README.md docs/deployment.md
git commit -m "docs: add setup and deployment instructions"
```

---

## Self-Review Checklist

- Spec coverage: The plan includes hosted Streamlit delivery, single password, PDF upload/extraction, AI topic checklist, section blueprint, structured editing, no answer key, English-only generation, DOCX export, and deployment docs.
- Placeholder scan: The plan contains concrete files, commands, and code blocks for each implementation task.
- Type consistency: The interfaces introduced in `schemas.py` are consumed by validators, AI modules, DOCX export, demo defaults, and Streamlit using the same class and function names.
- Scope control: The plan does not add accounts, persistence, answer keys, PDF export, multilingual generation, or rich document editing.
