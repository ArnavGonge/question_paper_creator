Status: completed

Files changed:
- `app.py`
- `tests/test_app_config.py`

Tests / commands / results:
1. `PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_config.py -v`
   Result before implementation: failed during collection with `ModuleNotFoundError: No module named 'app'`, which was the expected red-state because `app.py` did not exist yet.
2. `PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_config.py -v`
   Result after implementation: passed (`1 passed in 0.64s`).
3. `PYTHONPATH=src .venv/bin/python -m pytest -v`
   Result: passed (`24 passed in 0.81s`).
4. `.venv/bin/python -m ruff check app.py tests/test_app_config.py src/qpc tests`
   Result: passed (`All checks passed!`).
5. `timeout 15s env PYTHONPATH=src .venv/bin/streamlit run app.py --server.headless true --server.port 8501`
   Result in sandbox: failed with `PermissionError: [Errno 1] Operation not permitted` when binding the local socket.
6. `timeout 15s env PYTHONPATH=src .venv/bin/streamlit run app.py --server.headless true --server.port 8501`
   Result with approved escalation: Streamlit started successfully on Sunday, August 16, 2026, with `Local URL: http://localhost:8501`; the timeout then stopped it cleanly.

Self-review notes:
- Kept edits scoped to the Task 8 files requested in the brief.
- Implemented `load_secret(name: str, default: str = "") -> str` exactly as specified, sourcing from `streamlit.secrets` first and falling back to environment variables.
- Wired the app to existing `qpc` modules only: PDF extraction, AI topic extraction, blueprint validation, question generation, generated-paper validation, and DOCX export.
- Preserved the simple session-based workflow from the brief: password gate, upload, topic selection, paper configuration, generation/review, and DOCX download.
- No compatibility adjustment was needed to existing module interfaces, so the brief’s public behavior was implemented directly.

Concerns:
- The automated test coverage added by Task 8 is intentionally narrow and only verifies `load_secret`; the rest of the Streamlit workflow is covered here by linting, the existing backend test suite, and a local startup check rather than UI automation.
- Streamlit startup requires permission to bind a localhost port in this harness, so that verification needed one escalated command.
- Git commit was intentionally skipped because `.git` is a read-only harness mount in this environment and the task instructions explicitly said not to commit.

---

Fix round 1 status: completed

Files changed in fix round 1:
- `app.py`
- `tests/test_app_config.py`

Fix round 1 tests / commands / results:
1. `PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_config.py -v`
   Result before implementation: failed during collection with `ImportError: cannot import name 'paper_is_stale' from 'app'`, which was the expected red-state proving the new helper surface did not exist yet.
2. `PYTHONPATH=src .venv/bin/python -m pytest tests/test_app_config.py -v`
   Result after implementation: passed (`4 passed in 0.64s`).
3. `PYTHONPATH=src .venv/bin/python -m pytest -v`
   Result: passed (`27 passed in 0.81s`).
4. `PYTHONPATH=src .venv/bin/ruff check src tests app.py`
   Result: passed (`All checks passed!`).
5. `timeout 15s env PYTHONPATH=src .venv/bin/streamlit run app.py --server.headless true --server.port 8501`
   Result in sandbox: attempted and failed with `PermissionError: [Errno 1] Operation not permitted` while binding the local socket. No escalated rerun was requested in this fix round because the task only required reporting whether the startup check was run if escalation would be needed.

Fix round 1 self-review notes:
- Added small pure helpers in `app.py` for document/topic snapshots, stale-paper comparison, and export-time paper validation so the new behavior is testable without UI automation.
- Generated paper is now invalidated only when inputs actually differ from the paper’s saved generation inputs: extracted documents, selected topics, or blueprint configuration.
- The app now stores the generation input snapshot alongside the paper and clears both together when a relevant upstream change makes the paper stale.
- Manual edits are validated after the review form renders and again before download; invalid papers now block export with visible validation errors instead of allowing a bad DOCX render path.

Fix round 1 concerns:
- The stale-state logic compares stable serialized snapshots rather than object identity, which is the intended behavior here, but it still relies on the existing Pydantic model dump shape staying stable.
- Streamlit startup was attempted but not rerun with escalation in this round, so there is no fresh post-fix socket-bind startup confirmation beyond tests, lint, and the code-path review.
- Git commit was intentionally skipped because `.git` is a read-only harness mount in this environment and the task instructions explicitly said not to commit.
