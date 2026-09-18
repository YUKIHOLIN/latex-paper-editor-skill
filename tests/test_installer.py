import tempfile
import unittest
from pathlib import Path

from installer import copy_skill


class InstallerTests(unittest.TestCase):
    def test_copy_skill_installs_only_skill_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            target = Path(directory) / "target"
            skill = source / "skills" / "latex-paper-editor"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: latex-paper-editor\n---\n", encoding="utf-8")
            (skill / "assets").mkdir()
            (skill / "assets" / "cjk-font-fallback.tex").write_text("fallback", encoding="utf-8")
            (source / "paper.tex").write_text("sample", encoding="utf-8")

            installed = copy_skill(source, target)

            self.assertEqual(installed, target / "latex-paper-editor")
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertTrue((installed / "assets" / "cjk-font-fallback.tex").is_file())
            self.assertFalse((target / "paper.tex").exists())


if __name__ == "__main__":
    unittest.main()
