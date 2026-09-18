#!/usr/bin/env python3
"""Compile paper.tex into build/paper.pdf without destroying the last good preview."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
COMPILER = Path("/mnt/c/Users/Yukiho/.codex/plugins/cache/openai-bundled/latex/0.2.6/scripts/compile_latex.py")


def main() -> int:
    root = WORKSPACE / "paper.tex"
    build = WORKSPACE / "build"
    build.mkdir(exist_ok=True)
    output = build / "paper.pdf"
    with tempfile.TemporaryDirectory(prefix="paper-build-", dir=build) as staging:
        command = [sys.executable, str(COMPILER), str(root), "--output-directory", staging]
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
