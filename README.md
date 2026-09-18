# LaTeX Paper Editor Skill

This repository packages a portable agent skill and a lightweight PDF.js selection bridge for editing research papers in LaTeX. It works with Codex and can be adapted to Doubao, Kimi, Hermes, DeepSeek, Harness, and other agents that can load Markdown instructions and run local commands.

完整的安装、平台支持、编译软件和字体说明见 [USAGE.md](USAGE.md)。

This repository is the complete project source for the skill and bridge. It does not require a separate Overleaf checkout. A local LaTeX distribution and CJK fonts are host prerequisites, selected through the system `PATH`.

## Public browser workspace

The ready-to-use beginner interface is available at:

<https://latex-paper-editor.netlify.app>

Upload a PDF and its matching `.tex` file, select text in the PDF, enter the
replacement, choose the source candidate, and apply the annotation. The site
processes the files in the browser and downloads the updated `.tex`; it does
not send manuscript contents to Netlify. Automatic XeLaTeX recompilation is
available through the local bridge described below.

The repository and the browser workspace are intentionally kept as one
distribution. Installing the skill from this repository gives an AI agent the
instructions and local tools; opening the URL gives beginners a zero-install
preview/edit surface.

## Install the skill

Clone or download this repository, then install the skill into the agent's skill directory:

```bash
python3 install.py --target ~/.codex/skills
```

For another agent, replace the target with that agent's skills directory. If the agent has no skill directory, copy `skills/latex-paper-editor/SKILL.md` into its project instructions or system prompt and keep this repository available as the project toolkit.

Typical locations include:

| Agent | Target example |
| --- | --- |
| Codex | `~/.codex/skills` or `.codex/skills` |
| Cursor | `~/.cursor/skills` or `.cursor/skills` |
| Hermes / DeepSeek / Harness | Their configured agent skills directory |
| Doubao / Kimi | Project instructions or a custom tool/skill directory |

The installer copies only `skills/latex-paper-editor`; it does not modify the host agent configuration or upload files.

## Preview a paper

From this directory:

```bash
python3 scripts/preview.py
```

The script writes `build/paper.pdf`. It compiles into a temporary directory first, so a failed build preserves the previous good PDF.

For Chinese text, include `ctex`, `xeCJK`, or `fontspec` in the LaTeX preamble. The preview script automatically selects XeLaTeX for non-ASCII source, prints the first available CJK font from a broad fallback list, and adds the repository CJK preamble after `\documentclass` when an annotation introduces Chinese into a source that lacks one. Use [`templates/cjk-font-fallback.tex`](templates/cjk-font-fallback.tex) with `fontspec`/`xeCJK` when a document needs explicit cross-platform font selection. No package can guarantee every Unicode glyph without a font that contains that glyph, so the script reports missing CJK font coverage before compilation.

## Start the selection bridge

```bash
python3 scripts/start_bridge.py
```

Open <http://127.0.0.1:8765/>. The viewer renders the PDF with PDF.js, lets you select text, and searches the LaTeX source. After you choose a candidate and replacement, **Apply annotation** rechecks and writes that source span, rebuilds the PDF, and can publish to the configured Git remote.

After entering replacement text, click **Find source location**, choose the source candidate, and click **Apply annotation**. The bridge edits the indicated `.tex` lines, runs the preview compiler, and refreshes the PDF. Publishing is opt-in: enable **Also commit and push to GitHub** only when you explicitly want a remote commit.

## Netlify website

The `site/` directory is a Netlify-ready browser workspace. It asks the user for a PDF and its matching `.tex`, renders the PDF with PDF.js, maps selected text to source lines, applies an in-browser source edit, and downloads the updated `.tex`. Files are not uploaded to Netlify. Deploy the static site with Netlify's dashboard using `site` as the publish directory, or with the Netlify CLI:

```bash
npx netlify-cli deploy --dir=site --prod
```

The public static site cannot run XeLaTeX or write arbitrary server files. Use the local bridge in this repository when the updated PDF must be recompiled immediately.

When PyMuPDF is installed (`python3 -m pip install -r requirements.txt`), selecting PDF text also shows the decoded Unicode span, BaseFont/family, Type0/CID subtype, embedded-font status and extracted font file, size, color, style flags, bounding box, and block/line/span content location. PDF.js remains the renderer and selection layer; it does not provide reliable font extraction or CID writing.

## Codex workflow

Useful requests include:

- “Compile `paper.tex` and open the PDF beside the source.”
- “In `sections/introduction.tex`, replace lines 18–19 with: …, then rebuild the preview.”
- “Add a stable `paper:id` marker around this paragraph so PDF selection remains unambiguous.”

For macro-heavy text, add markers around the source region:

```tex
% paper:id=discussion-limitations
The sentence or paragraph to edit.
% paper:end=discussion-limitations
```

## Limitations

PDF text is not a perfect source map. Hyphenation, ligatures, generated text, and TeX macros can prevent exact matching. The bridge reports all candidates when a selection is ambiguous and waits for the user to choose one before editing. SyncTeX files are copied when the compiler produces them, so a SyncTeX-capable editor can provide click-to-source navigation as a complement to this viewer.

An input PDF without its original LaTeX source cannot be edited as a source-backed manuscript. Use an extracted transcript only for bridge verification, or provide the original source project. Direct PDF overlays are preview-only and require an embedded CJK-capable font for Chinese replacements. The recommended write-back path is source-backed: update `.tex` and recompile so XeLaTeX/xeCJK performs valid CID and ToUnicode encoding. PyMuPDF can inspect and extract embedded fonts but should not blindly rewrite arbitrary Type0 content streams; pdf-lib is useful for page/object operations but does not provide equivalent CID/ToUnicode font mapping. PDF.js renders and selects text but does not write embedded fonts.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Repository layout

- `skills/latex-paper-editor/SKILL.md` — portable agent instructions.
- `bridge/` — local PDF.js viewer and source matcher.
- `scripts/preview.py` — compile a preview PDF.
- `scripts/compile_latex.py` — repository-local wrapper that selects `latexmk` or a TeX engine from `PATH`.
- `scripts/inspect_pdf.py` — inspect PDF text, fonts, CID mapping, and geometry from the command line.
- `scripts/start_bridge.py` — serve the selection bridge on localhost.
- `requirements.txt` — optional PyMuPDF dependency for PDF diagnostics.
- `scripts/font_diagnostics.py` — detect CJK text and available fallback fonts.
- `templates/cjk-font-fallback.tex` — dynamic XeLaTeX font fallback chain.
- `installer.py` / `install.py` — install the skill into an agent skill directory.
- `paper.tex` — smoke-test manuscript.
