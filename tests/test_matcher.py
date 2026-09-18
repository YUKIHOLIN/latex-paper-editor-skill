import tempfile
import unittest
from pathlib import Path

from bridge.matcher import find_matches


class MatcherTests(unittest.TestCase):
    def write_sources(self, root: Path) -> None:
        (root / "sections").mkdir()
        (root / "paper.tex").write_text(
            "% comment\n\\documentclass{article}\n"
            "\\begin{document}\n"
            "A uniquely identifiable sentence for the preview.\n"
            "\\input{sections/other}\n"
            "\\end{document}\n",
            encoding="utf-8",
        )
        (root / "sections" / "other.tex").write_text(
            "The same sentence appears twice.\n"
            "The same sentence appears twice.\n",
            encoding="utf-8",
        )

    def test_exact_match_returns_file_and_line_span(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_sources(root)
            matches = find_matches(root, "A uniquely identifiable sentence for the preview.")
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["file"], "paper.tex")
            self.assertEqual(matches[0]["startLine"], 4)
            self.assertEqual(matches[0]["endLine"], 4)
            self.assertEqual(matches[0]["confidence"], "exact")

    def test_normalized_whitespace_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_sources(root)
            matches = find_matches(root, "A uniquely   identifiable sentence\nfor the preview.")
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["confidence"], "normalized")

    def test_ambiguous_match_returns_all_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_sources(root)
            matches = find_matches(root, "The same sentence appears twice.")
            self.assertEqual(len(matches), 2)
            self.assertEqual({item["startLine"] for item in matches}, {1, 2})

    def test_unmatched_text_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_sources(root)
            self.assertEqual(find_matches(root, "not present"), [])


if __name__ == "__main__":
    unittest.main()
