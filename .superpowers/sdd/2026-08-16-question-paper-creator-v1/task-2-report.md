Status: DONE

Files changed:
- `src/qpc/schemas.py`
- `tests/test_schemas.py`

Tests/commands run and results:
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_schemas.py -v`
  - Initial red run: failed during collection with `ModuleNotFoundError: No module named 'qpc.schemas'`
  - Final verification run: passed, `4 passed`
- `PYTHONPATH=src .venv/bin/ruff check src/qpc/schemas.py tests/test_schemas.py`
  - Initial lint run: failed with `F401` for unused `GeneratedSection` import in `tests/test_schemas.py`
  - Final verification run: passed, `All checks passed!`

Self-review notes:
- Kept edits scoped to the two Task 2 files named in the brief.
- Implemented the schema models, enum, validators, and mark-calculation helpers exactly as required by the task brief.
- Added the minimal extra assertion needed to satisfy Ruff while preserving the brief's test intent.

Concerns, if any:
- Git commit was intentionally skipped because `.git` is a read-only harness mount per task constraints.

---

Fix round 1:

Status: DONE

Files changed:
- `src/qpc/schemas.py`
- `tests/test_schemas.py`

Tests/commands run and results:
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_schemas.py -v`
  - Red run after adding reviewer-requested tests: failed with `Failed: DID NOT RAISE ValidationError` in `test_generated_section_rejects_mixed_question_types`
  - First green run after adding `GeneratedSection` validation: passed, `8 passed`
  - Final verification run after import-order cleanup: passed, `8 passed`
- `PYTHONPATH=src .venv/bin/ruff check src/qpc/schemas.py tests/test_schemas.py`
  - First lint run after schema fix: failed with `I001 Import block is un-sorted or un-formatted` in `tests/test_schemas.py`
  - Final verification run: passed, `All checks passed!`

Self-review notes:
- Added a single `GeneratedSection` model validator to enforce that every `GeneratedQuestion.question_type` matches the section `question_type`.
- Expanded tests to cover `SourceDocument.combined_text()`, `Topic`/`TopicSet` defaults, `PaperBlueprint` empty-section validation, and mixed question-type rejection in `GeneratedSection`.
- Kept edits scoped to the reviewer-approved files.

Concerns, if any:
- Git commit was intentionally skipped because `.git` is a read-only harness mount per task constraints.
