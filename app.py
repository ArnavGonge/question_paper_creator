from __future__ import annotations

import os
from datetime import UTC, date, datetime
from typing import Any

import streamlit as st

from qpc.demo_data import default_blueprint
from qpc.docx_exporter import render_docx
from qpc.pdf_extractor import extract_pdf_bytes
from qpc.question_generator import generate_questions_with_ai
from qpc.schemas import (
    GeneratedPaper,
    GeneratedSection,
    PaperBlueprint,
    QuestionType,
    SectionBlueprint,
    Topic,
)
from qpc.topic_extractor import extract_topics_with_ai
from qpc.validators import (
    ValidationIssue,
    expected_generated_question_count,
    validate_blueprint,
    validate_generated_paper,
)


def load_secret(name: str, default: str = "") -> str:
    return str(st.secrets.get(name, os.environ.get(name, default)))


WIZARD_STEPS = (
    "Upload PDFs",
    "Topics",
    "Paper Details",
    "Question Sections",
    "Generate and Review",
    "Download Word Document",
)
MAX_UPLOAD_PDFS = 5
PRIMARY_ACTIONS = (
    "Extract text",
    "Choose topics",
    "Save details",
    "Build sections",
    "Generate paper",
    "Download Word document",
)


def clamp_step(step: int) -> int:
    return max(0, min(step, len(WIZARD_STEPS) - 1))


def wizard_progress(step: int) -> float:
    return (clamp_step(step) + 1) / len(WIZARD_STEPS)


def wizard_step_label(step: int) -> str:
    current = clamp_step(step)
    return f"Step {current + 1} of {len(WIZARD_STEPS)}: {WIZARD_STEPS[current]}"


def wizard_progress_label(step: int) -> str:
    current = clamp_step(step)
    return f"Step {current + 1} of {len(WIZARD_STEPS)}"


def wizard_primary_action(step: int) -> str:
    return PRIMARY_ACTIONS[clamp_step(step)]


def uploaded_pdf_limit_message(file_count: int) -> str | None:
    if file_count <= MAX_UPLOAD_PDFS:
        return None
    return (
        f"You uploaded {file_count} PDFs. For best results, use "
        f"{MAX_UPLOAD_PDFS} or fewer at a time."
    )


def document_upload_summary(documents: list) -> tuple[int, int]:
    return len(documents), sum(len(document.pages) for document in documents)


def documents_after_extraction(previous_documents: list, extracted_documents: list) -> list:
    return extracted_documents


def wizard_sidebar_state(step_index: int, current_step: int, ready: bool) -> str:
    if step_index < current_step:
        return "Done"
    if step_index == current_step:
        return "Current"
    if ready:
        return "Next"
    return "Locked"


def selected_topic_count(topics: list[Topic]) -> int:
    return len([topic for topic in topics if topic.selected])


def should_auto_extract_topics(documents: list, topics: list) -> bool:
    return bool(documents) and not topics


def step_ready(
    step: int,
    *,
    documents: list,
    topics: list[Topic],
    blueprint: PaperBlueprint,
    paper: GeneratedPaper | None,
) -> tuple[bool, str]:
    current = clamp_step(step)
    if current >= 1 and not documents:
        return False, "Upload and extract at least one PDF first."
    if current >= 2 and not topics:
        return False, "Find topics from the PDFs first."
    if current >= 2 and selected_topic_count(topics) == 0:
        return False, "Select at least one topic first."
    if current >= 4 and validate_blueprint(blueprint):
        return False, "Fix the paper details and section warnings first."
    if current >= 5 and paper is None:
        return False, "Generate a valid question paper first."
    return True, ""


def snapshot_documents(documents: list) -> list[dict]:
    return [
        {
            "filename": document.filename,
            "pages": [
                {"page_number": page.page_number, "text": page.text}
                for page in document.pages
            ],
        }
        for document in documents
    ]


def snapshot_selected_topics(topics: list[Topic]) -> list[dict]:
    return [
        topic.model_dump(mode="json")
        for topic in topics
        if topic.selected
    ]


def build_generation_inputs_snapshot(
    *,
    documents: list,
    topics: list[Topic],
    blueprint: PaperBlueprint,
) -> dict:
    return {
        "documents": snapshot_documents(documents),
        "topics": snapshot_selected_topics(topics),
        "blueprint": blueprint.model_dump(mode="json"),
    }


def section_blueprint_only(
    blueprint: PaperBlueprint, section_index: int
) -> PaperBlueprint:
    return PaperBlueprint(
        metadata=blueprint.metadata.model_copy(deep=True),
        sections=[blueprint.sections[section_index].model_copy(deep=True)],
    )


def replace_section_in_paper(
    paper: GeneratedPaper,
    section_index: int,
    replacement_section: GeneratedSection,
) -> GeneratedPaper:
    sections = [section.model_copy(deep=True) for section in paper.sections]
    sections[section_index] = replacement_section.model_copy(deep=True)
    return GeneratedPaper(sections=sections)


def paper_is_stale(
    *,
    previous_documents: list[dict],
    new_documents: list[dict],
    previous_topics: list[dict],
    new_topics: list[dict],
    previous_blueprint: dict,
    new_blueprint: dict,
) -> bool:
    return (
        previous_documents != new_documents
        or previous_topics != new_topics
        or previous_blueprint != new_blueprint
    )


def validate_export_ready_paper(
    blueprint: PaperBlueprint,
    paper: GeneratedPaper | None,
):
    if paper is None:
        return []
    return validate_generated_paper(blueprint, paper)


def build_generation_issue_diagnostics(
    issues: list[ValidationIssue],
    blueprint: PaperBlueprint,
    paper: GeneratedPaper,
) -> list[dict[str, Any]]:
    blueprint_sections = {section.label: section for section in blueprint.sections}
    generated_sections = {section.label: section for section in paper.sections}

    return [
        {
            "code": issue.code,
            "message": issue.message,
            "section": issue.section_label,
            "expected": _diagnostic_expected_value(
                issue,
                blueprint_sections.get(issue.section_label),
            ),
            "actual": _diagnostic_actual_value(
                issue,
                generated_sections.get(issue.section_label),
            ),
            "blueprint_section": (
                blueprint_sections[issue.section_label].model_dump(mode="json")
                if issue.section_label in blueprint_sections
                else None
            ),
            "generated_section": (
                generated_sections[issue.section_label].model_dump(mode="json")
                if issue.section_label in generated_sections
                else None
            ),
        }
        for issue in issues
    ]


def _diagnostic_expected_value(
    issue: ValidationIssue,
    blueprint_section: SectionBlueprint | None,
) -> Any:
    if blueprint_section is None:
        return "present" if issue.code == "missing_section" else "not generated"
    if issue.code == "question_count_mismatch":
        return expected_generated_question_count(
            blueprint_section.question_type,
            blueprint_section.questions_to_generate,
        )
    if issue.code in {"case_study_sub_question_count", "match_pair_count"}:
        return blueprint_section.questions_to_generate
    if issue.code == "mcq_option_count":
        return 4
    if issue.code == "missing_case_study_passage":
        return "non-empty passage"
    if issue.code == "question_too_short":
        return "at least 8 characters"
    if issue.code in {"section_type_mismatch", "question_type_mismatch"}:
        return blueprint_section.question_type.value
    return ""


def _diagnostic_actual_value(
    issue: ValidationIssue,
    generated_section: GeneratedSection | None,
) -> Any:
    if generated_section is None:
        return "missing"
    if issue.code == "question_count_mismatch":
        return len(generated_section.questions)
    if issue.code == "case_study_sub_question_count":
        return [len(question.sub_questions) for question in generated_section.questions]
    if issue.code == "match_pair_count":
        return [len(question.pairs) for question in generated_section.questions]
    if issue.code == "mcq_option_count":
        return [len(question.options) for question in generated_section.questions]
    if issue.code == "missing_case_study_passage":
        return "empty" if not generated_section.passage.strip() else "present"
    if issue.code == "question_too_short":
        return [len(question.text.strip()) for question in generated_section.questions]
    if issue.code == "section_type_mismatch":
        return generated_section.question_type.value
    if issue.code == "question_type_mismatch":
        return [question.question_type.value for question in generated_section.questions]
    if issue.code == "unexpected_section":
        return "generated"
    return ""


def render_generation_diagnostics(
    issues: list[ValidationIssue],
    blueprint: PaperBlueprint,
    paper: GeneratedPaper,
) -> None:
    diagnostics = build_generation_issue_diagnostics(issues, blueprint, paper)
    if not diagnostics:
        return

    with st.expander("Generation details"):
        st.dataframe(
            [
                {
                    "Section": item["section"],
                    "Code": item["code"],
                    "Expected": item["expected"],
                    "Actual": item["actual"],
                }
                for item in diagnostics
            ],
            hide_index=True,
            use_container_width=True,
        )
        st.caption("Raw section data")
        st.json(
            {
                "issues": [
                    {
                        "section": item["section"],
                        "code": item["code"],
                        "message": item["message"],
                        "expected": item["expected"],
                        "actual": item["actual"],
                    }
                    for item in diagnostics
                ],
                "sections": {
                    item["section"] or "Paper": {
                        "blueprint_section": item["blueprint_section"],
                        "generated_section": item["generated_section"],
                    }
                    for item in diagnostics
                },
            }
        )


def run_generation(
    *,
    documents: list,
    topics: list[Topic],
    blueprint: PaperBlueprint,
    api_key: str,
    model: str,
) -> GeneratedPaper:
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY. Add it to Streamlit secrets or the server environment.")
    return generate_questions_with_ai(
        documents,
        topics,
        blueprint,
        api_key=api_key,
        model=model,
    )


def save_generated_paper(
    *,
    paper: GeneratedPaper,
    documents: list,
    topics: list[Topic],
    blueprint: PaperBlueprint,
) -> None:
    st.session_state.paper = paper
    st.session_state.paper_inputs = build_generation_inputs_snapshot(
        documents=documents,
        topics=topics,
        blueprint=blueprint,
    )


def ensure_state() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 0
    if "documents" not in st.session_state:
        st.session_state.documents = []
    if "topics" not in st.session_state:
        st.session_state.topics = []
    if "blueprint" not in st.session_state:
        st.session_state.blueprint = default_blueprint()
    if "paper" not in st.session_state:
        st.session_state.paper = None
    if "paper_inputs" not in st.session_state:
        st.session_state.paper_inputs = None
    if "upload_errors" not in st.session_state:
        st.session_state.upload_errors = []


def clear_paper_if_blueprint_changed(previous_blueprint: dict) -> None:
    previous_inputs = st.session_state.paper_inputs
    documents_snapshot = snapshot_documents(st.session_state.documents)
    topics_snapshot = snapshot_selected_topics(st.session_state.topics)
    new_blueprint = st.session_state.blueprint.model_dump(mode="json")
    if st.session_state.paper is not None and paper_is_stale(
        previous_documents=(
            previous_inputs["documents"] if previous_inputs is not None else documents_snapshot
        ),
        new_documents=documents_snapshot,
        previous_topics=(
            previous_inputs["topics"] if previous_inputs is not None else topics_snapshot
        ),
        new_topics=topics_snapshot,
        previous_blueprint=(
            previous_inputs["blueprint"] if previous_inputs is not None else previous_blueprint
        ),
        new_blueprint=new_blueprint,
    ):
        st.session_state.paper = None
        st.session_state.paper_inputs = None


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


def metric_text(value: int, label: str) -> str:
    return f"{value} {label}" if value == 1 else f"{value} {label}s"


def parse_metadata_date(value: str) -> date:
    try:
        parts = value.split(".")
        if len(parts) != 3:
            raise ValueError
        day, month, year = (int(part) for part in parts)
        return date(year, month, day)
    except ValueError:
        return datetime.now(UTC).date()


def format_metadata_date(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def extraction_success_message(document_count: int, page_count: int) -> str:
    return (
        f"Text extracted from {metric_text(document_count, 'PDF')}, "
        f"{metric_text(page_count, 'page')}."
    )


def render_wizard_progress() -> None:
    current = clamp_step(st.session_state.wizard_step)
    st.session_state.wizard_step = current

    with st.sidebar:
        st.caption(wizard_progress_label(current))
        st.progress(wizard_progress(current))
        st.header("Steps")
        for index, name in enumerate(WIZARD_STEPS):
            ready, _ = step_ready(
                index,
                documents=st.session_state.documents,
                topics=st.session_state.topics,
                blueprint=st.session_state.blueprint,
                paper=st.session_state.paper,
            )
            state = wizard_sidebar_state(index, current, ready)
            st.write(f"{index + 1}. {name} - {state}")


def navigation_controls() -> None:
    st.divider()
    current = clamp_step(st.session_state.wizard_step)
    back_column, next_column = st.columns(2)
    with back_column:
        if st.button("Back", disabled=current == 0, use_container_width=True):
            st.session_state.wizard_step = clamp_step(current - 1)
            st.rerun()
    with next_column:
        if current == len(WIZARD_STEPS) - 1:
            st.button("Next", disabled=True, use_container_width=True)
            return
        ready, _ = step_ready(
            current + 1,
            documents=st.session_state.documents,
            topics=st.session_state.topics,
            blueprint=st.session_state.blueprint,
            paper=st.session_state.paper,
        )
        label = f"Next: {wizard_primary_action(current + 1)}"
        if st.button(label, disabled=not ready, use_container_width=True):
            st.session_state.wizard_step = clamp_step(current + 1)
            st.rerun()


def upload_step() -> None:
    st.subheader("Add source PDFs")
    st.caption(f"PDF only. Recommended: {MAX_UPLOAD_PDFS} or fewer files.")
    files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)
    if files:
        limit_message = uploaded_pdf_limit_message(len(files))
        if limit_message:
            st.warning(limit_message)
    if st.button("Extract text", disabled=not files, type="primary"):
        previous_documents = snapshot_documents(st.session_state.documents)
        documents = []
        errors = []
        with st.spinner("Reading the PDFs and extracting page text..."):
            for file in files:
                try:
                    documents.append(extract_pdf_bytes(file.name, file.getvalue()))
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{file.name}: {exc}")
        st.session_state.upload_errors = errors
        st.session_state.documents = documents_after_extraction(
            st.session_state.documents,
            documents,
        )
        new_documents = snapshot_documents(st.session_state.documents)
        if previous_documents != new_documents:
            st.session_state.topics = []
            st.session_state.paper = None
            st.session_state.paper_inputs = None
        if errors:
            st.error("Some files could not be read.")
    for error in st.session_state.upload_errors:
        st.error(error)
    if st.session_state.documents:
        doc_count, page_count = document_upload_summary(st.session_state.documents)
        st.success(extraction_success_message(doc_count, page_count))
        with st.expander("Extraction details"):
            for document in st.session_state.documents:
                st.write(f"{document.filename}: {metric_text(len(document.pages), 'page')}")


def topics_step() -> None:
    st.subheader("Topics")
    if not st.session_state.documents:
        st.info("Upload and extract PDFs first.")
        return

    api_key = load_secret("OPENAI_API_KEY")
    model = load_secret("OPENAI_MODEL", "gpt-4.1-mini")
    should_extract = should_auto_extract_topics(
        st.session_state.documents,
        st.session_state.topics,
    )
    refresh_requested = False
    if st.session_state.topics:
        refresh_requested = st.button("Refresh topics")
    if should_extract or refresh_requested:
        try:
            if not api_key:
                raise ValueError(
                    "Missing OPENAI_API_KEY. Add it to Streamlit secrets or the server environment."
                )
            with st.spinner("Finding topics from the uploaded PDFs..."):
                topic_set = extract_topics_with_ai(
                    st.session_state.documents,
                    api_key=api_key,
                    model=model,
                )
            st.session_state.topics = topic_set.topics
            st.session_state.paper = None
            st.session_state.paper_inputs = None
        except Exception as exc:  # noqa: BLE001
            st.error(f"Topic extraction failed: {exc}")

    if not st.session_state.topics:
        st.caption("The checklist will appear here after topics are found.")
        return

    previous_selected_topics = snapshot_selected_topics(st.session_state.topics)
    previous_inputs = st.session_state.paper_inputs
    documents_snapshot = snapshot_documents(st.session_state.documents)
    blueprint_snapshot = st.session_state.blueprint.model_dump(mode="json")
    updated_topics: list[Topic] = []

    st.caption(
        f"Selected {selected_topic_count(st.session_state.topics)} of "
        f"{len(st.session_state.topics)} topics"
    )
    columns = st.columns(2)
    for index, topic in enumerate(st.session_state.topics):
        with columns[index % 2]:
            selected = st.checkbox(
                topic.name,
                value=topic.selected,
                key=f"topic_{topic.id}",
                help=topic.summary,
            )
            updated_topics.append(topic.model_copy(update={"selected": selected}))
    st.session_state.topics = updated_topics
    new_selected_topics = snapshot_selected_topics(st.session_state.topics)
    if st.session_state.paper is not None and paper_is_stale(
        previous_documents=(
            previous_inputs["documents"] if previous_inputs is not None else documents_snapshot
        ),
        new_documents=documents_snapshot,
        previous_topics=(
            previous_inputs["topics"] if previous_inputs is not None else previous_selected_topics
        ),
        new_topics=new_selected_topics,
        previous_blueprint=(
            previous_inputs["blueprint"] if previous_inputs is not None else blueprint_snapshot
        ),
        new_blueprint=blueprint_snapshot,
    ):
        st.session_state.paper = None
        st.session_state.paper_inputs = None


def paper_details_step() -> None:
    st.subheader("Header details")
    blueprint: PaperBlueprint = st.session_state.blueprint
    previous_blueprint = blueprint.model_dump(mode="json")
    metadata = blueprint.metadata

    grade_col, subject_col, exam_col = st.columns(3)
    metadata.grade = grade_col.text_input("Grade", metadata.grade)
    metadata.subject = subject_col.text_input("Subject", metadata.subject)
    metadata.exam_name = exam_col.text_input("Exam name", metadata.exam_name)

    date_col, duration_col, marks_col = st.columns(3)
    selected_date = date_col.date_input(
        "Date",
        value=parse_metadata_date(metadata.date),
        format="DD.MM.YYYY",
    )
    metadata.date = format_metadata_date(selected_date)
    metadata.duration = duration_col.text_input("Time", metadata.duration)
    metadata.max_marks = marks_col.number_input(
        "Maximum marks",
        min_value=1,
        value=metadata.max_marks,
        step=1,
    )

    st.session_state.blueprint = PaperBlueprint(
        metadata=metadata,
        sections=blueprint.sections,
    )
    clear_paper_if_blueprint_changed(previous_blueprint)
    if st.session_state.blueprint.total_marks() != metadata.max_marks:
        st.warning(
            f"Section total is {st.session_state.blueprint.total_marks()} marks; "
            f"paper maximum is {metadata.max_marks}."
        )


def question_sections_step() -> None:
    st.subheader("Build paper sections")
    blueprint: PaperBlueprint = st.session_state.blueprint
    previous_blueprint = blueprint.model_dump(mode="json")

    sections: list[SectionBlueprint] = []
    for index, section in enumerate(blueprint.sections):
        expanded = index == 0
        with st.expander(f"{section.label}: {section.heading}", expanded=expanded):
            label_col, heading_col = st.columns([1, 3])
            label = label_col.text_input(
                "Section label",
                section.label,
                key=f"label_{index}",
            )
            heading = heading_col.text_input(
                "Heading",
                section.heading,
                key=f"heading_{index}",
            )

            type_col, instruction_col = st.columns([1, 2])
            question_type = type_col.selectbox(
                "Question type",
                list(QuestionType),
                index=list(QuestionType).index(section.question_type),
                format_func=lambda value: value.value.replace("_", " ").title(),
                key=f"type_{index}",
            )
            instruction = instruction_col.text_input(
                "Optional instruction",
                section.instruction,
                key=f"instruction_{index}",
            )

            generate_col, answer_col, marks_col = st.columns(3)
            generate = generate_col.number_input(
                "Questions to generate",
                min_value=1,
                value=section.questions_to_generate,
                key=f"gen_{index}",
            )
            answer = answer_col.number_input(
                "Questions to answer",
                min_value=1,
                max_value=generate,
                value=min(section.questions_to_answer, generate),
                key=f"ans_{index}",
            )
            marks = marks_col.number_input(
                "Marks per question",
                min_value=1,
                value=section.marks_per_question,
                key=f"marks_{index}",
            )
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

    st.session_state.blueprint = PaperBlueprint(
        metadata=blueprint.metadata,
        sections=sections,
    )
    clear_paper_if_blueprint_changed(previous_blueprint)
    issues = validate_blueprint(st.session_state.blueprint)
    st.caption(f"Section total: {st.session_state.blueprint.total_marks()} marks")
    for issue in issues:
        st.warning(issue.message)


def generation_step() -> None:
    st.subheader("Generate the paper")
    selected_topics = [topic for topic in st.session_state.topics if topic.selected]
    source_col, topic_col, section_col = st.columns(3)
    source_col.metric("PDFs", len(st.session_state.documents))
    topic_col.metric("Selected topics", len(selected_topics))
    section_col.metric("Sections", len(st.session_state.blueprint.sections))

    api_key = load_secret("OPENAI_API_KEY")
    model = load_secret("OPENAI_MODEL", "gpt-4.1-mini")
    disabled = (
        not st.session_state.documents
        or not selected_topics
        or bool(validate_blueprint(st.session_state.blueprint))
    )
    if disabled:
        ready, message = step_ready(
            4,
            documents=st.session_state.documents,
            topics=st.session_state.topics,
            blueprint=st.session_state.blueprint,
            paper=st.session_state.paper,
        )
        if not ready:
            st.info(message)

    generate_label = "Regenerate paper" if st.session_state.paper is not None else "Generate paper"
    if st.button(generate_label, disabled=disabled, type="primary"):
        try:
            with st.spinner("Generating the question paper. This can take a minute."):
                paper = run_generation(
                    documents=st.session_state.documents,
                    topics=selected_topics,
                    blueprint=st.session_state.blueprint,
                    api_key=api_key,
                    model=model,
                )
            issues = validate_generated_paper(st.session_state.blueprint, paper)
            if issues:
                for issue in issues:
                    st.error(issue.message)
                render_generation_diagnostics(
                    issues,
                    st.session_state.blueprint,
                    paper,
                )
            else:
                save_generated_paper(
                    paper=paper,
                    documents=st.session_state.documents,
                    topics=st.session_state.topics,
                    blueprint=st.session_state.blueprint,
                )
                st.success("Question paper generated.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Paper generation failed: {exc}")

    paper: GeneratedPaper | None = st.session_state.paper
    if paper is None:
        return

    st.subheader("Review")
    for section_index, section in enumerate(paper.sections):
        configured_section = st.session_state.blueprint.sections[section_index]
        with st.expander(
            f"{section.label}: {len(section.questions)} question(s)",
            expanded=section_index == 0,
        ):
            if st.button(
                f"Regenerate {section.label}",
                key=f"regenerate_section_{section_index}",
                disabled=disabled,
            ):
                try:
                    single_section_blueprint = section_blueprint_only(
                        st.session_state.blueprint,
                        section_index,
                    )
                    with st.spinner(f"Regenerating {section.label}..."):
                        regenerated = run_generation(
                            documents=st.session_state.documents,
                            topics=selected_topics,
                            blueprint=single_section_blueprint,
                            api_key=api_key,
                            model=model,
                        )
                    issues = validate_generated_paper(single_section_blueprint, regenerated)
                    if issues:
                        for issue in issues:
                            st.error(issue.message)
                        render_generation_diagnostics(
                            issues,
                            single_section_blueprint,
                            regenerated,
                        )
                    else:
                        updated_paper = replace_section_in_paper(
                            st.session_state.paper,
                            section_index,
                            regenerated.sections[0],
                        )
                        save_generated_paper(
                            paper=updated_paper,
                            documents=st.session_state.documents,
                            topics=st.session_state.topics,
                            blueprint=st.session_state.blueprint,
                        )
                        paper = updated_paper
                        section = paper.sections[section_index]
                        st.success(f"{section.label} regenerated.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"{section.label} regeneration failed: {exc}")

            if section.passage:
                section.passage = st.text_area(
                    "Passage",
                    section.passage,
                    key=f"passage_{section_index}",
                )
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
                            question.options[option_index]
                            if option_index < len(question.options)
                            else "",
                            key=f"option_{section_index}_{question_index}_{option_index}",
                        )
                        for option_index in range(4)
                    ]
                if question.question_type is QuestionType.MATCH:
                    question.pairs = [
                        (
                            st.text_input(
                                f"Pair {pair_index + 1} left",
                                question.pairs[pair_index][0]
                                if pair_index < len(question.pairs)
                                else "",
                                key=f"pair_left_{section_index}_{question_index}_{pair_index}",
                            ),
                            st.text_input(
                                f"Pair {pair_index + 1} right",
                                question.pairs[pair_index][1]
                                if pair_index < len(question.pairs)
                                else "",
                                key=f"pair_right_{section_index}_{question_index}_{pair_index}",
                            ),
                        )
                        for pair_index in range(configured_section.questions_to_generate)
                    ]
                if question.question_type is QuestionType.CASE_STUDY:
                    question.sub_questions = [
                        st.text_area(
                            f"Sub-question {sub_index + 1}",
                            question.sub_questions[sub_index]
                            if sub_index < len(question.sub_questions)
                            else "",
                            key=f"sub_question_{section_index}_{question_index}_{sub_index}",
                        )
                        for sub_index in range(configured_section.questions_to_generate)
                    ]

    issues = validate_export_ready_paper(st.session_state.blueprint, paper)
    for issue in issues:
        st.error(issue.message)


def download_step() -> None:
    st.subheader("Download the Word file")
    if st.session_state.paper is None:
        st.info("Generate a valid paper before downloading.")
        return
    issues = validate_export_ready_paper(st.session_state.blueprint, st.session_state.paper)
    if issues:
        for issue in issues:
            st.error(issue.message)
        st.info("Fix the paper issues above before downloading.")
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
    render_wizard_progress()
    current = clamp_step(st.session_state.wizard_step)
    if current == 0:
        upload_step()
    elif current == 1:
        topics_step()
    elif current == 2:
        paper_details_step()
    elif current == 3:
        question_sections_step()
    elif current == 4:
        generation_step()
    elif current == 5:
        download_step()
    navigation_controls()


if __name__ == "__main__":
    main()
