from qpc.schemas import PaperBlueprint, PaperMetadata, QuestionType, SectionBlueprint


def default_metadata() -> PaperMetadata:
    return PaperMetadata(
        grade="VII",
        subject="Social Science",
        exam_name="First Periodic Assessment 2026-27",
        date="17.07.2026",
        max_marks=4,
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
    ]


def default_blueprint() -> PaperBlueprint:
    return PaperBlueprint(metadata=default_metadata(), sections=default_sections())
