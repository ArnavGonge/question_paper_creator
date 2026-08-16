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
    SourceDocument,
    SourcePage,
    Topic,
    TopicSet,
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


def test_source_document_combines_non_empty_pages_with_headers():
    document = SourceDocument(
        filename="chapter-1.pdf",
        pages=[
            SourcePage(page_number=1, text="Air has pressure."),
            SourcePage(page_number=2, text="   "),
            SourcePage(page_number=3, text="Wind moves from high to low pressure."),
        ],
    )

    assert (
        document.combined_text()
        == "[Page 1]\nAir has pressure.\n\n[Page 3]\nWind moves from high to low pressure."
    )


def test_topic_and_topic_set_defaults_are_applied():
    topic = Topic(
        id="topic-1",
        document_filename="chapter-1.pdf",
        name="Weather",
        summary="State of the atmosphere at a place and time.",
    )
    topic_set = TopicSet(topics=[topic])

    assert topic.source_pages == []
    assert topic.selected is True
    assert topic_set.topics[0] == topic


def test_paper_blueprint_rejects_empty_sections():
    metadata = PaperMetadata(
        grade="VII",
        subject="Social Science",
        exam_name="First Periodic Assessment 2026-27",
        date="17.07.2026",
        max_marks=30,
        duration="2 Hour",
    )

    with pytest.raises(ValidationError):
        PaperBlueprint(metadata=metadata, sections=[])


def test_generated_section_rejects_mixed_question_types():
    with pytest.raises(ValidationError):
        GeneratedSection(
            label="Section A",
            heading="Multiple Choice Based Questions",
            question_type=QuestionType.MCQ,
            questions=[
                GeneratedQuestion(
                    question_type=QuestionType.MCQ,
                    text="What is weather?",
                    options=[
                        "Air only",
                        "State of atmosphere",
                        "Ocean current",
                        "Rock layer",
                    ],
                ),
                GeneratedQuestion(
                    question_type=QuestionType.SHORT,
                    text="Explain humidity.",
                ),
            ],
        )


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
                            "options": [
                                "Air only",
                                "State of atmosphere",
                                "Ocean current",
                                "Rock layer",
                            ],
                        }
                    ],
                }
            ]
        }
    )

    assert isinstance(paper.sections[0], GeneratedSection)
    assert paper.sections[0].questions[0].question_type is QuestionType.MCQ
