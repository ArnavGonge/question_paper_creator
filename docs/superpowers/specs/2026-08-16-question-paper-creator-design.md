# Question Paper Creator V1 Design

## Overview

Build a hosted Streamlit web app for one non-technical teacher/client. The teacher opens a URL, enters a shared password, uploads chapter PDFs, selects extracted topics, defines question-paper sections, reviews the AI-generated draft, and downloads an editable Word document.

The app is session-based. It does not require local installation, teacher-side API setup, user accounts, or a database in v1.

## Goals

- Provide a simple hosted browser interface for generating question papers from chapter PDFs.
- Keep the teacher workflow guided and non-technical.
- Use AI for topic extraction and question generation.
- Ground generated questions in selected topics from uploaded source PDFs.
- Export an editable `.docx` matching the provided sample question paper layout.
- Allow basic structured editing before download.

## Non-Goals

- Multi-user accounts or roles.
- Saved paper history.
- Permanent file storage.
- Answer keys.
- PDF export.
- Multilingual generation.
- Full Word-style rich editing in the web app.
- Arbitrary teacher-created topics.
- Generated or embedded map images.
- Billing, analytics, or SaaS administration.

## Hosting And Delivery

V1 will be delivered as a hosted Streamlit app.

- The teacher receives a URL.
- The app is protected by one shared password.
- `APP_PASSWORD` and `OPENAI_API_KEY` are stored server-side as secrets.
- No executable or local installation is required.
- Streamlit Community Cloud is acceptable for a prototype or first delivery.
- Render, Railway, or similar hosting can be used if stronger privacy/control is required.

## Architecture

Recommended stack:

- UI and app runtime: Streamlit.
- Language: Python.
- PDF extraction: PyMuPDF or pdfplumber.
- AI: OpenAI API.
- Internal data format: structured JSON.
- Word export: python-docx initially, or docxtpl if a dedicated Word template is needed.
- Secrets: Streamlit secrets or host environment variables.
- Database: none in v1.
- Permanent object storage: none in v1.

Suggested modules:

- `app.py`: Streamlit UI, workflow state, and orchestration.
- `pdf_extractor.py`: extracts and cleans chapter text from uploaded PDFs.
- `topic_extractor.py`: calls AI and returns grouped topic JSON.
- `question_generator.py`: calls AI with selected topics, source text, and section blueprint.
- `validators.py`: validates topic output, paper blueprint, generated question JSON, counts, and marks.
- `docx_exporter.py`: renders the final Word document.
- `schemas.py`: shared typed structures for topics, sections, and generated questions.

## User Workflow

### 1. Password Gate

The teacher enters the shared password. The app compares it with `APP_PASSWORD` from secrets. If the password is incorrect, the app does not expose upload or generation controls.

### 2. Upload PDFs

The teacher uploads one or more chapter PDFs. The app shows uploaded filenames and extraction status, including basic page counts when available.

The app extracts text and keeps enough source metadata to link generated topics back to approximate source pages.

### 3. Select Topics

The AI extracts topics from the uploaded PDFs. Topics are shown as a checklist grouped by source PDF or chapter.

Each topic includes:

- Topic name.
- Short summary.
- Approximate source page range when available.

Teacher controls:

- Include topic.
- Exclude topic.

Teacher cannot:

- Rename topics.
- Add topics.
- Edit topic summaries.

This keeps generation grounded in the uploaded material and avoids unsupported question scope.

### 4. Configure Paper

The teacher fills paper metadata:

- Grade.
- Subject.
- Exam name.
- Date.
- Maximum marks.
- Time.

The teacher defines sections. Each section contains exactly one question type.

Section fields:

- Section label, such as `Section A`.
- Section heading, such as `Multiple Choice Based Questions`.
- Question type.
- Questions to generate.
- Questions to answer.
- Marks per question.
- Optional instruction.

Supported v1 question types:

- MCQ.
- Very Short Answer.
- Short Answer.
- Long Answer.
- Fill in the Blanks.
- True/False.
- Match the Following.
- Case Study.
- Map/Diagram Based Prompt.

The app calculates section marks as:

```text
questions_to_answer * marks_per_question
```

The app calculates total paper marks as the sum of section marks and warns if the total does not match the configured maximum marks.

### 5. Generate Draft

The app sends the selected source material and section blueprint to the AI. The AI returns structured JSON, not formatted prose.

The prompt must instruct the AI to generate only from selected topics and uploaded source text.

### 6. Review And Edit

The generated paper is displayed as structured editable fields.

The teacher can edit:

- Question text.
- MCQ options.
- Fill-in-the-blank statements.
- True/false statements.
- Match-the-following pairs.
- Case-study passage and sub-questions.
- Map/diagram prompt text.

The teacher can regenerate:

- The full paper.
- An individual section.

V1 does not include drag-and-drop ordering, rich text formatting, inline comments, or page-break controls.

### 7. Download DOCX

The app renders the reviewed paper into an editable `.docx` document. The app does not generate an answer key in v1.

## Generation Rules

- Output language is English only.
- The AI must generate only from selected topics and uploaded source text.
- Each section has exactly one question type.
- MCQs must include four options.
- Case-study sections must include a short passage and the configured number of sub-questions.
- Map/diagram sections generate prompt text only.
- The AI must not generate questions requiring unseen images unless the teacher explicitly created a map/diagram prompt section.
- No answer key is generated.
- No unsupported topics are introduced.
- Section and paper marks are calculated by the app, not trusted from the AI.

## Validation

The app validates AI output before allowing `.docx` export.

Validation should catch:

- Wrong number of questions in a section.
- Missing MCQ options.
- MCQs with fewer or more than four options.
- Missing case-study passage.
- Wrong number of case-study sub-questions.
- Empty or too-short question text.
- Malformed JSON.
- Unsupported question type.
- Section marks mismatch.
- Paper total mismatch.
- Obvious topic leakage outside selected source scope when detectable.

On validation failure, the app should show a clear error and offer:

- Regenerate section.
- Regenerate full paper.

## DOCX Output

The generated Word document should match the visual structure of `data/Grade 7 PA 1 QP 26-27.pdf`.

The document includes:

- Fixed school name/address header matching the sample.
- Centered exam name.
- Grade, subject, name blank, date, roll number, maximum marks, and time.
- Section labels, such as `Section A`.
- Section headings with marks summary, such as `Multiple Choice Based Questions (4x1=4)`.
- Optional choice notation, such as `Very Short Answer Based Questions (Any 2) (2x2=4)`.
- Numbered questions.
- MCQ options formatted compactly.
- Case-study passage followed by sub-questions.
- Map/diagram prompt text only.
- End marker `*****`.

The output format is `.docx` only.

## Data Retention

V1 is session-based.

- Uploaded PDFs are processed for the active session.
- Generated `.docx` files are downloaded by the teacher.
- The app does not promise history, recovery, or permanent storage.
- If the hosting platform writes temporary files during processing, they should be treated as temporary implementation details and cleaned up where practical.

## Risks And Mitigations

### AI Hallucination

Risk: The AI may generate questions outside the selected topics.

Mitigation: Generate from selected source chunks only, validate output structure, and require teacher review before export.

### PDF Extraction Quality

Risk: Text extraction from textbook PDFs can include headers, footers, captions, or layout artifacts.

Mitigation: Clean extracted text, preserve page metadata, and use topic summaries to help the teacher verify scope.

### DOCX Layout Differences

Risk: Word rendering may differ slightly across Microsoft Word, LibreOffice, and Google Docs.

Mitigation: Keep the layout simple and template-like. Use tables only where useful for header alignment. Treat final `.docx` as editable by the teacher.

### Secret Exposure

Risk: Exposing the OpenAI API key would allow misuse.

Mitigation: Keep the key server-side in Streamlit secrets or host environment variables. Never send it to the browser or embed it in downloadable artifacts.

### Single Password Sharing

Risk: A shared password is weaker than real accounts.

Mitigation: Acceptable for one-client v1. Upgrade to accounts only if usage expands.

## Acceptance Criteria

- A teacher can access the hosted app with the shared password.
- A teacher can upload multiple chapter PDFs.
- The app extracts readable text from the provided sample PDFs.
- The app generates a topic checklist from uploaded PDFs.
- The teacher can include/exclude topics without editing topic text.
- The teacher can create sections with one question type per section.
- The app calculates section marks and total marks.
- The app generates a structured question-paper draft from selected topics.
- The teacher can edit generated questions in structured fields.
- The app exports an editable `.docx`.
- The `.docx` follows the sample paper structure and contains no answer key.

## Open Implementation Decisions

- Choose PyMuPDF or pdfplumber after testing extraction quality on the sample PDFs.
- Choose python-docx or docxtpl after creating the first export prototype.
- Decide whether the first deployment target is Streamlit Community Cloud or a Docker host such as Render/Railway.
