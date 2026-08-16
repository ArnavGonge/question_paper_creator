### Task 8: Streamlit App Workflow

**Files:**
- Create: `app.py`
- Create: `tests/test_app_config.py`

**Interfaces:**
- Consumes: all modules from earlier tasks.
- Produces: `load_secret(name: str, default: str = "") -> str`.
- Produces: hosted Streamlit UI with password, upload, topics, paper config, generation, review, and DOCX download.

- [ ] **Step 1: Write config test**

`tests/test_app_config.py`:

```python
from app import load_secret


def test_load_secret_returns_default_for_missing_value(monkeypatch):
    class EmptySecrets(dict):
        def get(self, key, default=None):
            return default

    monkeypatch.setattr("streamlit.secrets", EmptySecrets())

    assert load_secret("MISSING", "fallback") == "fallback"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
PYTHONPATH=src pytest tests/test_app_config.py -v
```

Expected: FAIL because `app.py` does not exist.

- [ ] **Step 3: Implement Streamlit app**

`app.py`:

```python
from __future__ import annotations

import os

import streamlit as st

from qpc.demo_data import default_blueprint
from qpc.docx_exporter import render_docx
from qpc.pdf_extractor import extract_pdf_bytes
from qpc.question_generator import generate_questions_with_ai
from qpc.schemas import GeneratedPaper, PaperBlueprint, QuestionType, SectionBlueprint, Topic
from qpc.topic_extractor import extract_topics_with_ai
from qpc.validators import validate_blueprint, validate_generated_paper


def load_secret(name: str, default: str = "") -> str:
    return str(st.secrets.get(name, os.environ.get(name, default)))


def ensure_state() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "documents" not in st.session_state:
        st.session_state.documents = []
    if "topics" not in st.session_state:
        st.session_state.topics = []
    if "blueprint" not in st.session_state:
        st.session_state.blueprint = default_blueprint()
    if "paper" not in st.session_state:
        st.session_state.paper = None


def password_gate() -> bool:
    if st.session_state.authenticated:
        return True
    st.title("Question Paper Creator")
    password = st.text_input("Password", type="password")
    if st.button("Enter"):
        if password and password == load_secret("APP_PASSWORD"):
            st.session_state.authenticated = True
            st.rerun()
        st.error("Incorrect password.")
    return False


def upload_step() -> None:
    st.header("1. Upload chapter PDFs")
    files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)
    if st.button("Extract text", disabled=not files):
        st.session_state.documents = [extract_pdf_bytes(file.name, file.getvalue()) for file in files]
        st.session_state.topics = []
        st.session_state.paper = None
    for document in st.session_state.documents:
        st.write(f"{document.filename}: {len(document.pages)} pages")


def topic_step() -> None:
    st.header("2. Select topics")
    api_key = load_secret("OPENAI_API_KEY")
    model = load_secret("OPENAI_MODEL", "gpt-4.1-mini")
    if st.button("Extract topics with AI", disabled=not st.session_state.documents):
        topic_set = extract_topics_with_ai(st.session_state.documents, api_key=api_key, model=model)
        st.session_state.topics = topic_set.topics

    updated_topics: list[Topic] = []
    for topic in st.session_state.topics:
        selected = st.checkbox(
            f"{topic.name} — {topic.summary}",
            value=topic.selected,
            key=f"topic_{topic.id}",
        )
        updated_topics.append(topic.model_copy(update={"selected": selected}))
    st.session_state.topics = updated_topics


def configure_step() -> None:
    st.header("3. Configure paper")
    blueprint: PaperBlueprint = st.session_state.blueprint
    metadata = blueprint.metadata

    metadata.grade = st.text_input("Grade", metadata.grade)
    metadata.subject = st.text_input("Subject", metadata.subject)
    metadata.exam_name = st.text_input("Exam name", metadata.exam_name)
    metadata.date = st.text_input("Date", metadata.date)
    metadata.duration = st.text_input("Time", metadata.duration)
    metadata.max_marks = st.number_input("Maximum marks", min_value=1, value=metadata.max_marks, step=1)

    st.subheader("Sections")
    sections: list[SectionBlueprint] = []
    for index, section in enumerate(blueprint.sections):
        with st.expander(section.label, expanded=True):
            label = st.text_input("Section label", section.label, key=f"label_{index}")
            heading = st.text_input("Heading", section.heading, key=f"heading_{index}")
            question_type = st.selectbox(
                "Question type",
                list(QuestionType),
                index=list(QuestionType).index(section.question_type),
                format_func=lambda value: value.value.replace("_", " ").title(),
                key=f"type_{index}",
            )
            generate = st.number_input("Questions to generate", min_value=1, value=section.questions_to_generate, key=f"gen_{index}")
            answer = st.number_input("Questions to answer", min_value=1, max_value=generate, value=min(section.questions_to_answer, generate), key=f"ans_{index}")
            marks = st.number_input("Marks per question", min_value=1, value=section.marks_per_question, key=f"marks_{index}")
            instruction = st.text_input("Optional instruction", section.instruction, key=f"instruction_{index}")
            sections.append(
                SectionBlueprint(
                    label=label,
                    heading=heading,
                    question_type=question_type,
                    questions_to_generate=generate,
                    questions_to_answer=answer,
                    marks_per_question=marks,
                    instruction=instruction,
                )
            )

    if st.button("Add section"):
        sections.append(
            SectionBlueprint(
                label=f"Section {chr(65 + len(sections))}",
                heading="Short Answer Based Questions",
                question_type=QuestionType.SHORT,
                questions_to_generate=3,
                questions_to_answer=3,
                marks_per_question=2,
            )
        )

    st.session_state.blueprint = PaperBlueprint(metadata=metadata, sections=sections)
    issues = validate_blueprint(st.session_state.blueprint)
    st.write(f"Calculated marks: {st.session_state.blueprint.total_marks()}")
    for issue in issues:
        st.warning(issue.message)


def generation_step() -> None:
    st.header("4. Generate and review")
    selected_topics = [topic for topic in st.session_state.topics if topic.selected]
    api_key = load_secret("OPENAI_API_KEY")
    model = load_secret("OPENAI_MODEL", "gpt-4.1-mini")
    disabled = not st.session_state.documents or not selected_topics or bool(validate_blueprint(st.session_state.blueprint))
    if st.button("Generate paper", disabled=disabled):
        paper = generate_questions_with_ai(
            st.session_state.documents,
            selected_topics,
            st.session_state.blueprint,
            api_key=api_key,
            model=model,
        )
        issues = validate_generated_paper(st.session_state.blueprint, paper)
        if issues:
            for issue in issues:
                st.error(issue.message)
        else:
            st.session_state.paper = paper

    paper: GeneratedPaper | None = st.session_state.paper
    if paper is None:
        return

    for section_index, section in enumerate(paper.sections):
        st.subheader(section.label)
        if section.passage:
            section.passage = st.text_area("Passage", section.passage, key=f"passage_{section_index}")
        for question_index, question in enumerate(section.questions):
            question.text = st.text_area(
                f"Question {question_index + 1}",
                question.text,
                key=f"question_{section_index}_{question_index}",
            )
            if question.question_type is QuestionType.MCQ:
                question.options = [
                    st.text_input(
                        f"Option {option_index + 1}",
                        option,
                        key=f"option_{section_index}_{question_index}_{option_index}",
                    )
                    for option_index, option in enumerate(question.options)
                ]


def download_step() -> None:
    st.header("5. Download")
    if st.session_state.paper is None:
        st.info("Generate a valid paper before downloading.")
        return
    data = render_docx(st.session_state.blueprint, st.session_state.paper)
    st.download_button(
        "Download Word document",
        data=data,
        file_name="question-paper.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def main() -> None:
    st.set_page_config(page_title="Question Paper Creator", layout="wide")
    ensure_state()
    if not password_gate():
        return
    upload_step()
    topic_step()
    configure_step()
    generation_step()
    download_step()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run config test**

```bash
PYTHONPATH=src pytest tests/test_app_config.py -v
```

Expected: PASS.

- [ ] **Step 5: Run full test suite**

```bash
PYTHONPATH=src pytest -v
```

Expected: PASS.

- [ ] **Step 6: Run app locally**

Run:

```bash
PYTHONPATH=src streamlit run app.py
```

Expected: Streamlit starts and shows the password screen.

- [ ] **Step 7: Commit when git exists**

```bash
git add app.py tests/test_app_config.py
git commit -m "feat: add streamlit workflow"
```

---

