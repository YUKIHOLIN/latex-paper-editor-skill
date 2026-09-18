"""Inspect PDF text spans, fonts, geometry, and Unicode extraction metadata.

PyMuPDF is intentionally optional.  The LaTeX source bridge continues to work
without it; installing ``PyMuPDF`` enables this richer diagnostic endpoint.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class PdfInspectionError(RuntimeError):
    """Raised when PDF inspection cannot be completed."""


def _load_fitz():
    try:
        import fitz  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on host setup
        raise PdfInspectionError(
            "PDF font inspection needs PyMuPDF. Install it with: python3 -m pip install PyMuPDF"
        ) from exc
    return fitz


def _family(base_font: str, displayed_font: str) -> str:
    value = base_font or displayed_font or "unknown"
    value = value.split("+", 1)[-1]
    value = re.sub(r"-(Identity-[HV]|Uni[A-Za-z0-9-]+)$", "", value)
    return value or displayed_font or "unknown"


def _color(value: int, alpha: int) -> dict[str, Any]:
    red = (value >> 16) & 255
    green = (value >> 8) & 255
    blue = value & 255
    return {
        "space": "rgb",
        "value": [red, green, blue],
        "hex": f"#{red:02x}{green:02x}{blue:02x}",
        "alpha": alpha,
    }


def _font_records(document: Any) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for page_number in range(document.page_count):
        page = document[page_number]
        for item in page.get_fonts(full=True):
            xref, ext, subtype, base_font, resource, encoding, refer = item[:7]
            base_font = str(base_font or "")
            resource = str(resource or "")
            encoding = str(encoding or "")
            subtype = str(subtype or "")
            family = _family(base_font, base_font)
            key_values = {resource, base_font, base_font.split("+", 1)[-1], family}
            if any(key in records for key in key_values):
                continue
            content = b""
            extracted_ext = ext
            try:
                extracted = document.extract_font(xref)
                extracted_ext = extracted[1] or ext
                content = extracted[3] or b""
            except (RuntimeError, ValueError, IndexError):
                pass
            records.update(
                {
                    key: {
                        "xref": xref,
                        "extension": extracted_ext,
                        "subtype": subtype,
                        "baseFont": base_font,
                        "resource": resource,
                        "encoding": encoding,
                        "refer": refer,
                        "embedded": bool(content),
                        "content": content,
                    }
                    for key in key_values
                    if key
                }
            )
    return records


def _font_file_path(pdf_path: Path, record: dict[str, Any]) -> str | None:
    content = record.get("content", b"")
    if not content:
        return None
    output = pdf_path.parent / "pdf-fonts"
    output.mkdir(parents=True, exist_ok=True)
    extension = str(record.get("extension") or "bin").lower().lstrip(".")
    path = output / f"font-{record['xref']}.{extension}"
    if not path.exists():
        path.write_bytes(content)
    return path.as_posix()


def _span_overlaps(span_bbox: list[float], selection_bbox: list[float], fitz: Any) -> bool:
    return fitz.Rect(*span_bbox).intersects(fitz.Rect(*selection_bbox))


def inspect_pdf(
    pdf_path: Path,
    *,
    page_number: int,
    bbox: list[float] | None = None,
) -> dict[str, Any]:
    """Return metadata for text spans on a 1-based PDF page.

    ``bbox`` uses PDF.js/PyMuPDF's top-left page coordinates.  Type0/CID text
    is returned after the PDF's Unicode mapping has been applied by PyMuPDF;
    the report explicitly identifies this mapping state rather than guessing
    a legacy encoding.
    """
    fitz = _load_fitz()
    if not pdf_path.is_file():
        raise PdfInspectionError(f"PDF not found: {pdf_path}")
    if page_number < 1:
        raise PdfInspectionError("page must be 1 or greater")
    try:
        document = fitz.open(pdf_path)
    except Exception as exc:
        raise PdfInspectionError(f"Could not open PDF: {exc}") from exc
    try:
        if page_number > document.page_count:
            raise PdfInspectionError(f"page {page_number} is outside the PDF")
        page = document[page_number - 1]
        page_rect = page.rect
        selection = None
        if bbox is not None:
            if len(bbox) != 4:
                raise PdfInspectionError("bbox must contain left, top, right, bottom")
            selection = [float(value) for value in bbox]
            if selection[2] <= selection[0] or selection[3] <= selection[1]:
                raise PdfInspectionError("bbox must have positive width and height")
        records = _font_records(document)
        spans: list[dict[str, Any]] = []
        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT).get("blocks", [])
        for block_index, block in enumerate(blocks):
            for line_index, line in enumerate(block.get("lines", [])):
                for span_index, raw_span in enumerate(line.get("spans", [])):
                    text = str(raw_span.get("text", ""))
                    if not text.strip():
                        continue
                    span_bbox = [float(value) for value in raw_span.get("bbox", [])]
                    if len(span_bbox) != 4 or (selection and not _span_overlaps(span_bbox, selection, fitz)):
                        continue
                    displayed_font = str(raw_span.get("font", ""))
                    record = records.get(displayed_font, {})
                    if not record:
                        record = records.get(_family("", displayed_font), {})
                    flags = int(raw_span.get("flags", 0))
                    spans.append(
                        {
                            "text": text,
                            "font": displayed_font,
                            "fontFamily": _family(str(record.get("baseFont", "")), displayed_font),
                            "baseFont": record.get("baseFont"),
                            "fontSubtype": record.get("subtype"),
                            "resourceName": record.get("resource"),
                            "encoding": record.get("encoding"),
                            "embedded": bool(record.get("embedded", False)),
                            "fontFileType": record.get("extension"),
                            "fontFilePath": _font_file_path(pdf_path, record),
                            "fontFileBytes": len(record.get("content", b"")),
                            "size": float(raw_span.get("size", 0)),
                            "color": _color(int(raw_span.get("color", 0)), int(raw_span.get("alpha", 255))),
                            "bold": bool(flags & 16),
                            "italic": bool(flags & 2),
                            "monospace": bool(flags & 8),
                            "serif": bool(flags & 4),
                            "bbox": span_bbox,
                            "origin": raw_span.get("origin"),
                            "contentLocation": {
                                "block": block_index,
                                "line": line_index,
                                "span": span_index,
                            },
                            "unicodeMapping": "decoded by PyMuPDF (ToUnicode/CID mapping when present)",
                            "mappingStatus": "ok" if "\ufffd" not in text else "replacement-character-present",
                        }
                    )
        return {
            "engine": "PyMuPDF",
            "page": page_number,
            "pageSize": [float(page_rect.width), float(page_rect.height)],
            "selectionBBox": selection,
            "spans": spans,
            "contentStreamXRefs": list(page.get_contents() or []),
            "contentStreamPosition": "reported as block/line/span; raw byte offsets are not stable across PDF implementations",
        }
    finally:
        document.close()
