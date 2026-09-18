import json
import tempfile
import unittest
from pathlib import Path

from bridge.server import match_payload, status_payload


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


if __name__ == "__main__":
    unittest.main()
