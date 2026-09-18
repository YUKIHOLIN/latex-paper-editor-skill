import tempfile
import unittest
from pathlib import Path

from bridge.server import apply_match


class ApplyTests(unittest.TestCase):
    def test_apply_match_replaces_exact_source_span(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "paper.tex"
            source.write_text("before\nOriginal sentence.\nafter\n", encoding="utf-8")
            match = {
                "file": "paper.tex",
                "startLine": 2,
                "endLine": 2,
                "sourceText": "Original sentence.",
            }

            result = apply_match(root, match, "Revised sentence.")

            self.assertEqual(result["file"], "paper.tex")
            self.assertEqual(source.read_text(encoding="utf-8"), "before\nRevised sentence.\nafter\n")

    def test_apply_match_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                apply_match(
                    root,
                    {"file": "../paper.tex", "startLine": 1, "endLine": 1, "sourceText": "x"},
                    "y",
                )

    def test_apply_match_rejects_stale_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "paper.tex").write_text("current\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                apply_match(
                    root,
                    {"file": "paper.tex", "startLine": 1, "endLine": 1, "sourceText": "old"},
                    "new",
                )

    def test_apply_match_replaces_only_selected_substring(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "paper.tex"
            source.write_text("A uniquely identifiable sentence.\n", encoding="utf-8")
            match = {
                "file": "paper.tex",
                "startLine": 1,
                "endLine": 1,
                "sourceText": "A uniquely identifiable sentence.",
                "selectedText": "uniquely identifiable",
            }

            apply_match(root, match, "directly applied")

            self.assertEqual(source.read_text(encoding="utf-8"), "A directly applied sentence.\n")


if __name__ == "__main__":
    unittest.main()
