### Task 9: Deployment Notes And Final Verification

**Files:**
- Create: `README.md`
- Create: `docs/deployment.md`

**Interfaces:**
- Consumes: completed app from prior tasks.
- Produces: operator instructions for local run, secrets, tests, and hosted deployment.

- [ ] **Step 1: Create README**

`README.md`:

```markdown
# Question Paper Creator

Hosted Streamlit app for generating editable Word question papers from uploaded chapter PDFs.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
PYTHONPATH=src streamlit run app.py
```

Set real values in `.streamlit/secrets.toml` before using AI generation.

## Tests

```bash
PYTHONPATH=src pytest -v
PYTHONPATH=src ruff check src tests app.py
```

## V1 Limits

- Single shared password.
- No saved history.
- No answer key.
- English only.
- DOCX export only.
```

- [ ] **Step 2: Create deployment doc**

`docs/deployment.md`:

```markdown
# Deployment

## Streamlit Community Cloud

1. Push the repository to GitHub.
2. Create a Streamlit Community Cloud app from the repository.
3. Set the main file path to `app.py`.
4. Add secrets:

```toml
APP_PASSWORD = "client-password"
OPENAI_API_KEY = "real-openai-key"
OPENAI_MODEL = "gpt-4.1-mini"
```

5. Deploy the app.
6. Share the Streamlit app URL and password with the client.

## Render Or Railway

Use this route when stronger privacy or operational control is needed. Configure the same environment variables as secrets and run:

```bash
PYTHONPATH=src streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

## Operational Notes

- Rotate `APP_PASSWORD` if the URL is shared beyond the intended client.
- Track OpenAI API usage in the OpenAI dashboard.
- Do not commit `.streamlit/secrets.toml`.
- The app is session-based and does not preserve generated papers.
```

- [ ] **Step 3: Run full verification**

```bash
PYTHONPATH=src pytest -v
PYTHONPATH=src ruff check src tests app.py
```

Expected: PASS.

- [ ] **Step 4: Manual local smoke test**

Run:

```bash
PYTHONPATH=src streamlit run app.py
```

Manual checks:

- Password screen appears.
- Correct password unlocks the app.
- `data/gees101 Geographical Diversity of India.pdf` uploads.
- `data/gees102 Understanding the Weather.pdf` uploads.
- Text extraction reports page counts.
- Topic extraction works when `OPENAI_API_KEY` is configured.
- Blueprint marks total displays correctly.
- Paper generation works when topics are selected.
- Review fields appear.
- DOCX downloads and opens in Word or LibreOffice.

- [ ] **Step 5: Commit when git exists**

```bash
git add README.md docs/deployment.md
git commit -m "docs: add setup and deployment instructions"
```

---

## Self-Review Checklist

- Spec coverage: The plan includes hosted Streamlit delivery, single password, PDF upload/extraction, AI topic checklist, section blueprint, structured editing, no answer key, English-only generation, DOCX export, and deployment docs.
- Placeholder scan: The plan contains concrete files, commands, and code blocks for each implementation task.
- Type consistency: The interfaces introduced in `schemas.py` are consumed by validators, AI modules, DOCX export, demo defaults, and Streamlit using the same class and function names.
- Scope control: The plan does not add accounts, persistence, answer keys, PDF export, multilingual generation, or rich document editing.
