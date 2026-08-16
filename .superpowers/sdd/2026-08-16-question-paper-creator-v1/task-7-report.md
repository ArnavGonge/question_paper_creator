Status: Complete

Files changed:
- `src/qpc/demo_data.py`
- `tests/test_demo_data.py`

Tests / commands / results:
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_demo_data.py -v`
  - Initial run: failed during collection with `ModuleNotFoundError: No module named 'qpc.demo_data'`, which was the expected red-state proving the new module did not yet exist.
  - Final run: passed, `1 passed in 0.05s`.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_imports.py tests/test_schemas.py tests/test_validators.py tests/test_pdf_extractor.py tests/test_prompt_builders.py tests/test_docx_exporter.py tests/test_demo_data.py -v`
  - Result: passed, `23 passed in 0.66s`.
- `.venv/bin/ruff check src tests`
  - Result: passed, `All checks passed!`

Self-review notes:
- Kept the implementation scoped to the Task 7 module, its test, and this required report file.
- Used the exact metadata and section values from the Task 7 brief, with no schema changes.
- Defaults match the sample paper pattern totals: `metadata.max_marks == 30` and `default_blueprint().total_marks() == 30`.
- Reused existing `PaperMetadata`, `SectionBlueprint`, `PaperBlueprint`, and `QuestionType` models from Tasks 1-6 as requested.

Concerns:
- The Task 7 test intentionally verifies the sample total and section type ordering from the brief; it does not separately assert every metadata field and per-section numeric field, although those are implemented verbatim in `default_metadata()` and `default_sections()`.
- Git commit was intentionally skipped because `.git` is a read-only harness mount in this environment and the task instructions explicitly said not to commit.
