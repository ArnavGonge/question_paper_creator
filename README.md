# Question Paper Creator

Hosted Streamlit app for generating editable Word question papers from uploaded chapter PDFs.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
PYTHONPATH=src .venv/bin/python -m streamlit run app.py
```

Set real values in `.streamlit/secrets.toml` before using AI generation.

## Tests

```bash
PYTHONPATH=src .venv/bin/python -m pytest -v
PYTHONPATH=src .venv/bin/ruff check src tests app.py
```

## V1 Limits

- Single shared password.
- No saved history.
- No answer key.
- English only.
- DOCX export only.
