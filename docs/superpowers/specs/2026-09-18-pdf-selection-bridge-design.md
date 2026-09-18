# PDF Selection Bridge for LaTeX Papers

## Goal

Provide a lightweight local paper workspace where Codex can edit LaTeX source, compile a preview PDF, and use a PDF.js-based side panel to capture selected text plus source context for precise edits.

## Scope

- Keep manuscripts and generated previews under the repository root (`paper.tex` and `build/`).
- Keep every project script, bridge asset, template, and skill file in this repository; an Overleaf Toolkit checkout is not required.
- Support a local PDF.js viewer that displays the latest preview PDF and captures text selections.
- Map selections to LaTeX source by exact/normalized text matching, with optional stable region markers for ambiguous or macro-heavy text.
- Expose a local bridge endpoint that accepts a proposed replacement and returns the source file and line span to edit.
- Document Codex commands for editing, compiling, and opening source/PDF side-by-side.

## Non-goals

- Reimplement the Overleaf web application.
- Guarantee perfect PDF-to-source mapping for every TeX construct; generated text, hyphenation, ligatures, and macro expansion can make exact mapping impossible.
- Replace arbitrary PDF text without a source-backed `.tex` project.

## Architecture

The workspace contains a canonical `paper.tex`, optional section files, a `build/` directory for generated artifacts, and a small Python bridge. The bridge serves a local HTML/PDF.js viewer, extracts the current selection in the browser, searches the source using exact, normalized, and substring text, and returns candidate source ranges. After the user confirms a candidate, the bridge rechecks the source, patches the LaTeX file, runs the preview compiler, and refreshes the PDF.

Stable `paper:id` / `paper:end` markers are supported for paragraphs that cannot be matched safely from rendered text. SyncTeX output is enabled whenever the installed compiler supports it, providing click-to-source navigation as a complementary feature.

## Components

1. `paper.tex` — minimal smoke-test manuscript and default compilation root.
2. `bridge/server.py` — local HTTP server and JSON endpoints for viewer assets, source matching, and replacement preview.
3. `bridge/web/index.html` — PDF.js viewer UI with text selection capture and replacement text box.
4. `scripts/preview.py` — invokes the repository-local compiler wrapper and writes artifacts to `build/`.
5. `README.md` — setup, daily workflow, limitations, and Codex prompt examples.
6. `.gitignore` — excludes build output, caches, and local environment files.

## Data flow

1. User runs the preview command; `paper.tex` is compiled to `build/paper.pdf`.
2. User starts the local bridge; the viewer loads `build/paper.pdf`.
3. User selects PDF text and enters a replacement.
4. The browser sends `{selectedText, replacementText, page}` to `/api/match`.
5. The bridge searches source files and returns candidate `{file, startLine, endLine, sourceText, confidence}` records.
6. The bridge applies the requested edit to the selected candidate, recompiles, and refreshes the PDF; optional Git publishing uses the repository's configured remote.

## Error handling

- If no candidate matches, the viewer returns a clear message asking the user to identify the source file or add a stable marker.
- If multiple candidates match, the viewer lists candidates and does not modify files automatically.
- The bridge rechecks the selected source span before writing and refuses stale or unsafe paths.
- Compilation failures preserve the previous PDF and expose the compiler log path.

## Verification

- Smoke-test the bridge API against the sample sentence in `paper.tex`.
- Compile the sample paper and verify `build/paper.pdf` exists.
- Open the source and PDF in Codex panels.
- Test an unmatched selection and an ambiguous selection without modifying source.
