---
name: latex-paper-editor
description: Edit research papers in LaTeX, compile preview PDFs, map PDF selections back to source lines, and iterate on manuscripts. Use when a user asks to write, revise, format, compile, or inspect a research paper or LaTeX project.
---

# LaTeX Paper Editor

## Distribution and beginner entry point

This skill is distributed from the single canonical repository:

<https://github.com/YUKIHOLIN/latex-paper-editor-skill>

When a user asks to install or use this skill, keep this repository as the
project toolkit and install `skills/latex-paper-editor` into the host agent's
skill directory. The matching no-install browser workspace is available at:

<https://latex-paper-editor.netlify.app>

For a beginner who has a PDF and its matching `.tex` file, open the browser
workspace, upload both files, select text in the PDF, enter the replacement,
find and choose the source candidate, then apply the annotation. The browser
workspace edits and downloads the `.tex` file locally. It does not upload
paper contents to Netlify. To rebuild a PDF automatically after an edit, run
the local bridge from the cloned repository with `python3 scripts/start_bridge.py`;
the public static site cannot run XeLaTeX.

Use this skill for paper work when the project contains `paper.tex`, another `.tex` root, or the bridge files from this repository.

## Workflow

1. Identify the LaTeX root file. Prefer `paper.tex`; otherwise use the file named by the user or the file containing `\\documentclass`.
2. Preserve the user's source structure and bibliography setup.
3. For a source edit, make the smallest direct change in the relevant `.tex` file.
4. Compile a preview after edits:

   ```bash
   python3 scripts/preview.py
   ```

5. Report compiler errors with the source file and line information. Do not claim a PDF is current if compilation failed.
6. Open the generated `build/paper.pdf` beside the edited source when the host agent supports file panels.

For Chinese or other non-ASCII text, use XeLaTeX and configure the preamble with `ctex`, `xeCJK`, or `fontspec`. The preview script detects Unicode text, reports available CJK fallback fonts, and automatically adds the repository CJK preamble after `\documentclass` when an annotation introduces Unicode into a source that lacks one. If no document class is present, report the actionable configuration error instead of claiming the PDF is current.

For explicit cross-platform font selection, load the bundled `assets/cjk-font-fallback.tex` after `fontspec` and `xeCJK`. It checks these families in order: Noto Serif/Sans CJK, Source Han Serif/Sans, Microsoft YaHei, SimSun, and Droid Sans Fallback. The same fallback file is included in the installed skill, so it remains available after downloading or installing this repository.

No font package can contain every Unicode glyph on every host. When a required character is outside the installed fonts' coverage, stop and report the missing font instead of silently producing blank glyphs.

## PDF selection bridge

If this repository's bridge is available, start it with:

```bash
python3 scripts/start_bridge.py
```

Open `http://127.0.0.1:8765/`. A user can select rendered text, enter a replacement, choose the source candidate, and click **Apply annotation**. The bridge rechecks the source span, edits the `.tex` file, recompiles the PDF, and can commit and push the change to the configured GitHub remote.

The bridge writes only the selected `.tex` span after rechecking its current contents. It can return multiple candidates; choose the correct candidate before applying. When there is no match or the source changed after selection, stop and ask the user to select again or identify the source region. Stable markers can disambiguate macro-heavy passages:

If PyMuPDF is installed, the browser also reports the selected PDF span's decoded Unicode text, BaseFont/family, Type0/CID encoding, embedded font extraction path, size, color, style flags, bounding box, and block/line/span location. Treat this as diagnostics: write replacements through `.tex` and recompile so the TeX engine performs valid font fallback and CID encoding. Do not claim that PDF.js alone can rewrite arbitrary embedded Type0 fonts.

```tex
% paper:id=unique-region-name
Text to edit.
% paper:end=unique-region-name
```

If the input is a PDF without its original `.tex` source, do not present PDF overlay edits as source-backed LaTeX edits. Create an extracted transcript only for matching tests, or ask for the source project. Direct PDF redaction/insertion must embed a CJK-capable font and should be labeled as a preview-only PDF edit.

## Paper editing rules

- Preserve citations, labels, cross-references, equations, and macros unless the user asks to change them.
- Keep generated files under `build/`; do not edit generated PDF or auxiliary files.
- Treat PDF text matching as approximate because of macros, hyphenation, ligatures, and line wrapping.
- For broad rewrites, explain the affected section and compile the preview once after the complete edit.
- For bibliographies or indexes, use the project's existing build instructions when the simple preview command is insufficient.

## Cross-agent behavior

If the host does not support a native skill directory, load this file as an agent instruction and run the same commands from the project root. The workflow requires only Python 3 and an available LaTeX installation; PDF.js is loaded by the local browser viewer.
