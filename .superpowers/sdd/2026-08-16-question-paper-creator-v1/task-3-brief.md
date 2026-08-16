### Task 3: Validators

**Files:**
- Create: `src/qpc/validators.py`
- Create: `tests/test_validators.py`

**Interfaces:**
- Consumes: schemas from Task 2.
- Produces: `ValidationIssue` dataclass.
- Produces: `validate_blueprint(blueprint: PaperBlueprint) -> list[ValidationIssue]`.
- Produces: `validate_generated_paper(blueprint: PaperBlueprint, paper: GeneratedPaper) -> list[ValidationIssue]`.

- [ ] **Step 1: Write validator tests**

`tests/test_validators.py`:

```python
from qpc.schemas import (
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperBlueprint,
    PaperMetadata,
    QuestionType,
    SectionBlueprint,
)
from qpc.validators import validate_blueprint, validate_generated_paper


def make_blueprint() -> PaperBlueprint:
    return PaperBlueprint(
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


def test_validate_blueprint_detects_total_mismatch():
    blueprint = make_blueprint()
    blueprint.metadata.max_marks = 5

    issues = validate_blueprint(blueprint)

    assert [issue.code for issue in issues] == ["paper_total_mismatch"]


def test_validate_generated_paper_accepts_valid_mcq_section():
    blueprint = make_blueprint()
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions=[
                    GeneratedQuestion(question_type=QuestionType.MCQ, text=f"Question {i}", options=["A", "B", "C", "D"])
                    for i in range(1, 5)
                ],
            )
        ]
    )

    assert validate_generated_paper(blueprint, paper) == []


def test_validate_generated_paper_detects_missing_mcq_options():
    blueprint = make_blueprint()
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions=[
                    GeneratedQuestion(question_type=QuestionType.MCQ, text="Question 1", options=["A", "B"]),
                    GeneratedQuestion(question_type=QuestionType.MCQ, text="Question 2", options=["A", "B", "C", "D"]),
                    GeneratedQuestion(question_type=QuestionType.MCQ, text="Question 3", options=["A", "B", "C", "D"]),
                    GeneratedQuestion(question_type=QuestionType.MCQ, text="Question 4", options=["A", "B", "C", "D"]),
                ],
            )
        ]
    )

    issues = validate_generated_paper(blueprint, paper)

    assert "mcq_option_count" in {issue.code for issue in issues}


def test_validate_generated_paper_detects_wrong_question_count():
    blueprint = make_blueprint()
    paper = GeneratedPaper(
        sections=[
            GeneratedSection(
                label="Section A",
                heading="Multiple Choice Based Questions",
                question_type=QuestionType.MCQ,
                questions=[
                    GeneratedQuestion(question_type=QuestionType.MCQ, text="Question 1", options=["A", "B", "C", "D"])
                ],
            )
        ]
    )

    issues = validate_generated_paper(blueprint, paper)

    assert "question_count_mismatch" in {issue.code for issue in issues}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src pytest tests/test_validators.py -v
```

Expected: FAIL because `qpc.validators` does not exist.

- [ ] **Step 3: Implement validators**

`src/qpc/validators.py`:

```python
from dataclasses import dataclass

from qpc.schemas import GeneratedPaper, PaperBlueprint, QuestionType


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    section_label: str = ""


def validate_blueprint(blueprint: PaperBlueprint) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    total = blueprint.total_marks()
    if total != blueprint.metadata.max_marks:
        issues.append(
            ValidationIssue(
                code="paper_total_mismatch",
                message=f"Configured sections total {total} marks, but max marks is {blueprint.metadata.max_marks}.",
            )
        )
    return issues


def validate_generated_paper(blueprint: PaperBlueprint, paper: GeneratedPaper) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    expected_by_label = {section.label: section for section in blueprint.sections}
    generated_by_label = {section.label: section for section in paper.sections}

    for blueprint_section in blueprint.sections:
        generated_section = generated_by_label.get(blueprint_section.label)
        if generated_section is None:
            issues.append(
                ValidationIssue(
                    code="missing_section",
                    message=f"{blueprint_section.label} is missing from generated paper.",
                    section_label=blueprint_section.label,
                )
            )
            continue

        if generated_section.question_type != blueprint_section.question_type:
            issues.append(
                ValidationIssue(
                    code="section_type_mismatch",
                    message=f"{blueprint_section.label} should be {blueprint_section.question_type}.",
                    section_label=blueprint_section.label,
                )
            )

        if len(generated_section.questions) != blueprint_section.questions_to_generate:
            issues.append(
                ValidationIssue(
                    code="question_count_mismatch",
                    message=(
                        f"{blueprint_section.label} should contain "
                        f"{blueprint_section.questions_to_generate} questions."
                    ),
                    section_label=blueprint_section.label,
                )
            )

        if blueprint_section.question_type is QuestionType.CASE_STUDY and not generated_section.passage.strip():
            issues.append(
                ValidationIssue(
                    code="missing_case_study_passage",
                    message=f"{blueprint_section.label} needs a case-study passage.",
                    section_label=blueprint_section.label,
                )
            )

        for question in generated_section.questions:
            if len(question.text.strip()) < 8:
                issues.append(
                    ValidationIssue(
                        code="question_too_short",
                        message=f"{blueprint_section.label} contains an empty or too-short question.",
                        section_label=blueprint_section.label,
                    )
                )
            if blueprint_section.question_type is QuestionType.MCQ and len(question.options) != 4:
                issues.append(
                    ValidationIssue(
                        code="mcq_option_count",
                        message=f"{blueprint_section.label} MCQs must have exactly four options.",
                        section_label=blueprint_section.label,
                    )
                )
            if question.question_type != blueprint_section.question_type:
                issues.append(
                    ValidationIssue(
                        code="question_type_mismatch",
                        message=f"{blueprint_section.label} contains a question with the wrong type.",
                        section_label=blueprint_section.label,
                    )
                )

    extra_labels = set(generated_by_label) - set(expected_by_label)
    for label in sorted(extra_labels):
        issues.append(
            ValidationIssue(
                code="unexpected_section",
                message=f"{label} was generated but is not in the blueprint.",
                section_label=label,
            )
        )

    return issues
```

- [ ] **Step 4: Run validator tests**

```bash
PYTHONPATH=src pytest tests/test_validators.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit when git exists**

```bash
git add src/qpc/validators.py tests/test_validators.py
git commit -m "feat: validate question paper structures"
```

---

