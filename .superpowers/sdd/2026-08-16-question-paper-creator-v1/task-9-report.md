Status: completed with concerns

Files changed:
- `README.md`
- `docs/deployment.md`
- `.superpowers/sdd/2026-08-16-question-paper-creator-v1/task-9-report.md`

Tests / commands / results:
1. `env PYTHONPATH=src .venv/bin/python -m pytest -v`
   Result: passed (`27 passed in 0.83s`).
2. `env PYTHONPATH=src .venv/bin/ruff check src tests app.py`
   Result: passed (`All checks passed!`).
3. `timeout 15s env PYTHONPATH=src .venv/bin/python -m streamlit run app.py`
   Result in sandbox: Streamlit did not reach the app startup flow because the first-run CLI onboarding prompt requested an email address and then exited with code `255`. The manual smoke checklist from the brief could not be completed in this harness from that command result.

Self-review notes:
- Kept edits scoped to the Task 9 docs and this required report file.
- Used the exact Task 9 README and deployment content, adjusting local commands to `.venv/bin/python` and `.venv/bin/ruff` for this workspace.
- Preserved the brief’s exact deployment secret names and hosted deployment notes.
- Verified the current codebase still passes the full pytest suite and Ruff checks after adding the docs.

Concerns:
- The manual local smoke test did not complete because `streamlit run` stopped at Streamlit's first-run onboarding email prompt in this sandboxed harness, so I could not verify the password screen, uploads, topic extraction, generation flow, review UI, or DOCX download from that command.
- Git commit was intentionally skipped because `.git` is a read-only harness mount in this environment and the task instructions explicitly said not to commit.

---

Fix round 1 status: completed with concerns

Files changed in fix round 1:
- `docs/deployment.md`
- `.superpowers/sdd/2026-08-16-question-paper-creator-v1/task-9-report.md`

Fix round 1 tests / commands / results:
1. `env PYTHONPATH=src .venv/bin/python -m pytest -v`
   Result: passed (`27 passed in 0.83s`).
2. `env PYTHONPATH=src .venv/bin/ruff check src tests app.py`
   Result: passed (`All checks passed!`).
3. `timeout 15s env STREAMLIT_BROWSER_GATHER_USAGE_STATS=false APP_PASSWORD=dummy-password PYTHONPATH=src .venv/bin/python -m streamlit run app.py --server.headless true`
   Result in sandbox: onboarding was bypassed, but Streamlit failed during server startup with `PermissionError: [Errno 1] Operation not permitted` while creating the socket in `streamlit/web/server/starlette/starlette_server.py`. No escalated rerun was requested, per task instructions.

Fix round 1 self-review notes:
- Corrected the hosted Render/Railway command to use host-native `streamlit run` invocation rather than a workspace-local `.venv` path.
- Kept local README commands unchanged because this workspace explicitly uses `.venv`.
- Re-ran the required verification commands fresh and recorded the actual non-interactive Streamlit sandbox failure instead of the earlier onboarding prompt.

Fix round 1 concerns:
- The hosted deployment doc now uses a platform-appropriate command, but the local harness still cannot complete a full manual UI smoke test because socket creation is denied before the app can be reached.
- Git commit was intentionally skipped because `.git` is a read-only harness mount in this environment and the task instructions explicitly said not to commit.
