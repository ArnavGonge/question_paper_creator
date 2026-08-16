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

