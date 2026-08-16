Status: Complete

Files changed:
- `src/qpc/topic_extractor.py`
- `src/qpc/question_generator.py`
- `tests/test_prompt_builders.py`

Tests / commands / results:
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_prompt_builders.py -v`
  - Initial run: failed during collection with `ModuleNotFoundError: No module named 'qpc.question_generator'`, which was the expected red-state proving the new modules did not yet exist.
  - Final run: passed, `4 passed in 0.43s`.
- `.venv/bin/ruff check src/qpc/topic_extractor.py src/qpc/question_generator.py tests/test_prompt_builders.py`
  - Result: passed, `All checks passed!`

Self-review notes:
- Kept Task 5 scoped to the two new AI adapter modules and the prompt-builder test file.
- Reused existing Task 2 schemas and validation through `model_validate(...)` exactly as the brief requires.
- Confirmed the pinned `openai==3.1.0` SDK supports `OpenAI(...).responses.create(..., text={"format": {"type": "json_object"}})`, so no public-interface adjustment was required.
- Kept tests network-free by limiting them to prompt construction and response parsing.

Concerns:
- The AI adapter functions are not exercised in tests because Task 5 explicitly requires network-free tests. Any runtime issues in live API calls would need follow-up tests with mocked SDK responses or an integration test path.
- Git commit was intentionally skipped because `.git` is a read-only harness mount in this environment.
