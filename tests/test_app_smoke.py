from pathlib import Path

from streamlit.testing.v1 import AppTest

from qpc.demo_data import default_blueprint
from qpc.schemas import (
    ExerciseType,
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    QuestionType,
    SourceDocument,
    SourcePage,
    Topic,
)

APP_FILE = Path(__file__).parents[1] / "app.py"


def authenticated_app(step: int) -> AppTest:
    app = AppTest.from_file(APP_FILE, default_timeout=10)
    app.session_state["authenticated"] = True
    app.session_state["wizard_step"] = step
    return app.run()


def test_upload_step_renders_without_an_exception():
    app = authenticated_app(1)

    assert not app.exception
    assert len(app.file_uploader) == 1
    assert not any(button.label == "Extract text" for button in app.button)


def test_next_from_upload_extracts_text_and_advances_to_topics(monkeypatch):
    def fake_extract_pdf_bytes(filename: str, content: bytes) -> SourceDocument:
        assert filename == "chapter.pdf"
        assert content == b"pdf-bytes"
        return SourceDocument(
            filename=filename,
            pages=[SourcePage(page_number=1, text="Chapter text")],
        )

    monkeypatch.setattr("qpc.pdf_extractor.extract_pdf_bytes", fake_extract_pdf_bytes)
    app = authenticated_app(1)
    app.file_uploader[0].set_value(
        ("chapter.pdf", b"pdf-bytes", "application/pdf")
    )
    app = app.run()
    next_button = next(
        button for button in app.button if button.label == "Next: Choose topics"
    )

    assert next_button.disabled is False

    next_button.click()
    app = app.run()

    assert not app.exception
    assert app.session_state["wizard_step"] == 2
    assert [document.filename for document in app.session_state["documents"]] == [
        "chapter.pdf"
    ]
    assert app.session_state["upload_result_message"] == "1 PDF ready."


def test_section_editor_renders_complete_controls_for_default_section():
    app = authenticated_app(4)

    assert not app.exception
    labels = [button.label for button in app.button]
    assert "Move up" in labels
    assert "Move down" in labels
    assert "Delete" in labels
    assert "Add section" in labels
    assert labels.index("Add section") > labels.index("Delete")
    delete_button = next(button for button in app.button if button.label == "Delete")
    assert delete_button.disabled is True
    number_input_labels = [field.label for field in app.number_input]
    assert "Total questions" in number_input_labels
    assert "Compulsory questions" in number_input_labels
    assert "Questions to generate" not in number_input_labels
    assert "Questions to answer" not in number_input_labels
    compulsory_input = next(
        field for field in app.number_input if field.label == "Compulsory questions"
    )
    assert compulsory_input.max == 4
    assert [metric.label for metric in app.metric] == ["Section total", "Paper total"]


def test_section_header_updates_when_label_field_changes():
    app = authenticated_app(4)

    app.text_input[0].set_value("Section Z")
    app = app.run()

    assert not app.exception
    assert [expander.label for expander in app.expander] == ["Section Z"]
    assert app.session_state["blueprint"].sections[0].label == "Section Z"


def test_paper_details_does_not_show_marks_total():
    app = authenticated_app(3)

    assert not app.exception
    assert not any(field.label == "Maximum marks" for field in app.number_input)
    assert not any(metric.label == "Calculated marks" for metric in app.metric)


def test_topics_step_does_not_show_selected_topic_count():
    app = AppTest.from_file(APP_FILE, default_timeout=10)
    app.session_state["authenticated"] = True
    app.session_state["wizard_step"] = 2
    app.session_state["documents"] = [
        SourceDocument(
            filename="weather.pdf",
            pages=[SourcePage(page_number=1, text="Weather systems")],
        )
    ]
    app.session_state["topics"] = [
        Topic(
            id="weather",
            document_filename="weather.pdf",
            name="Weather",
            summary="Weather systems",
            selected=True,
        )
    ]
    app = app.run()

    assert not app.exception
    assert not any(metric.label == "Selected topics" for metric in app.metric)


def test_exercise_type_step_defaults_to_question_paper():
    app = authenticated_app(0)

    assert not app.exception
    assert len(app.radio) == 1
    assert app.radio[0].label == "Exercise type"
    assert app.radio[0].value == ExerciseType.QUESTION_PAPER


def test_skill_sheet_section_editor_hides_marks_controls():
    app = AppTest.from_file(APP_FILE, default_timeout=10)
    app.session_state["authenticated"] = True
    app.session_state["wizard_step"] = 4
    app.session_state["exercise_type"] = ExerciseType.SKILL_SHEET
    app = app.run()

    assert not app.exception
    number_input_labels = [field.label for field in app.number_input]
    assert "Total questions" in number_input_labels
    assert "Compulsory questions" not in number_input_labels
    assert "Marks per question" not in number_input_labels
    assert not any(metric.label == "Section total" for metric in app.metric)
    assert not any(metric.label == "Paper total" for metric in app.metric)


def test_generation_review_includes_editable_answer_fields():
    app = AppTest.from_file(APP_FILE, default_timeout=10)
    app.session_state["authenticated"] = True
    app.session_state["wizard_step"] = 5
    app.session_state["documents"] = [
        SourceDocument(filename="weather.pdf", pages=[SourcePage(page_number=1, text="A")])
    ]
    app.session_state["topics"] = [
        Topic(
            id="humidity",
            document_filename="weather.pdf",
            name="Humidity",
            summary="Water vapour in air",
            selected=True,
        )
    ]
    app.session_state["blueprint"] = default_blueprint()
    app.session_state["paper"] = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions=[
                    GeneratedQuestion(
                        question_type=QuestionType.MCQ,
                        text="What does humidity measure?",
                        options=["Rain", "Water vapour", "Wind", "Clouds"],
                        answer="Water vapour",
                    )
                ],
            )
        ]
    )
    app = app.run()

    assert not app.exception
    assert any(field.label == "Answer 1" for field in app.text_area)
