#!/usr/bin/env python3
"""Compile paper.tex into build/paper.pdf without destroying the last good preview."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import re
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
COMPILER = Path("/mnt/c/Users/Yukiho/.codex/plugins/cache/openai-bundled/latex/0.2.6/scripts/compile_latex.py")


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


def main() -> int:
    root = WORKSPACE / "paper.tex"
    source = root.read_text(encoding="utf-8")
    engine = choose_engine(source)
    configuration_error = cjk_support_error(source)
    if configuration_error:
        print(configuration_error, file=sys.stderr)
        print("Preview compilation stopped; the previous PDF was preserved.", file=sys.stderr)
        return 2
    build = WORKSPACE / "build"
    build.mkdir(exist_ok=True)
    output = build / "paper.pdf"
    with tempfile.TemporaryDirectory(prefix="paper-build-", dir=build) as staging:
        command = [sys.executable, str(COMPILER), str(root), "--engine", engine, "--output-directory", staging]
        print("$", " ".join(command))
        result = subprocess.run(command, cwd=WORKSPACE)
        staged_pdf = Path(staging) / "paper.pdf"
        if result.returncode != 0 or not staged_pdf.exists():
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
