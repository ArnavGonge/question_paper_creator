# Paper Builder UX Overhaul Design

## Summary

Redesign the existing Streamlit wizard as a friendly, guided paper-building workflow while preserving the current PDF extraction, topic extraction, AI generation, validation, and Word export pipeline. The work also makes section configuration the single source of truth for total marks, adds complete section lifecycle controls, and prevents technical error details from reaching end users.

## Goals

- Make the six-step workflow easier to scan, understand, and recover within.
- Keep the interface neutral and suitable for schools other than the current default school.
- Calculate the paper total directly from its sections everywhere it is used.
- Let users add, reorder, and delete sections without creating invalid paper state.
- Show users concise recovery guidance while retaining full diagnostics in server logs.
- Preserve successful work when a recoverable operation fails.

## Non-Goals

- Replacing Streamlit with a separate frontend and API.
- Changing the AI provider or the core question-generation strategy.
- Adding user accounts, persistent projects, or database storage.
- Reworking the generated Word document beyond the calculated total and any presentation changes required by that total.

## Product Structure

The app remains a six-step wizard:

1. Upload PDFs
2. Topics
3. Paper Details
4. Question Sections
5. Generate and Review
6. Download Word Document

The sidebar remains the primary progress indicator. Completed, current, available, and locked steps receive distinct but restrained states. Each main step uses a consistent layout:

- Step title and compact status summary
- Main task area
- Validation next to the field or action it concerns
- Clear primary action
- Consistent Back and Continue navigation

The wizard must remain usable at narrow viewport widths. Multi-column controls collapse before labels or values become cramped.

## Visual Direction

The interface uses a neutral light workspace, white editing surfaces, charcoal text, and teal for primary actions. Amber communicates guidance or incomplete work, red communicates blocking errors, and green communicates successful completion. Color is supplementary; labels and icons must communicate the same state without relying on color alone.

Typography uses a clean system sans-serif stack with moderate heading sizes, clear label hierarchy, and comfortable line height. The design relies on spacing, alignment, borders, and background contrast instead of decorative gradients, oversized headings, or excessive cards.

Reusable Streamlit presentation helpers and scoped CSS should provide:

- Application shell and content-width rules
- Step heading and status summary
- Status banners and inline field feedback
- Compact metric and summary treatments
- Section editor headers and action rows
- Consistent primary, secondary, and destructive actions
- Responsive layout adjustments

The app remains visually school-neutral. School details continue to affect the generated document, not the application chrome.

## Calculated Marks

Section configuration is the only source of truth for the grand total. For each section:

`section total = questions_to_answer * marks_per_question`

The paper total is the sum of every section total.

`PaperMetadata.max_marks` is removed as an independently editable field. The Paper Details step displays the current calculated total as a read-only summary and directs the user to Question Sections when it needs to change. The calculated value is used by:

- Wizard summaries and readiness checks
- AI generation prompts
- Generation and review summaries
- Validation diagnostics
- The Word document header

There is no paper-total mismatch validation because a second, independently editable total no longer exists. Existing constructors, defaults, tests, and serializers are migrated to the calculated model.

## Section Editor

Each section is presented as a compact, scannable editing panel. Its collapsed or header state shows:

- Section label
- Question type
- Number to answer
- Marks per question
- Calculated section subtotal

The editor supports:

- Adding a section with sensible defaults
- Moving a section up or down
- Deleting a section after confirmation
- Editing all existing section fields

Move controls are disabled at the first and last positions. Delete is disabled when only one section remains because a paper must contain at least one section. Labels are not silently rewritten when sections are reordered; the user's section labels remain part of the paper's identity.

Any section addition, edit, move, or deletion invalidates generated output when it changes the blueprint. The UI clearly states that regeneration is required rather than allowing stale output to proceed to download.

## Step-Level Improvements

### Upload PDFs

Show selected files as a concise list with file-level extraction outcomes. A failure in one file does not discard other documents successfully extracted in the same attempt. If every file in a new extraction attempt fails, retain the documents from the last successful extraction instead of replacing them with an empty list. Empty, unreadable, encrypted, or non-PDF content receives actionable guidance.

### Topics

Show topics as easy-to-scan selectable rows grouped by source document where practical. Display selected count prominently. Refreshing topics requires a deliberate action and invalidates generated output when the selection changes.

### Paper Details

Group school/exam metadata into predictable fields. Show calculated marks as read-only. Date parse failures should not silently replace the entered date; users receive field-level feedback and retain their input until corrected.

### Question Sections

Use the section editor described above, with a persistent paper-total summary and local validation. Prevent invalid answer/generation counts through control constraints where possible.

### Generate and Review

Present a readiness summary before generation. Separate paper-wide failures from section-specific failures. Keep section regeneration and manual editing available, and clearly mark generated output stale after upstream changes.

### Download Word Document

Show a compact final summary before download. Block export only for actionable validation failures and place the message beside the relevant next action.

## Error Handling and Diagnostics

Create a centralized error-reporting boundary for user-triggered operations. Each failure produces:

- A short, friendly user message describing what failed and the next useful action
- A generated reference ID visible to the user
- A structured server log entry containing that reference ID, operation context, and full exception traceback

Technical exception messages, stack traces, API payloads, keys, and internal implementation details are never rendered in the Streamlit interface. Server logs are the troubleshooting source available to the operator.

Known failures receive tailored messages, including:

- Missing server-side OpenAI configuration
- Corrupt, empty, encrypted, or unsupported PDF input
- Partial PDF extraction failure
- AI timeout, rate limiting, authentication, or unavailable service
- Invalid or incomplete AI JSON output
- Word export failure

Unexpected failures use a generic recovery message and reference ID. Logging must avoid document contents, API keys, passwords, and other secrets.

Successful state from earlier operations is retained when a failure is recoverable. Buttons show loading states and are protected from accidental duplicate operations using Streamlit's rerun/session-state behavior.

## Code Organization

The existing domain modules remain responsible for schemas, validation, generation, extraction, and export. The overhaul introduces narrowly scoped helpers instead of moving all behavior into custom components:

- UI theme and reusable presentation functions
- Section list operations such as move and delete
- Error classification, safe user messages, reference IDs, and logging

`app.py` remains the wizard coordinator but delegates presentation and state transformations to those helpers. Domain calculations stay in schema/domain code so prompts, UI, validation, and export all consume the same result.

## Testing

Unit and integration tests cover:

- Paper totals calculated only from sections
- Prompt and Word-header totals
- Section add, move, and delete behavior
- Protection of the final remaining section
- Generated-paper invalidation after blueprint changes
- User-safe error messages and server-side diagnostic logging
- Partial upload preservation
- Field and readiness validation
- Existing generation normalization and document export behavior

Run the complete pytest suite and Ruff checks. Use Streamlit's testing support for key wizard states where practical. Finally, start the application and smoke-test the workflow at desktop and narrow viewport widths, checking layout, navigation, empty states, validation, and section controls.

## Acceptance Criteria

- Users cannot create a mismatch between displayed maximum marks and section totals.
- The Word header always displays the calculated section total.
- Users can add, reorder, and delete sections, but cannot delete the last section.
- Deleting a section requires confirmation.
- Generated output cannot be downloaded after its inputs become stale.
- No raw exception or stack trace is shown in the app.
- Every unexpected user-facing failure includes a reference ID that appears in server logs with its traceback.
- The full existing test suite plus new behavior tests passes.
- The six-step workflow is visually coherent and usable on desktop and narrow screens.
