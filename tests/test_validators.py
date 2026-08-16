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


def test_validate_generated_paper_detects_wrong_match_pair_count():
    blueprint = PaperBlueprint(
        metadata=make_blueprint().metadata,
        sections=[
            SectionBlueprint(
                label="Section B",
                heading="Match the Following",
                question_type=QuestionType.MATCH,
                questions_to_generate=2,
                questions_to_answer=1,
                marks_per_question=2,
            )
        ],
    )
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section B",
                heading="Match the Following",
                question_type=QuestionType.MATCH,
                questions=[
                    GeneratedQuestion(
                        question_type=QuestionType.MATCH,
                        text="Match the landforms.",
                        pairs=[("Himalayas", "Mountains")],
                    )
                ],
            )
        ]
    )

    issues = validate_generated_paper(blueprint, paper)

    assert "match_pair_count" in {issue.code for issue in issues}


def test_validate_generated_paper_detects_wrong_case_study_sub_question_count():
    blueprint = PaperBlueprint(
        metadata=make_blueprint().metadata,
        sections=[
            SectionBlueprint(
                label="Section C",
                heading="Case Study",
                question_type=QuestionType.CASE_STUDY,
                questions_to_generate=2,
                questions_to_answer=1,
                marks_per_question=4,
            )
        ],
    )
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section C",
                heading="Case Study",
                question_type=QuestionType.CASE_STUDY,
                passage="A village depends on monsoon rainfall for farming throughout the year.",
                questions=[
                    GeneratedQuestion(
                        question_type=QuestionType.CASE_STUDY,
                        text="Read the passage and answer the questions.",
                        sub_questions=["What season is important for the village?"],
                    )
                ],
            )
        ]
    )

    issues = validate_generated_paper(blueprint, paper)

    assert "case_study_sub_question_count" in {issue.code for issue in issues}
