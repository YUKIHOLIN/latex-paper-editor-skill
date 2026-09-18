# Paper workspace instructions

Use `paper.tex` as the default LaTeX root unless the user names another entry point.

When the user asks to generate, edit, or preview a paper:

1. Edit the relevant `.tex` source directly.
2. Run `python3 scripts/preview.py`.
3. If compilation succeeds, open `build/paper.pdf` beside the edited source in Codex.
4. If the request came from the PDF selection bridge, preserve the requested replacement and use the reported file and line span as the edit target.

The bridge runs with `python3 scripts/start_bridge.py` at `http://127.0.0.1:8765/`. It applies a selected replacement only after rechecking the source span, then rebuilds the preview. Do not commit generated files under `build/`.
