### Task 7: Demo Defaults

**Files:**
- Create: `src/qpc/demo_data.py`
- Create: `tests/test_demo_data.py`

**Interfaces:**
- Consumes: schemas from Task 2.
- Produces: `default_metadata() -> PaperMetadata`.
- Produces: `default_sections() -> list[SectionBlueprint]`.
- Produces: `default_blueprint() -> PaperBlueprint`.

- [ ] **Step 1: Write default tests**

`tests/test_demo_data.py`:

```python
from qpc.demo_data import default_blueprint
from qpc.schemas import QuestionType


def test_default_blueprint_matches_sample_total():
    blueprint = default_blueprint()

    assert blueprint.metadata.max_marks == 30
    assert blueprint.total_marks() == 30
    assert [section.question_type for section in blueprint.sections] == [
        QuestionType.MCQ,
        QuestionType.VERY_SHORT,
        QuestionType.SHORT,
        QuestionType.LONG,
        QuestionType.CASE_STUDY,
        QuestionType.MAP_DIAGRAM,
    ]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src pytest tests/test_demo_data.py -v
```

Expected: FAIL because `qpc.demo_data` does not exist.

- [ ] **Step 3: Implement defaults**

`src/qpc/demo_data.py`:

```python
from qpc.schemas import PaperBlueprint, PaperMetadata, QuestionType, SectionBlueprint


def default_metadata() -> PaperMetadata:
    return PaperMetadata(
        grade="VII",
        subject="Social Science",
        exam_name="First Periodic Assessment 2026-27",
        date="17.07.2026",
        max_marks=30,
        duration="2 Hour",
    )


def default_sections() -> list[SectionBlueprint]:
    return [
        SectionBlueprint(
            label="Section A",
            heading="Multiple Choice Based Questions",
            question_type=QuestionType.MCQ,
            questions_to_generate=4,
            questions_to_answer=4,
            marks_per_question=1,
        ),
        SectionBlueprint(
            label="Section B",
            heading="Very Short Answer Based Questions",
            question_type=QuestionType.VERY_SHORT,
            questions_to_generate=3,
            questions_to_answer=2,
            marks_per_question=2,
        ),
        SectionBlueprint(
            label="Section C",
            heading="Short Answer Based Questions",
            question_type=QuestionType.SHORT,
            questions_to_generate=4,
            questions_to_answer=3,
            marks_per_question=3,
        ),
        SectionBlueprint(
            label="Section D",
            heading="Long Answer Questions",
            question_type=QuestionType.LONG,
            questions_to_generate=3,
            questions_to_answer=2,
            marks_per_question=5,
        ),
        SectionBlueprint(
            label="Section E",
            heading="Case Study Based Questions",
            question_type=QuestionType.CASE_STUDY,
            questions_to_generate=2,
            questions_to_answer=2,
            marks_per_question=1,
        ),
        SectionBlueprint(
            label="Section F",
            heading="Map Based Question",
            question_type=QuestionType.MAP_DIAGRAM,
            questions_to_generate=1,
            questions_to_answer=1,
            marks_per_question=1,
        ),
    ]


def default_blueprint() -> PaperBlueprint:
    return PaperBlueprint(metadata=default_metadata(), sections=default_sections())
```

- [ ] **Step 4: Run default tests**

```bash
PYTHONPATH=src pytest tests/test_demo_data.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit when git exists**

```bash
git add src/qpc/demo_data.py tests/test_demo_data.py
git commit -m "feat: add sample paper defaults"
```

---

