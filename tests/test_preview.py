import unittest

from scripts.preview import choose_engine, cjk_support_error


class PreviewEngineTests(unittest.TestCase):
    def test_ascii_source_uses_pdf_latex(self):
        self.assertEqual(choose_engine(r"\\documentclass{article}\nHello"), "pdflatex")

    def test_cjk_source_with_ctex_uses_xelatex(self):
        source = r"\\documentclass{ctexart}\n你好"
        self.assertEqual(choose_engine(source), "xelatex")
        self.assertIsNone(cjk_support_error(source))

    def test_cjk_source_without_unicode_package_reports_actionable_error(self):
        source = r"\\documentclass{article}\n你好"
        self.assertEqual(choose_engine(source), "xelatex")
        self.assertIn("ctex", cjk_support_error(source))


if __name__ == "__main__":
    unittest.main()
