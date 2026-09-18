#!/usr/bin/env python3
"""Compile one LaTeX root with tools available on the host PATH.

This deliberately small wrapper keeps preview compilation inside the project:
it does not import an agent installation or rely on a machine-specific path.
It uses ``latexmk`` when available (with rc files disabled), otherwise invokes
the requested TeX engine directly.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


ENGINE_FLAGS = {
    "pdflatex": "-pdf",
    "xelatex": "-xelatex",
    "lualatex": "-lualatex",
}


def build_command(root: Path, engine: str, output_directory: Path) -> list[str]:
    """Build a safe, non-interactive command for the available LaTeX tool."""
    latexmk = shutil.which("latexmk")
    if latexmk:
        return [
            latexmk,
            "-norc",
            ENGINE_FLAGS[engine],
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-synctex=1",
            f"-outdir={output_directory}",
            os.fspath(root),
        ]
    executable = shutil.which(engine)
    if executable is None:
        raise RuntimeError(
            f"Neither latexmk nor {engine} is available on PATH. "
            "Install TeX Live, MiKTeX, or MacTeX and retry."
        )
    return [
        executable,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-synctex=1",
        f"-output-directory={output_directory}",
        os.fspath(root),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tex_file", type=Path)
    parser.add_argument("--engine", choices=sorted(ENGINE_FLAGS), default="pdflatex")
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()

    root = args.tex_file.expanduser().resolve()
    output_directory = args.output_directory.expanduser().resolve()
    if not root.is_file():
        raise SystemExit(f"TeX file not found: {root}")
    output_directory.mkdir(parents=True, exist_ok=True)
    command = build_command(root, args.engine, output_directory)
    print("$", " ".join(command), flush=True)
    result = subprocess.run(command, cwd=root.parent, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
