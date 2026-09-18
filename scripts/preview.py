#!/usr/bin/env python3
"""Compile paper.tex into build/paper.pdf without destroying the last good preview."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import re
import os
from pathlib import Path

try:
    from scripts.font_diagnostics import diagnostic
except ModuleNotFoundError:  # direct execution: `python3 scripts/preview.py`
    from font_diagnostics import diagnostic


WORKSPACE = Path(__file__).resolve().parents[1]
DOCUMENTCLASS_RE = re.compile(r"(?m)^(?P<line>\s*\\documentclass(?:\[[^\n]*\])?\{[^\n]*\}\s*\n?)")


def compiler_script_path(workspace: Path = WORKSPACE) -> Path:
    """Return the repository-local compiler wrapper used for previews.

    ``LATEX_COMPILER_HELPER`` is an optional escape hatch for hosts that want
    to provide a newer wrapper, but a fresh clone always has a working default
    inside this repository.  No Codex- or machine-specific path is assumed.
    """
    override = os.environ.get("LATEX_COMPILER_HELPER")
    if override:
        return Path(override).expanduser().resolve()
    return workspace / "scripts" / "compile_latex.py"


def choose_engine(source: str) -> str:
    """Choose XeLaTeX for Unicode source, otherwise pdfLaTeX."""
    return "xelatex" if any(ord(char) > 127 for char in source) else "pdflatex"


def cjk_support_error(source: str) -> str | None:
    """Explain how to configure CJK text before compilation can succeed."""
    if not any(ord(char) > 127 for char in source):
        return None
    if re.search(r"ctex|xeCJK|fontspec", source, re.IGNORECASE):
        return None
    return "Unicode/CJK text detected. Add ctex, xeCJK, or fontspec to the LaTeX preamble before compiling."


def add_cjk_preamble(source: str) -> str:
    """Add the repository's CJK setup when Unicode text lacks one.

    The insertion is deliberately after ``\\documentclass`` so XeLaTeX can
    load packages normally.  If a document has no class declaration, leave it
    untouched and let the existing actionable error explain the problem.
    """
    if cjk_support_error(source) is None:
        return source
    match = DOCUMENTCLASS_RE.search(source)
    if match is None:
        return source
    preamble = (
        "\\usepackage{fontspec}\n"
        "\\usepackage{xeCJK}\n"
        "\\input{skills/latex-paper-editor/assets/cjk-font-fallback.tex}\n"
    )
    return source[: match.end()] + preamble + source[match.end() :]


def main() -> int:
    root = WORKSPACE / "paper.tex"
    source = root.read_text(encoding="utf-8")
    engine = choose_engine(source)
    font_info = diagnostic(source)
    if font_info["hasCjk"]:
        print(font_info["message"])
    original_source = source
    repaired_source = add_cjk_preamble(source)
    if repaired_source != source:
        root.write_text(repaired_source, encoding="utf-8")
        source = repaired_source
        print("Added the repository CJK font preamble for this Unicode source.")
    configuration_error = cjk_support_error(source)
    if configuration_error:
        print(configuration_error, file=sys.stderr)
        print("Preview compilation stopped; the previous PDF was preserved.", file=sys.stderr)
        return 2
    build = WORKSPACE / "build"
    build.mkdir(exist_ok=True)
    output = build / "paper.pdf"
    with tempfile.TemporaryDirectory(prefix="paper-build-", dir=build) as staging:
        compiler = compiler_script_path()
        command = [sys.executable, str(compiler), str(root), "--engine", engine, "--output-directory", staging]
        print("$", " ".join(command))
        result = subprocess.run(command, cwd=WORKSPACE)
        staged_pdf = Path(staging) / "paper.pdf"
        if result.returncode != 0 or not staged_pdf.exists():
            if source != original_source:
                root.write_text(original_source, encoding="utf-8")
            print("Preview compilation failed; the previous PDF was preserved.", file=sys.stderr)
            return result.returncode or 1
        shutil.copy2(staged_pdf, output)
        for suffix in (".synctex.gz", ".log", ".aux", ".out"):
            candidate = Path(staging) / f"paper{suffix}"
            if candidate.exists():
                shutil.copy2(candidate, build / candidate.name)
    print(f"Preview written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
