from datetime import date

import pytest

from app import (
    MAX_UPLOAD_PDFS,
    WIZARD_STEPS,
    build_generation_inputs_snapshot,
    build_generation_issue_diagnostics,
    clamp_step,
    document_upload_summary,
    documents_after_extraction,
    extraction_success_message,
    format_metadata_date,
    load_secret,
    paper_is_stale,
    parse_metadata_date,
    replace_section_in_paper,
    section_blueprint_only,
    should_auto_extract_topics,
    snapshot_documents,
    snapshot_selected_topics,
    step_ready,
    topics_by_document,
    upload_result_summary,
    uploaded_pdf_limit_message,
    validate_export_ready_paper,
    wizard_primary_action,
    wizard_progress,
    wizard_progress_label,
    wizard_sidebar_state,
    wizard_step_label,
)
from qpc.demo_data import default_blueprint
from qpc.schemas import (
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperBlueprint,
    QuestionType,
    SectionBlueprint,
    SourceDocument,
    SourcePage,
    Topic,
)


def test_load_secret_returns_default_for_missing_value(monkeypatch):
    class EmptySecrets(dict):
        def get(self, key, default=None):
            return default

    monkeypatch.setattr("streamlit.secrets", EmptySecrets())

    assert load_secret("MISSING", "fallback") == "fallback"


def test_wizard_steps_are_fixed_for_guided_flow():
    assert WIZARD_STEPS == (
        "Upload PDFs",
        "Topics",
        "Paper Details",
        "Question Sections",
        "Generate and Review",
        "Download Word Document",
    )
    assert wizard_step_label(1) == "Step 2 of 6: Topics"
    assert wizard_progress(2) == 3 / 6
    assert clamp_step(-1) == 0
    assert clamp_step(99) == 5


def test_upload_limit_message_only_warns_above_suggested_limit():
    assert uploaded_pdf_limit_message(MAX_UPLOAD_PDFS) is None
    assert uploaded_pdf_limit_message(MAX_UPLOAD_PDFS + 1) == (
        f"You uploaded {MAX_UPLOAD_PDFS + 1} PDFs. For best results, use "
        f"{MAX_UPLOAD_PDFS} or fewer at a time."
    )


def test_document_upload_summary_counts_documents_and_pages():
    documents = [
        SourceDocument(filename="a.pdf", pages=[SourcePage(page_number=1, text="A")]),
        SourceDocument(
            filename="b.pdf",
            pages=[
                SourcePage(page_number=1, text="B"),
                SourcePage(page_number=2, text="C"),
            ],
        ),
    ]

    assert document_upload_summary(documents) == (2, 3)


def test_extraction_success_message_is_single_concise_result():
    assert extraction_success_message(2, 18) == "Text extracted from 2 PDFs, 18 pages."
    assert extraction_success_message(1, 1) == "Text extracted from 1 PDF, 1 page."


def test_upload_result_summary_handles_partial_success():
    assert upload_result_summary(2, 1) == "2 PDFs ready; 1 PDF needs attention."


def test_upload_result_summary_handles_complete_failure():
    assert upload_result_summary(0, 2) == (
        "No new PDFs were extracted; your previous sources are still available."
    )


def test_metadata_date_round_trips_between_picker_and_header_format():
    parsed = parse_metadata_date("17.07.2026")

    assert parsed == date(2026, 7, 17)
    assert format_metadata_date(parsed) == "17.07.2026"


def test_metadata_date_parser_rejects_unparseable_existing_value():
    with pytest.raises(ValueError):
        parse_metadata_date("not-a-date")


def test_documents_after_extraction_keeps_working_documents_after_total_failure():
    previous = [
        SourceDocument(filename="old.pdf", pages=[SourcePage(page_number=1, text="Old")])
    ]

    assert documents_after_extraction(previous, []) == previous


def test_wizard_sidebar_state_distinguishes_available_from_completed():
    assert wizard_sidebar_state(step_index=1, current_step=0, ready=True) == "Next"
    assert wizard_sidebar_state(step_index=2, current_step=4, ready=True) == "Done"
    assert wizard_sidebar_state(step_index=4, current_step=4, ready=True) == "Current"
    assert wizard_sidebar_state(step_index=5, current_step=3, ready=False) == "Locked"


def test_wizard_primary_action_uses_short_teacher_facing_labels():
    assert wizard_primary_action(0) == "Extract text"
    assert wizard_primary_action(1) == "Choose topics"
    assert wizard_primary_action(4) == "Generate paper"


def test_wizard_progress_label_is_secondary_and_short():
    assert wizard_progress_label(0) == "Step 1 of 6"
    assert wizard_progress_label(5) == "Step 6 of 6"


def test_topics_auto_extract_only_after_documents_before_topics_exist():
    assert should_auto_extract_topics(documents=[object()], topics=[]) is True
    assert should_auto_extract_topics(documents=[], topics=[]) is False
    assert should_auto_extract_topics(documents=[object()], topics=[object()]) is False


def test_topics_are_grouped_by_source_document_in_input_order():
    topics = [
        Topic(
            id="weather",
            document_filename="climate.pdf",
            name="Weather",
            summary="Daily atmospheric conditions",
        ),
        Topic(
            id="rivers",
            document_filename="geography.pdf",
            name="Rivers",
            summary="River systems",
        ),
        Topic(
            id="rainfall",
            document_filename="climate.pdf",
            name="Rainfall",
            summary="Forms of precipitation",
        ),
    ]

    grouped = topics_by_document(topics)

    assert list(grouped) == ["climate.pdf", "geography.pdf"]
    assert [topic.id for topic in grouped["climate.pdf"]] == ["weather", "rainfall"]


def test_step_ready_guides_incomplete_flow():
    blueprint = default_blueprint()

    ready, message = step_ready(
        1,
        documents=[],
        topics=[],
        blueprint=blueprint,
        paper=None,
    )

    assert ready is False
    assert message == "Upload and extract at least one PDF first."


def test_step_ready_requires_selected_topics_before_paper_details():
    blueprint = default_blueprint()
    topics = [
        Topic(
            id="weather",
            document_filename="weather.pdf",
            name="Weather",
            summary="Weather systems",
            source_pages=[1],
            selected=False,
        )
    ]
    documents = [
        SourceDocument(filename="weather.pdf", pages=[SourcePage(page_number=1, text="A")])
    ]

    ready, message = step_ready(
        2,
        documents=documents,
        topics=topics,
        blueprint=blueprint,
        paper=None,
    )

    assert ready is False
    assert message == "Select at least one topic first."


def test_step_ready_allows_generation_when_inputs_and_blueprint_are_ready():
    blueprint = default_blueprint()
    topics = [
        Topic(
            id="weather",
            document_filename="weather.pdf",
            name="Weather",
            summary="Weather systems",
            source_pages=[1],
            selected=True,
        )
    ]
    documents = [
        SourceDocument(filename="weather.pdf", pages=[SourcePage(page_number=1, text="A")])
    ]

    ready, message = step_ready(
        4,
        documents=documents,
        topics=topics,
        blueprint=blueprint,
        paper=None,
    )

    assert ready is True
    assert message == ""


def test_step_ready_requires_generated_paper_before_download():
    blueprint = default_blueprint()
    topics = [
        Topic(
            id="weather",
            document_filename="weather.pdf",
            name="Weather",
            summary="Weather systems",
            source_pages=[1],
            selected=True,
        )
    ]
    documents = [
        SourceDocument(filename="weather.pdf", pages=[SourcePage(page_number=1, text="A")])
    ]

    ready, message = step_ready(
        5,
        documents=documents,
        topics=topics,
        blueprint=blueprint,
        paper=None,
    )

    assert ready is False
    assert message == "Generate a valid question paper first."


def test_paper_is_stale_when_selected_topics_change():
    original_topics = [
        Topic(
            id="monsoon",
            document_filename="weather.pdf",
            name="Monsoon",
            summary="Seasonal rainfall pattern",
            source_pages=[1, 2],
            selected=True,
        )
    ]
    updated_topics = [
        original_topics[0].model_copy(update={"selected": False}),
    ]

    assert paper_is_stale(
        previous_documents=snapshot_documents([]),
        new_documents=snapshot_documents([]),
        previous_topics=snapshot_selected_topics(original_topics),
        new_topics=snapshot_selected_topics(updated_topics),
        previous_blueprint=default_blueprint().model_dump(mode="json"),
        new_blueprint=default_blueprint().model_dump(mode="json"),
    )


def test_paper_is_stale_when_blueprint_changes():
    blueprint = default_blueprint()
    updated_blueprint = blueprint.model_copy(
        update={"metadata": blueprint.metadata.model_copy(update={"exam_name": "Updated"})}
    )

    assert paper_is_stale(
        previous_documents=snapshot_documents([]),
        new_documents=snapshot_documents([]),
        previous_topics=[],
        new_topics=[],
        previous_blueprint=blueprint.model_dump(mode="json"),
        new_blueprint=updated_blueprint.model_dump(mode="json"),
    )


def test_validate_export_ready_paper_reports_invalid_manual_edits():
    defaults = default_blueprint()
    blueprint = PaperBlueprint(
        metadata=defaults.metadata,
        sections=[
            SectionBlueprint(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions_to_generate=1,
                questions_to_answer=1,
                marks_per_question=1,
            )
        ],
    )
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions=[
                    GeneratedQuestion(
                        question_type=QuestionType.MCQ,
                        text="Short?",
                        options=["A", "B", "C"],
                    )
                ],
            )
        ]
    )

    issues = validate_export_ready_paper(blueprint, paper)

    assert {issue.code for issue in issues} == {"question_too_short", "mcq_option_count"}


def test_build_generation_issue_diagnostics_includes_counts_and_section_json():
    defaults = default_blueprint()
    blueprint = PaperBlueprint(
        metadata=defaults.metadata,
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
                passage="A passage about weather.",
                questions=[
                    GeneratedQuestion(
                        question_type=QuestionType.CASE_STUDY,
                        text="Read the passage and answer the questions.",
                        sub_questions=["Why does it rain?"],
                    )
                ],
            )
        ]
    )

    diagnostics = build_generation_issue_diagnostics(
        validate_export_ready_paper(blueprint, paper),
        blueprint,
        paper,
    )

    assert diagnostics == [
        {
            "code": "case_study_sub_question_count",
            "message": "Section E should contain 2 case-study sub-questions.",
            "section": "Section E",
            "expected": 2,
            "actual": [1],
            "blueprint_section": blueprint.sections[0].model_dump(mode="json"),
            "generated_section": paper.sections[0].model_dump(mode="json"),
        }
    ]


def test_build_generation_issue_diagnostics_reports_all_case_study_counts():
    defaults = default_blueprint()
    blueprint = PaperBlueprint(
        metadata=defaults.metadata,
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
                passage="A passage about weather.",
                questions=[
                    GeneratedQuestion(
                        question_type=QuestionType.CASE_STUDY,
                        text="First case-study wrapper.",
                        sub_questions=["What is rainfall?", "What is humidity?"],
                    ),
                    GeneratedQuestion(
                        question_type=QuestionType.CASE_STUDY,
                        text="Second case-study wrapper.",
                        sub_questions=["What is temperature?"],
                    ),
                ],
            )
        ]
    )

    diagnostics = build_generation_issue_diagnostics(
        validate_export_ready_paper(blueprint, paper),
        blueprint,
        paper,
    )

    case_study_diagnostic = next(
        item for item in diagnostics if item["code"] == "case_study_sub_question_count"
    )
    assert case_study_diagnostic["actual"] == [2, 1]


def test_section_blueprint_only_keeps_metadata_and_requested_section():
    blueprint = default_blueprint()

    single = section_blueprint_only(blueprint, 0)

    assert single.metadata == blueprint.metadata
    assert len(single.sections) == 1
    assert single.sections[0] == blueprint.sections[0]


def test_replace_section_in_paper_replaces_only_target_section():
    original = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions=[
                    GeneratedQuestion(
                        question_type=QuestionType.MCQ,
                        text="Original A",
                        options=["A", "B", "C", "D"],
                    )
                ],
            ),
            GeneratedSection(
                label="Section B",
                heading="Short Answer Based Questions",
                question_type=QuestionType.SHORT,
                questions=[
                    GeneratedQuestion(
                        question_type=QuestionType.SHORT,
                        text="Original B",
                    )
                ],
            ),
        ]
    )
    replacement = GeneratedSection(
        label="Section B",
        heading="Short Answer Based Questions",
        question_type=QuestionType.SHORT,
        questions=[
            GeneratedQuestion(
                question_type=QuestionType.SHORT,
                text="Replacement B",
            )
        ],
    )

    updated = replace_section_in_paper(original, 1, replacement)

    assert updated.sections[0].questions[0].text == "Original A"
    assert updated.sections[1].questions[0].text == "Replacement B"


def test_build_generation_inputs_snapshot_uses_selected_topics_and_blueprint_json():
    blueprint = default_blueprint()
    topics = [
        Topic(
            id="selected-topic",
            document_filename="weather.pdf",
            name="Weather",
            summary="Selected topic",
            source_pages=[1],
            selected=True,
        ),
        Topic(
            id="ignored-topic",
            document_filename="weather.pdf",
            name="Ignored",
            summary="Not selected",
            source_pages=[2],
            selected=False,
        ),
    ]

    snapshot = build_generation_inputs_snapshot(
        documents=[],
        topics=topics,
        blueprint=blueprint,
    )

    assert [topic["id"] for topic in snapshot["topics"]] == ["selected-topic"]
    assert snapshot["blueprint"] == blueprint.model_dump(mode="json")
