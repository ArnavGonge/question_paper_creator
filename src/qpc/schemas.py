from enum import StrEnum
from typing import Any

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
        return "\n\n".join(
            f"[Page {page.page_number}]\n{page.text}"
            for page in self.pages
            if page.text.strip()
        )


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
    def sections_cannot_be_empty(
        cls, value: list[SectionBlueprint]
    ) -> list[SectionBlueprint]:
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

    @field_validator("sub_questions", mode="before")
    @classmethod
    def sub_question_objects_to_text(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value
        return [
            item["text"]
            if isinstance(item, dict) and "text" in item
            else item
            for item in value
        ]


class GeneratedSection(BaseModel):
    label: str
    heading: str
    question_type: QuestionType
    passage: str = ""
    questions: list[GeneratedQuestion]

    @model_validator(mode="after")
    def questions_must_match_section_type(self) -> "GeneratedSection":
        for question in self.questions:
            if question.question_type is not self.question_type:
                raise ValueError(
                    "all questions in a section must match section question_type"
                )
        return self


class GeneratedPaper(BaseModel):
    sections: list[GeneratedSection]
