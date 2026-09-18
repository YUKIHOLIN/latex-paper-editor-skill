import json
import tempfile
import unittest
from pathlib import Path

try:
    import fitz
except ImportError:  # pragma: no cover - optional dependency
    fitz = None

from bridge.server import inspect_payload, match_payload, status_payload


class ServerPayloadTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "paper.tex").write_text(
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "A bridge sentence.\n"
            "\\end{document}\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_match_payload_returns_candidates(self):
        payload = match_payload(self.root, {"selectedText": "A bridge sentence.", "page": 1})
        self.assertEqual(payload["matches"][0]["file"], "paper.tex")

    def test_empty_selection_is_safe(self):
        self.assertEqual(match_payload(self.root, {"selectedText": ""}), {"matches": []})

    def test_status_payload_uses_relative_pdf_path(self):
        payload = status_payload(self.root)
        self.assertEqual(payload["pdf"], "build/paper.pdf")
        self.assertEqual(payload["sourceRoot"], ".")

    @unittest.skipUnless(fitz is not None, "PyMuPDF is optional")
    def test_inspect_payload_returns_font_and_geometry_metadata(self):
        build = self.root / "build"
        build.mkdir()
        document = fitz.open()
        page = document.new_page(width=300, height=200)
        page.insert_text((40, 80), "Bridge text", fontname="helv", fontsize=12)
        document.save(build / "paper.pdf")
        document.close()

        payload = inspect_payload(self.root, {"page": 1, "bbox": [20, 40, 180, 100]})

        self.assertEqual(payload["engine"], "PyMuPDF")
        self.assertEqual(payload["spans"][0]["text"], "Bridge text")
        self.assertIn("fontFamily", payload["spans"][0])


if __name__ == "__main__":
    unittest.main()
