### Task 6: DOCX Exporter

**Files:**
- Create: `src/qpc/docx_exporter.py`
- Create: `tests/test_docx_exporter.py`

**Interfaces:**
- Consumes: `PaperMetadata`, `PaperBlueprint`, `GeneratedPaper`.
- Produces: `render_docx(blueprint: PaperBlueprint, paper: GeneratedPaper) -> bytes`.

- [ ] **Step 1: Write DOCX tests**

`tests/test_docx_exporter.py`:

```python
from io import BytesIO

from docx import Document

from qpc.docx_exporter import render_docx
from qpc.schemas import (
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperBlueprint,
    PaperMetadata,
    QuestionType,
    SectionBlueprint,
)


def test_render_docx_contains_header_and_questions():
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
                questions_to_generate=1,
                questions_to_answer=1,
                marks_per_question=4,
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
                        text="Which physical feature is known as the storehouse of water?",
                        options=["Coastal Plains", "Himalayas", "Deccan Plateau", "Islands"],
                    )
                ],
            )
        ]
    )

    data = render_docx(blueprint, paper)
    document = Document(BytesIO(data))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)

    assert "ZENITH PUBLIC SCHOOL" in text
    assert "First Periodic Assessment 2026-27" in text
    assert "Section A" in text
    assert "Which physical feature" in text
    assert "*****" in text
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src pytest tests/test_docx_exporter.py -v
```

Expected: FAIL because `qpc.docx_exporter` does not exist.

- [ ] **Step 3: Implement exporter**

`src/qpc/docx_exporter.py`:

```python
from io import BytesIO

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from qpc.schemas import GeneratedPaper, PaperBlueprint, QuestionType, SectionBlueprint


def render_docx(blueprint: PaperBlueprint, paper: GeneratedPaper) -> bytes:
    document = Document()
    style = document.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)

    _add_header(document, blueprint)
    sections_by_label = {section.label: section for section in paper.sections}
    for section_blueprint in blueprint.sections:
        generated_section = sections_by_label[section_blueprint.label]
        _add_section(document, section_blueprint, generated_section)

    end = document.add_paragraph("*****")
    end.alignment = WD_ALIGN_PARAGRAPH.CENTER

    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _add_header(document: Document, blueprint: PaperBlueprint) -> None:
    metadata = blueprint.metadata
    school = document.add_paragraph(metadata.school_name)
    school.alignment = WD_ALIGN_PARAGRAPH.CENTER
    school.runs[0].bold = True
    school.runs[0].font.size = Pt(14)

    address = document.add_paragraph(metadata.school_address)
    address.alignment = WD_ALIGN_PARAGRAPH.CENTER
    affiliation = document.add_paragraph(f"({metadata.affiliation})")
    affiliation.alignment = WD_ALIGN_PARAGRAPH.CENTER

    exam = document.add_paragraph(metadata.exam_name)
    exam.alignment = WD_ALIGN_PARAGRAPH.CENTER
    exam.runs[0].bold = True

    table = document.add_table(rows=3, cols=2)
    table.cell(0, 0).text = f"Grade: {metadata.grade}"
    table.cell(0, 1).text = f"Subject: - {metadata.subject}"
    table.cell(1, 0).text = "Name: -_____________________________"
    table.cell(1, 1).text = f"Date: - {metadata.date}"
    table.cell(2, 0).text = "Roll No: - _______"
    table.cell(2, 1).text = f"M.M. {metadata.max_marks}        Time- {metadata.duration}"


def _section_summary(section: SectionBlueprint) -> str:
    total = section.section_marks()
    if section.questions_to_answer < section.questions_to_generate:
        return f"{section.heading} (Any {section.questions_to_answer}) ({section.questions_to_answer}x{section.marks_per_question}={total})"
    return f"{section.heading} ({section.questions_to_answer}x{section.marks_per_question}={total})"


def _add_section(document: Document, section_blueprint: SectionBlueprint, generated_section) -> None:
    label = document.add_paragraph(section_blueprint.label)
    label.alignment = WD_ALIGN_PARAGRAPH.CENTER
    label.runs[0].bold = True

    summary = document.add_paragraph(_section_summary(section_blueprint))
    summary.alignment = WD_ALIGN_PARAGRAPH.CENTER
    summary.runs[0].bold = True

    if generated_section.passage.strip():
        document.add_paragraph(generated_section.passage.strip())

    for index, question in enumerate(generated_section.questions, start=1):
        document.add_paragraph(f"{index}. {question.text.strip()}")
        if section_blueprint.question_type is QuestionType.MCQ:
            options = " ".join(f"{chr(97 + option_index)}) {option}" for option_index, option in enumerate(question.options))
            document.add_paragraph(options)
        elif section_blueprint.question_type is QuestionType.MATCH:
            for left, right in question.pairs:
                document.add_paragraph(f"{left} — {right}")
        for sub_index, sub_question in enumerate(question.sub_questions, start=1):
            document.add_paragraph(f"({sub_index}) {sub_question}")
```

- [ ] **Step 4: Run DOCX tests**

```bash
PYTHONPATH=src pytest tests/test_docx_exporter.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit when git exists**

```bash
git add src/qpc/docx_exporter.py tests/test_docx_exporter.py
git commit -m "feat: render question paper docx"
```

---

