from qpc.question_generator import (
    build_question_prompt,
    normalize_generated_paper,
    parse_generated_paper_response,
)
from qpc.schemas import (
    ExerciseType,
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
)
from qpc.topic_extractor import build_topic_prompt, parse_topic_response
from qpc.validators import validate_generated_paper


def test_build_topic_prompt_includes_document_text():
    document = SourceDocument(
        filename="weather.pdf",
        pages=[
            SourcePage(
                page_number=1,
                text="Weather is a state of the Earth's atmosphere.",
            )
        ],
    )

    prompt = build_topic_prompt([document])

    assert "weather.pdf" in prompt
    assert "Weather is a state" in prompt
    assert "Return JSON" in prompt
    assert "English only" in prompt


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
        pages=[
            SourcePage(
                page_number=1,
                text="Humidity is the amount of water vapour in the air.",
            )
        ],
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

    prompt = build_question_prompt(
        [document],
        [topic],
        blueprint,
        exercise_type=ExerciseType.QUESTION_PAPER,
    )

    assert "Humidity" in prompt
    assert "Section A" in prompt
    assert "exactly four options" in prompt
    assert "include an answer for every question" in prompt
    assert "case_study: return exactly one question object" in prompt
    assert "sub_questions as an array of plain strings, not objects" in prompt
    assert "map_diagram: return exactly generate question objects" in prompt
    assert "Paper total: 4 marks" in prompt
    assert '"answer": "Correct answer or model answer"' in prompt


def test_build_skill_sheet_prompt_omits_marks_language():
    document = SourceDocument(
        filename="weather.pdf",
        pages=[SourcePage(page_number=1, text="Clouds form when vapour condenses.")],
    )
    topic = Topic(
        id="clouds",
        document_filename="weather.pdf",
        name="Clouds",
        summary="Cloud formation.",
        source_pages=[1],
    )
    blueprint = PaperBlueprint(
        metadata=PaperMetadata(
            grade="VII",
            subject="Social Science",
            exam_name="Skill Sheet",
            date="17.07.2026",
            duration="Practice",
        ),
        sections=[
            SectionBlueprint(
                label="Section A",
                heading="Short Answer Questions",
                question_type=QuestionType.SHORT,
                questions_to_generate=3,
                questions_to_answer=3,
                marks_per_question=1,
            )
        ],
    )

    prompt = build_question_prompt(
        [document],
        [topic],
        blueprint,
        exercise_type=ExerciseType.SKILL_SHEET,
    )

    assert "Skill sheet" in prompt
    assert "Marks do not apply" in prompt
    assert "Paper total:" not in prompt
    assert "marks_each=" not in prompt


def test_normalize_generated_paper_collapses_case_study_questions_to_subquestions():
    blueprint = PaperBlueprint(
        metadata=PaperMetadata(
            grade="VII",
            subject="Social Science",
            exam_name="First Periodic Assessment 2026-27",
            date="17.07.2026",
            duration="2 Hour",
        ),
        sections=[
            SectionBlueprint(
                label="Section E",
                heading="Case Study Based Questions",
                question_type=QuestionType.CASE_STUDY,
                questions_to_generate=2,
                questions_to_answer=2,
                marks_per_question=1,
            )
        ],
    )
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section E",
                heading="Case Study Based Questions",
                question_type=QuestionType.CASE_STUDY,
                passage="A short passage about weather.",
                questions=[
                    GeneratedQuestion(
                        question_type=QuestionType.CASE_STUDY,
                        text="Why does humidity affect comfort?",
                    ),
                    GeneratedQuestion(
                        question_type=QuestionType.CASE_STUDY,
                        text="Name one instrument used to measure weather.",
                    ),
                ],
            )
        ]
    )

    normalized = normalize_generated_paper(blueprint, paper)

    section = normalized.sections[0]
    assert len(section.questions) == 1
    assert section.questions[0].text == "Read the passage and answer the questions."
    assert section.questions[0].sub_questions == [
        "Why does humidity affect comfort?",
        "Name one instrument used to measure weather.",
    ]


def test_normalize_generated_paper_limits_case_study_subquestions_to_blueprint_count():
    blueprint = PaperBlueprint(
        metadata=PaperMetadata(
            grade="VII",
            subject="Social Science",
            exam_name="First Periodic Assessment 2026-27",
            date="17.07.2026",
            duration="2 Hour",
        ),
        sections=[
            SectionBlueprint(
                label="Section E",
                heading="Case Study Based Questions",
                question_type=QuestionType.CASE_STUDY,
                questions_to_generate=2,
                questions_to_answer=2,
                marks_per_question=1,
            )
        ],
    )
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section E",
                heading="Case Study Based Questions",
                question_type=QuestionType.CASE_STUDY,
                passage="A short passage about weather.",
                questions=[
                    GeneratedQuestion(
                        question_type=QuestionType.CASE_STUDY,
                        text="Question wrapper one.",
                        sub_questions=[
                            "Why does humidity affect comfort?",
                            "Name one instrument used to measure weather.",
                        ],
                    ),
                    GeneratedQuestion(
                        question_type=QuestionType.CASE_STUDY,
                        text="Question wrapper two.",
                        sub_questions=[
                            "What causes rainfall?",
                            "Define temperature.",
                        ],
                    ),
                ],
            )
        ]
    )

    normalized = normalize_generated_paper(blueprint, paper)

    assert normalized.sections[0].questions[0].sub_questions == [
        "Why does humidity affect comfort?",
        "Name one instrument used to measure weather.",
    ]
    assert validate_generated_paper(blueprint, normalized) == []


def test_normalize_case_study_preserves_model_answer():
    blueprint = PaperBlueprint(
        metadata=PaperMetadata(
            grade="VII",
            subject="Social Science",
            exam_name="First Periodic Assessment 2026-27",
            date="17.07.2026",
            duration="2 Hour",
        ),
        sections=[
            SectionBlueprint(
                label="Section E",
                heading="Case Study Based Questions",
                question_type=QuestionType.CASE_STUDY,
                questions_to_generate=1,
                questions_to_answer=1,
                marks_per_question=1,
            )
        ],
    )
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section E",
                heading="Case Study Based Questions",
                question_type=QuestionType.CASE_STUDY,
                passage="A short passage about weather.",
                questions=[
                    GeneratedQuestion(
                        question_type=QuestionType.CASE_STUDY,
                        text="Why does humidity affect comfort?",
                        answer="High humidity slows evaporation from the skin.",
                    ),
                ],
            )
        ]
    )

    normalized = normalize_generated_paper(blueprint, paper)

    assert normalized.sections[0].questions[0].answer == (
        "High humidity slows evaporation from the skin."
    )


def test_normalize_generated_paper_fills_empty_map_diagram_section():
    blueprint = PaperBlueprint(
        metadata=PaperMetadata(
            grade="VII",
            subject="Social Science",
            exam_name="First Periodic Assessment 2026-27",
            date="17.07.2026",
            duration="2 Hour",
        ),
        sections=[
            SectionBlueprint(
                label="Section F",
                heading="Map Based Question",
                question_type=QuestionType.MAP_DIAGRAM,
                questions_to_generate=1,
                questions_to_answer=1,
                marks_per_question=1,
                instruction="Mark the required location on the map.",
            )
        ],
    )
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section F",
                heading="Map Based Question",
                question_type=QuestionType.MAP_DIAGRAM,
                questions=[],
            )
        ]
    )

    normalized = normalize_generated_paper(blueprint, paper)

    assert len(normalized.sections[0].questions) == 1
    assert normalized.sections[0].questions[0].question_type is QuestionType.MAP_DIAGRAM
    assert normalized.sections[0].questions[0].text == "Mark the required location on the map."


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


def test_parse_generated_paper_response_accepts_object_subquestions():
    payload = {
        "sections": [
            {
                "label": "Section E",
                "heading": "Case Study Based Questions",
                "question_type": "case_study",
                "passage": "Deserts may be hot or cold depending on their location.",
                "questions": [
                    {
                        "question_type": "case_study",
                        "text": "Read the passage and answer the questions.",
                        "sub_questions": [
                            "How do deserts differ from nearby regions?",
                            {"text": "What features make this a cold desert?"},
                            {
                                "text": (
                                    "Describe two ways people adapt to harsh "
                                    "climatic conditions."
                                )
                            },
                        ],
                    }
                ],
            }
        ]
    }

    paper = parse_generated_paper_response(payload)

    assert paper.sections[0].questions[0].sub_questions == [
        "How do deserts differ from nearby regions?",
        "What features make this a cold desert?",
        "Describe two ways people adapt to harsh climatic conditions.",
    ]
