# LaTeX Paper Editor Skill

This repository packages a portable agent skill and a lightweight PDF.js selection bridge for editing research papers in LaTeX. It works with Codex and can be adapted to Doubao, Kimi, Hermes, DeepSeek, Harness, and other agents that can load Markdown instructions and run local commands.

完整的安装、平台支持、编译软件和字体说明见 [USAGE.md](USAGE.md)。

The Overleaf Toolkit checkout used during development is separate from this project. It is optional and only needed when running a local Overleaf Community Edition server.

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

For Chinese text, include `ctex`, `xeCJK`, or `fontspec` in the LaTeX preamble. The preview script automatically selects XeLaTeX for non-ASCII source and prints the first available CJK font from a broad fallback list. Use [`templates/cjk-font-fallback.tex`](templates/cjk-font-fallback.tex) with `fontspec`/`xeCJK` when a document needs explicit cross-platform font selection. No package can guarantee every Unicode glyph without a font that contains that glyph, so the script reports missing CJK font coverage before compilation.

## Start the selection bridge

```bash
python3 scripts/start_bridge.py
```

Open <http://127.0.0.1:8765/>. The viewer renders the PDF with PDF.js, lets you select text, and searches the LaTeX source. It never writes source files.

After entering replacement text, click **Find source location**, then **Copy Codex edit prompt**. Paste that prompt into the Codex chat. Codex can then edit the indicated `.tex` lines, run `python3 scripts/preview.py`, and reopen the updated PDF side-by-side with the source.

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

PDF text is not a perfect source map. Hyphenation, ligatures, generated text, and TeX macros can prevent exact matching. The bridge reports all candidates when a selection is ambiguous and does not make an automatic edit. SyncTeX files are copied when the compiler produces them, so a SyncTeX-capable editor can provide click-to-source navigation as a complement to this viewer.

An input PDF without its original LaTeX source cannot be edited as a source-backed manuscript. Use an extracted transcript only for bridge verification, or provide the original source project. Direct PDF overlays are preview-only and require an embedded CJK-capable font for Chinese replacements.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Repository layout

- `skills/latex-paper-editor/SKILL.md` — portable agent instructions.
- `bridge/` — local PDF.js viewer and source matcher.
- `scripts/preview.py` — compile a preview PDF.
- `scripts/start_bridge.py` — serve the selection bridge on localhost.
- `scripts/font_diagnostics.py` — detect CJK text and available fallback fonts.
- `templates/cjk-font-fallback.tex` — dynamic XeLaTeX font fallback chain.
- `installer.py` / `install.py` — install the skill into an agent skill directory.
- `paper.tex` — smoke-test manuscript.
