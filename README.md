# Codex Paper Workspace

This workspace provides a lightweight PDF.js selection bridge for LaTeX papers. The Overleaf Toolkit checkout lives separately at `/mnt/c/Users/Yukiho/overleaf-toolkit`; it is optional and is only needed when you want to run a local Overleaf Community Edition server.

## Preview a paper

From this directory:

```bash
python3 scripts/preview.py
```

The script writes `build/paper.pdf`. It compiles into a temporary directory first, so a failed build preserves the previous good PDF.

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

## Tests

```bash
python3 -m unittest discover -s tests -v
```
