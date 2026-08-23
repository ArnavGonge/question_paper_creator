from qpc.demo_data import default_sections
from qpc.error_reporting import ErrorReport
from qpc.presentation import STEP_COPY, error_report_text, section_header


def test_every_wizard_step_has_concise_teacher_facing_copy():
    assert set(STEP_COPY) == {
        "Upload PDFs",
        "Topics",
        "Paper Details",
        "Question Sections",
        "Generate and Review",
        "Download Word Document",
    }
    assert all(item.title and item.prompt for item in STEP_COPY.values())


def test_section_header_contains_type_count_and_marks():
    assert section_header(default_sections()[0]) == (
        "Section A | Multiple Choice | Answer 4 | 1 mark each | 4 marks"
    )


def test_error_report_text_contains_safe_copy_and_reference():
    report = ErrorReport(
        user_message="The paper could not be generated. Please try again.",
        reference_id="ABC12345",
    )

    assert error_report_text(report) == (
        "The paper could not be generated. Please try again. Reference: ABC12345"
    )
