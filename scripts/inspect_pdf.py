#!/usr/bin/env python3
"""Inspect PDF text spans and embedded font metadata from the local project."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bridge.pdf_inspector import PdfInspectionError, inspect_pdf


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF path")
    parser.add_argument("--page", type=int, default=1, help="1-based page number")
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
        help="optional PDF-coordinate selection rectangle",
    )
    args = parser.parse_args()
    try:
        report = inspect_pdf(args.pdf, page_number=args.page, bbox=args.bbox)
    except PdfInspectionError as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
