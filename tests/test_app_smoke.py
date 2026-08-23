from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_FILE = Path(__file__).parents[1] / "app.py"


def authenticated_app(step: int) -> AppTest:
    app = AppTest.from_file(APP_FILE, default_timeout=10)
    app.session_state["authenticated"] = True
    app.session_state["wizard_step"] = step
    return app.run()


def test_upload_step_renders_without_an_exception():
    app = authenticated_app(0)

    assert not app.exception
    assert len(app.file_uploader) == 1
    assert any(button.label == "Extract text" for button in app.button)


def test_section_editor_renders_complete_controls_for_default_section():
    app = authenticated_app(3)

    assert not app.exception
    labels = [button.label for button in app.button]
    assert "Move up" in labels
    assert "Move down" in labels
    assert "Delete" in labels
    assert "Add section" in labels
    delete_button = next(button for button in app.button if button.label == "Delete")
    assert delete_button.disabled is True


def test_paper_details_shows_only_the_calculated_total():
    app = authenticated_app(2)

    assert not app.exception
    assert not any(field.label == "Maximum marks" for field in app.number_input)
    assert any(metric.label == "Calculated marks" for metric in app.metric)
