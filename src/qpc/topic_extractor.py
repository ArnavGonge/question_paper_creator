import json

from openai import OpenAI

from qpc.schemas import SourceDocument, TopicSet


def build_topic_prompt(documents: list[SourceDocument]) -> str:
    document_blocks = "\n\n".join(
        f"DOCUMENT: {document.filename}\n{document.combined_text()[:16000]}"
        for document in documents
    )
    return f"""
You extract question-paper topics from textbook chapter text.

Rules:
- English only.
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


def extract_topics_with_ai(
    documents: list[SourceDocument], api_key: str, model: str
) -> TopicSet:
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=build_topic_prompt(documents),
        text={"format": {"type": "json_object"}},
    )
    payload = json.loads(response.output_text)
    return parse_topic_response(payload)
