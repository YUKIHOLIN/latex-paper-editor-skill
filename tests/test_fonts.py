import unittest

from scripts.font_diagnostics import CJK_FONT_CANDIDATES, choose_cjk_font, has_cjk_text


class FontDiagnosticsTests(unittest.TestCase):
    def test_detects_cjk_text(self):
        self.assertTrue(has_cjk_text("矩阵"))
        self.assertFalse(has_cjk_text("matrix"))

    def test_candidate_list_contains_open_and_common_cjk_fonts(self):
        self.assertIn("Noto Serif CJK SC", CJK_FONT_CANDIDATES)
        self.assertIn("Microsoft YaHei", CJK_FONT_CANDIDATES)
        self.assertIn("SimSun", CJK_FONT_CANDIDATES)

    def test_choose_cjk_font_returns_none_when_no_candidates_match(self):
        self.assertIsNone(choose_cjk_font(lambda _: False))

    def test_choose_cjk_font_returns_first_available_candidate(self):
        self.assertEqual(choose_cjk_font(lambda name: name == CJK_FONT_CANDIDATES[2]), CJK_FONT_CANDIDATES[2])


if __name__ == "__main__":
    unittest.main()
