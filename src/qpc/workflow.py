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
        suffix = (
            chr(65 + candidate_index) if candidate_index < 26 else str(candidate_index + 1)
        )
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
