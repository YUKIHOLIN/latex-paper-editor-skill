import unittest

from scripts.preview import (
    WORKSPACE,
    add_cjk_preamble,
    choose_engine,
    cjk_support_error,
    compiler_script_path,
)


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

    def test_compiler_helper_is_bundled_in_repository(self):
        helper = compiler_script_path()
        self.assertEqual(helper, WORKSPACE / "scripts" / "compile_latex.py")
        self.assertTrue(helper.is_file())
        self.assertTrue(helper.is_relative_to(WORKSPACE))

    def test_missing_cjk_preamble_is_repaired_after_documentclass(self):
        source = "\\documentclass{article}\n\\begin{document}\n中文\n\\end{document}\n"

        repaired = add_cjk_preamble(source)

        self.assertIn("\\usepackage{fontspec}", repaired)
        self.assertIn("\\usepackage{xeCJK}", repaired)
        self.assertIn("skills/latex-paper-editor/assets/cjk-font-fallback.tex", repaired)
        self.assertEqual(repaired.count("\\usepackage{xeCJK}"), 1)


if __name__ == "__main__":
    unittest.main()
