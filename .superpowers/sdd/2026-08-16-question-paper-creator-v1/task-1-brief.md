### Task 1: Project Scaffold And Tooling

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `.streamlit/secrets.example.toml`
- Create: `src/qpc/__init__.py`
- Create: `tests/test_imports.py`

**Interfaces:**
- Produces: importable package `qpc`.
- Produces: dependency list for Streamlit, PDF extraction, OpenAI calls, DOCX export, validation, and tests.

- [ ] **Step 1: Create dependency and config files**

`requirements.txt`:

```text
streamlit==1.37.1
openai==1.99.1
pymupdf==1.24.9
python-docx==1.1.2
pydantic==2.8.2
pytest==8.3.2
ruff==0.5.7
```

`.streamlit/secrets.example.toml`:

```toml
APP_PASSWORD = "replace-with-a-client-password"
OPENAI_API_KEY = "sk-replace-with-real-key"
OPENAI_MODEL = "gpt-4.1-mini"
```

`.gitignore`:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.venv/
venv/
.env
.streamlit/secrets.toml
generated/
*.docx
```

`src/qpc/__init__.py`:

```python
"""Question Paper Creator application package."""
```

- [ ] **Step 2: Write the import smoke test**

`tests/test_imports.py`:

```python
def test_package_imports():
    import qpc

    assert qpc.__doc__
```

- [ ] **Step 3: Run test to verify scaffold**

Run:

```bash
PYTHONPATH=src pytest tests/test_imports.py -v
```

Expected: PASS.

- [ ] **Step 4: Run lint**

Run:

```bash
PYTHONPATH=src ruff check src tests
```

Expected: PASS.

- [ ] **Step 5: Commit when git exists**

Run only after initializing git:

```bash
git add requirements.txt .gitignore .streamlit/secrets.example.toml src/qpc/__init__.py tests/test_imports.py
git commit -m "chore: scaffold question paper app"
```

---

