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

