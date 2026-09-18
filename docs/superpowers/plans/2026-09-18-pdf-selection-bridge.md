# PDF Selection Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight local PDF.js selection bridge that maps selected rendered text to LaTeX source candidates, supports Codex-led edits, and previews the updated PDF.

**Architecture:** A Python standard-library bridge serves a browser viewer and JSON matching endpoint. The matcher searches `.tex` files using exact, normalized, and substring text, while optional `paper:id` markers disambiguate macro-heavy passages. The bridge rechecks and applies confirmed replacements, then invokes the repository-local LaTeX wrapper.

**Tech Stack:** Python 3 standard library, `unittest`, HTML/CSS/JavaScript, PDF.js loaded by the browser, LaTeX/Tectonic or TeX Live.

**Spec:** `docs/superpowers/specs/2026-09-18-pdf-selection-bridge-design.md`

## Global Constraints

- Keep manuscripts, scripts, templates, and bridge assets in this repository.
- The bridge may mutate `.tex` only after a source candidate is selected and its contents are rechecked.
- Ambiguous or unmatched selections must be reported without choosing a source location automatically.
- Build artifacts stay under `build/` and are ignored by git.

### Task 1: Source matcher and smoke-test manuscript

**Files:**
- Create: `paper.tex`
- Create: `bridge/__init__.py`
- Create: `bridge/matcher.py`
- Create: `tests/test_matcher.py`

**Interfaces:**
- `find_matches(root: Path, selected_text: str) -> list[dict]`
- Each result contains `file`, `startLine`, `endLine`, `sourceText`, and `confidence`.

- [ ] **Step 1: Write the failing tests** for exact matches, normalized whitespace, no matches, and ambiguity.
- [ ] **Step 2: Run `python -m unittest tests/test_matcher.py -v` and verify the matcher import/behavior fails.
- [ ] **Step 3: Implement line-preserving exact and normalized matching, ignoring comments and TeX commands only for the normalized comparison.
- [ ] **Step 4: Run the matcher tests and verify they pass.
- [ ] **Step 5: Add a minimal `paper.tex` containing a uniquely matchable sample sentence and a `paper:id` marker example.

### Task 2: Local JSON bridge server

**Files:**
- Create: `bridge/server.py`
- Create: `tests/test_server.py`

**Interfaces:**
- `GET /` serves the viewer.
- `GET /api/status` returns `{pdf, sourceRoot}`.
- `POST /api/match` accepts `{selectedText, page}` and returns `{matches}`.
- `POST /api/preview` accepts `{selectedText, replacementText}` and returns matches without writing files.

- [ ] **Step 1: Write failing HTTP-handler tests using an in-process temporary directory.
- [ ] **Step 2: Run the server tests and verify endpoint failures.
- [ ] **Step 3: Implement a loopback-only `ThreadingHTTPServer` with JSON parsing, CORS restricted to the local origin, and safe path handling.
- [ ] **Step 4: Run server tests and verify unmatched/ambiguous responses.

### Task 3: PDF.js selection viewer

**Files:**
- Create: `bridge/web/index.html`
- Create: `bridge/web/app.js`
- Create: `bridge/web/styles.css`

- [ ] **Step 1: Add a viewer layout with PDF canvas, selection text area, replacement text area, match results, and an “Open in Codex” instruction panel.
- [ ] **Step 2: Load PDF.js from a pinned CDN module and render `../build/paper.pdf` through the local server.
- [ ] **Step 3: Capture `window.getSelection().toString()` from the PDF text layer and submit it to `/api/preview`.
- [ ] **Step 4: Render candidate file and line spans, confidence, and a copyable Codex prompt; do not perform source writes in JavaScript.
- [ ] **Step 5: Add a direct-PDF fallback message when PDF.js cannot load.

### Task 4: Preview command and workflow documentation

**Files:**
- Create: `scripts/preview.py`
- Create: `scripts/start_bridge.py`
- Create: `README.md`
- Create: `.gitignore`
- Modify: `bridge/server.py`

- [ ] **Step 1: Add a preview command that calls the repository-local `scripts/compile_latex.py` wrapper and preserves the previous PDF on compile failure.
- [ ] **Step 2: Add a bridge launcher serving the workspace on `127.0.0.1:8765`.
- [ ] **Step 3: Document the daily workflow, Codex edit prompts, marker syntax, repository-local compiler, and selection limitations.
- [ ] **Step 4: Run the full test suite, compile `paper.tex`, and verify `build/paper.pdf`.
- [ ] **Step 5: Commit the completed bridge setup.
