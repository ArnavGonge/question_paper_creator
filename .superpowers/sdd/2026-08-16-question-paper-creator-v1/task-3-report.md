# Task 3 Report

## Status

COMPLETE

## Files Changed

- `src/qpc/validators.py`
- `tests/test_validators.py`

## Requirements Check

- Created `src/qpc/validators.py`.
- Created `tests/test_validators.py`.
- Added `ValidationIssue` as a frozen dataclass.
- Added `validate_blueprint(blueprint: PaperBlueprint) -> list[ValidationIssue]`.
- Added `validate_generated_paper(blueprint: PaperBlueprint, paper: GeneratedPaper) -> list[ValidationIssue]`.
- Used existing schemas from `src/qpc/schemas.py` as the source of truth.
- Kept edits scoped to Task 3 files.

## Tests / Commands / Results

1. Red phase:
   - Command: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_validators.py -v`
   - Result: FAIL during collection with `ModuleNotFoundError: No module named 'qpc.validators'`

2. Green phase:
   - Command: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_validators.py -v`
   - Result: PASS, `4 passed in 0.05s`

3. Lint:
   - Command: `PYTHONPATH=src .venv/bin/python -m ruff check src/qpc/validators.py tests/test_validators.py`
   - Result: PASS, `All checks passed!`

## Self-Review Notes

- Matched the Task 3 brief code and test values verbatim.
- Confirmed the test failure happened for the expected reason before implementation.
- Kept validation logic aligned with the current schema behavior, including `GeneratedSection` question type consistency.
- Did not change schema code or any non-Task-3 file outside the required report.

## Concerns

- `GeneratedSection` already enforces per-question type consistency at model validation time, so the `question_type_mismatch` branch in `validate_generated_paper()` is defensive and may be unreachable for fully validated inputs.
- Git commit was intentionally skipped because `.git` is a read-only harness mount per task constraints.
