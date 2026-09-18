"""Unicode and CJK font discovery shared by the preview workflow."""

from __future__ import annotations

import shutil
import subprocess
from typing import Callable


# Ordered from broad open-source coverage to common platform fonts.
CJK_FONT_CANDIDATES = (
    "Noto Serif CJK SC",
    "Noto Sans CJK SC",
    "Noto Sans CJK JP",
    "Noto Sans CJK TC",
    "Source Han Serif SC",
    "Source Han Sans SC",
    "Microsoft YaHei",
    "SimSun",
    "STSong",
    "WenQuanYi Zen Hei",
    "Droid Sans Fallback",
    "AR PL SungtiL GB",
)


def has_cjk_text(source: str) -> bool:
    return any(
        0x3000 <= code <= 0x30FF  # CJK punctuation, Hiragana, Katakana
        or 0x3400 <= code <= 0x9FFF  # CJK Unified Ideographs
        or 0xAC00 <= code <= 0xD7AF  # Hangul syllables
        or 0xF900 <= code <= 0xFAFF  # CJK compatibility ideographs
        for code in map(ord, source)
    )


def font_available(name: str) -> bool:
    """Return whether fontconfig resolves a named font on this host."""
    fc_match = shutil.which("fc-match")
    if not fc_match:
        return False
    result = subprocess.run(
        [fc_match, "-f", "%{family}", name],
        capture_output=True,
        text=True,
        check=False,
    )
    family = result.stdout.strip().lower()
    return bool(family) and "dejavu sans" not in family and "dejavu serif" not in family


def choose_cjk_font(checker: Callable[[str], bool] = font_available) -> str | None:
    for candidate in CJK_FONT_CANDIDATES:
        if checker(candidate):
            return candidate
    return None


def diagnostic(source: str) -> dict[str, str | bool | None]:
    if not has_cjk_text(source):
        return {"hasCjk": False, "font": None, "message": "No CJK characters detected."}
    font = choose_cjk_font()
    if font:
        return {"hasCjk": True, "font": font, "message": f"Using detected CJK font: {font}."}
    return {
        "hasCjk": True,
        "font": None,
        "message": "No known CJK font was detected. Install Noto CJK or configure a local font name before compiling.",
    }
