from __future__ import annotations

from dataclasses import dataclass
from html import escape

import streamlit as st

from qpc.error_reporting import ErrorReport
from qpc.schemas import QuestionType, SectionBlueprint


@dataclass(frozen=True)
class StepCopy:
    title: str
    prompt: str


STEP_COPY = {
    "Upload PDFs": StepCopy(
        "Add source material",
        "Choose the textbook PDFs this paper should use.",
    ),
    "Topics": StepCopy(
        "Choose topics",
        "Select the extracted topics that belong in this paper.",
    ),
    "Paper Details": StepCopy(
        "Set paper details",
        "Check the information that will appear in the document header.",
    ),
    "Question Sections": StepCopy(
        "Build question sections",
        "Set the question mix and marks for each part of the paper.",
    ),
    "Generate and Review": StepCopy(
        "Generate and review",
        "Create the paper, then review each section before export.",
    ),
    "Download Word Document": StepCopy(
        "Download the paper",
        "Check the final summary and prepare the Word document.",
    ),
}


QUESTION_TYPE_LABELS = {
    QuestionType.MCQ: "Multiple Choice",
    QuestionType.VERY_SHORT: "Very Short Answer",
    QuestionType.SHORT: "Short Answer",
    QuestionType.LONG: "Long Answer",
    QuestionType.FILL_BLANKS: "Fill in the Blanks",
    QuestionType.TRUE_FALSE: "True or False",
    QuestionType.MATCH: "Match the Following",
    QuestionType.CASE_STUDY: "Case Study",
    QuestionType.MAP_DIAGRAM: "Map or Diagram",
}


APP_CSS = """
<style>
:root {
  --qpc-canvas: #f5f7f8;
  --qpc-surface: #ffffff;
  --qpc-text: #17202a;
  --qpc-muted: #5f6b76;
  --qpc-border: #d9e0e4;
  --qpc-primary: #0f766e;
  --qpc-primary-hover: #0b5f59;
  --qpc-warning: #b45309;
  --qpc-danger: #b42318;
  --qpc-success: #18794e;
}

.stApp {
  background: var(--qpc-canvas);
  color: var(--qpc-text);
}

[data-testid="stHeader"] {
  background: rgba(245, 247, 248, 0.94);
}

[data-testid="stSidebar"] {
  background: var(--qpc-surface);
  border-right: 1px solid var(--qpc-border);
}

.block-container {
  max-width: 1120px;
  padding-top: 2.25rem;
  padding-bottom: 2rem;
}

h1, h2, h3, h4, h5, h6, p, label, button {
  letter-spacing: 0 !important;
}

.qpc-step-heading {
  border-bottom: 1px solid var(--qpc-border);
  margin-bottom: 1.25rem;
  padding-bottom: 1rem;
}

.qpc-step-heading h2 {
  color: var(--qpc-text);
  font-size: 1.65rem;
  line-height: 1.25;
  margin: 0.2rem 0 0.35rem;
}

.qpc-step-heading p {
  color: var(--qpc-muted);
  font-size: 0.98rem;
  margin: 0;
}

.qpc-eyebrow {
  color: var(--qpc-primary);
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
}

div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button {
  border-radius: 6px;
  min-height: 2.65rem;
  font-weight: 650;
}

button[kind="primary"] {
  background: var(--qpc-primary);
  border-color: var(--qpc-primary);
}

button[kind="primary"]:hover {
  background: var(--qpc-primary-hover);
  border-color: var(--qpc-primary-hover);
}

[data-testid="stExpander"],
[data-testid="stFileUploaderDropzone"],
[data-testid="stAlert"] {
  background: var(--qpc-surface);
  border-color: var(--qpc-border);
  border-radius: 8px;
}

[data-testid="stMetric"] {
  border-left: 3px solid var(--qpc-primary);
  padding: 0.25rem 0 0.25rem 0.8rem;
}

[data-baseweb="input"] > div,
[data-baseweb="select"] > div,
textarea {
  border-radius: 6px !important;
}

hr {
  border-color: var(--qpc-border);
}

@media (max-width: 700px) {
  .block-container {
    padding-left: 1rem;
    padding-right: 1rem;
    padding-top: 1.25rem;
  }

  [data-testid="stHorizontalBlock"] {
    flex-direction: column;
    gap: 0.55rem;
  }

  [data-testid="column"] {
    flex: 1 1 auto !important;
    min-width: 100% !important;
    width: 100% !important;
  }
}
</style>
"""


def section_header(section: SectionBlueprint) -> str:
    mark_label = "mark" if section.marks_per_question == 1 else "marks"
    return (
        f"{section.label} | {QUESTION_TYPE_LABELS[section.question_type]} | "
        f"Answer {section.questions_to_answer} | "
        f"{section.marks_per_question} {mark_label} each | "
        f"{section.section_marks()} marks"
    )


def error_report_text(report: ErrorReport) -> str:
    return f"{report.user_message} Reference: {report.reference_id}"


def apply_app_theme() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_step_heading(step_name: str, *, summary: str = "") -> None:
    copy = STEP_COPY[step_name]
    description = summary or copy.prompt
    st.markdown(
        (
            '<div class="qpc-step-heading">'
            f'<span class="qpc-eyebrow">{escape(step_name)}</span>'
            f"<h2>{escape(copy.title)}</h2>"
            f"<p>{escape(description)}</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_error_report(report: ErrorReport) -> None:
    st.error(error_report_text(report))
