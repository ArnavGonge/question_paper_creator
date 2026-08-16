Status: completed

Files changed:
- `src/qpc/docx_exporter.py`
- `tests/test_docx_exporter.py`

Tests / commands / results:
1. `PYTHONPATH=src .venv/bin/python -m pytest tests/test_docx_exporter.py -v`
   Result: failed during collection with `ModuleNotFoundError: No module named 'qpc.docx_exporter'` before implementation.
2. `PYTHONPATH=src .venv/bin/python -m pytest tests/test_docx_exporter.py -v`
   Result: passed (`1 passed`).
3. `.venv/bin/python -m ruff check src/qpc/docx_exporter.py tests/test_docx_exporter.py`
   Result: passed (`All checks passed!`).
4. `PYTHONPATH=src .venv/bin/python -m pytest tests/test_imports.py -v`
   Result: passed (`1 passed`).

Self-review notes:
- Kept edits scoped to the Task 6 files requested in the brief.
- Implemented `render_docx(blueprint: PaperBlueprint, paper: GeneratedPaper) -> bytes` exactly as the Task 6 brief specifies.
- The exporter uses existing schema defaults for school metadata and emits `.docx` bytes through `python-docx`.
- Header, section summaries, question text, MCQ options, case-study passage support, match-pair rendering, sub-questions, and closing `*****` marker are all covered by the implementation path.
- The current automated test covers the required header/content presence check from the brief. It does not yet assert full document layout fidelity beyond that required surface.

Concerns:
- The current test validates key text presence in the generated document, but it does not fully lock down formatting details such as table layout, spacing, or sample-paper visual parity.
- The brief included a commit step, but `.git` is a read-only harness mount and the user explicitly said to skip commit, so no git commit was attempted.

---

Fix round 1 status: completed

Files changed in fix round 1:
- `src/qpc/docx_exporter.py`
- `tests/test_docx_exporter.py`

Fix round 1 tests / commands / results:
1. `PYTHONPATH=src .venv/bin/python -m pytest tests/test_docx_exporter.py -v`
   Result before exporter change: failed (`2 failed`) because section instructions were missing from rendered output in both the MCQ and case-study coverage.
2. `PYTHONPATH=src .venv/bin/python -m pytest tests/test_docx_exporter.py -v`
   Result after exporter change: passed (`2 passed`).
3. `PYTHONPATH=src .venv/bin/ruff check src/qpc/docx_exporter.py tests/test_docx_exporter.py`
   Result: passed (`All checks passed!`).

Fix round 1 self-review notes:
- Added `_document_text()` test helper coverage so assertions include both paragraph content and table cell content.
- Expanded the primary DOCX test to assert grade, subject, date, max marks, and time from the header table.
- Added a case-study coverage path for instruction, passage, prompt text, and sub-questions.
- Updated the exporter to render non-empty section instructions immediately after the section summary and before passage/questions, matching the review requirement.

Fix round 1 concerns:
- Tests now cover required text presence for the header table and case-study structure, but they still do not assert deeper formatting fidelity such as alignment, fonts, or exact table styling from the sample paper.
