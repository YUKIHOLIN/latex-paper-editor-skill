"""Find rendered-text candidates in a LaTeX source tree."""

from __future__ import annotations

import re
from pathlib import Path


_COMMAND_RE = re.compile(r"\\[A-Za-z@]+\*?(?:\[[^]]*\])?")
_COMMENT_RE = re.compile(r"(?<!\\)%.*$")


def _normalize(value: str) -> str:
    value = _COMMENT_RE.sub("", value)
    value = _COMMAND_RE.sub(" ", value)
    value = value.replace("{", " ").replace("}", " ")
    return " ".join(value.split()).strip()


def _source_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.tex") if path.is_file())


def find_matches(root: Path, selected_text: str) -> list[dict]:
    """Return source candidates for text copied from a rendered PDF.

    Matching is line-preserving so Codex can apply a narrow edit. We first
    compare whitespace-normalized source windows, then fall back to a
    normalized comparison that removes common TeX commands and braces.
    """

    selected_raw = selected_text.strip()
    selected_normalized = _normalize(selected_text)
    if not selected_raw and not selected_normalized:
        return []

    matches: list[dict] = []
    for source_path in _source_files(root):
        lines = source_path.read_text(encoding="utf-8").splitlines()
        relative = source_path.relative_to(root).as_posix()
        for start in range(len(lines)):
            for length in range(1, min(6, len(lines) - start + 1)):
                end = start + length
                source_text = "\n".join(lines[start:end]).strip()
                if not source_text:
                    continue
                if any(line.lstrip().startswith("%") for line in lines[start:end]):
                    continue
                source_raw = source_text.strip()
                if source_raw == selected_raw:
                    confidence = "exact"
                elif _normalize(source_text) == selected_normalized:
                    confidence = "normalized"
                else:
                    continue
                matches.append(
                    {
                        "file": relative,
                        "startLine": start + 1,
                        "endLine": end,
                        "sourceText": source_text,
                        "confidence": confidence,
                    }
                )
    # The shortest matching span is the most actionable candidate. Keep only
    # the best confidence for identical spans discovered through multiple
    # window sizes.
    unique: dict[tuple[str, int, int], dict] = {}
    rank = {"exact": 0, "normalized": 1}
    for match in matches:
        key = (match["file"], match["startLine"], match["endLine"])
        current = unique.get(key)
        if current is None or rank[match["confidence"]] < rank[current["confidence"]]:
            unique[key] = match
    return sorted(unique.values(), key=lambda item: (item["file"], item["startLine"]))
