import json

from openai import OpenAI

from qpc.schemas import (
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperBlueprint,
    QuestionType,
    SourceDocument,
    Topic,
)


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
        f"DOCUMENT: {document.filename}\n{document.combined_text()[:16000]}"
        for document in documents
    )
    return f"""
You generate an English school question paper from selected textbook topics.

Rules:
- Use only the selected topics and source material below.
- Do not generate an answer key.
- Do not include unsupported topics.
- Each section must use exactly its configured question type.
- MCQ questions must include exactly four options.
- case_study: return exactly one question object in the section; put the case passage in section.passage; put exactly generate sub-questions in that one question object's sub_questions as an array of plain strings, not objects.
- match: return exactly one question object in the section; put exactly generate pairs in that one question object's pairs.
- map_diagram: return exactly generate question objects with prompt text only; do not ask for an embedded image.
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


def normalize_generated_paper(
    blueprint: PaperBlueprint,
    paper: GeneratedPaper,
) -> GeneratedPaper:
    sections_by_label = {section.label: section for section in paper.sections}
    normalized_sections: list[GeneratedSection] = []

    for blueprint_section in blueprint.sections:
        section = sections_by_label.get(blueprint_section.label)
        if section is None:
            continue
        if blueprint_section.question_type is QuestionType.CASE_STUDY:
            section = _normalize_case_study_section(
                section,
                expected_sub_question_count=blueprint_section.questions_to_generate,
            )
        if blueprint_section.question_type is QuestionType.MAP_DIAGRAM:
            section = _normalize_map_diagram_section(section, blueprint_section)
        normalized_sections.append(section)

    extra_sections = [
        section
        for section in paper.sections
        if section.label not in {blueprint_section.label for blueprint_section in blueprint.sections}
    ]
    return GeneratedPaper(sections=[*normalized_sections, *extra_sections])


def _normalize_case_study_section(
    section: GeneratedSection,
    *,
    expected_sub_question_count: int,
) -> GeneratedSection:
    sub_questions: list[str] = []
    for question in section.questions:
        if question.sub_questions:
            sub_questions.extend(question.sub_questions)
        elif question.text.strip():
            sub_questions.append(question.text.strip())

    if not sub_questions:
        return section

    sub_questions = sub_questions[:expected_sub_question_count]
    return section.model_copy(
        update={
            "questions": [
                GeneratedQuestion(
                    question_type=QuestionType.CASE_STUDY,
                    text="Read the passage and answer the questions.",
                    sub_questions=sub_questions,
                )
            ]
        },
        deep=True,
    )


def _normalize_map_diagram_section(
    section: GeneratedSection,
    blueprint_section,
) -> GeneratedSection:
    if section.questions:
        return section

    prompt = blueprint_section.instruction.strip() or blueprint_section.heading.strip()
    return section.model_copy(
        update={
            "questions": [
                GeneratedQuestion(
                    question_type=QuestionType.MAP_DIAGRAM,
                    text=prompt,
                )
            ]
        },
        deep=True,
    )


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
    return normalize_generated_paper(blueprint, parse_generated_paper_response(payload))
