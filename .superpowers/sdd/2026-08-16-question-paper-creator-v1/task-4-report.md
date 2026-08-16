Status: complete

Files changed:
- src/qpc/pdf_extractor.py
- tests/test_pdf_extractor.py
- .superpowers/sdd/2026-08-16-question-paper-creator-v1/task-4-report.md

Tests / commands / results:
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_pdf_extractor.py -v`
  - First run: failed during collection with `ModuleNotFoundError: No module named 'qpc.pdf_extractor'`, matching the expected red state from the brief.
  - Final run: passed, `3 passed in 0.22s`.
- `.venv/bin/python -m ruff check src/qpc/pdf_extractor.py tests/test_pdf_extractor.py`
  - First run: failed with `I001` import ordering issues in both new files.
  - After `.venv/bin/python -m ruff check --fix src/qpc/pdf_extractor.py tests/test_pdf_extractor.py`: passed, `All checks passed!`

Self-review notes:
- Kept implementation scoped to the Task 4 source and test files and reused `SourceDocument` / `SourcePage` from `qpc.schemas`.
- Used the exact interface names and noise-removal patterns specified in the task brief.
- Verified the extraction path against the sample PDFs in `data/` through the required tests.

Concerns:
- Commit was not created because the task context says `.git` is a read-only harness mount and to skip `git commit`.
- Verification was scoped to the Task 4 test module and the two Task 4 files for linting; no broader test suite was run.
