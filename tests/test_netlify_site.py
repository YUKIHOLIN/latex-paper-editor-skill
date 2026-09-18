import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NetlifySiteTests(unittest.TestCase):
    def test_static_site_contains_upload_gate_and_editor_controls(self):
        html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="pdf-file"', html)
        self.assertIn('id="tex-file"', html)
        self.assertIn('id="workspace"', html)
        self.assertIn('id="download-tex"', html)

    def test_netlify_config_publishes_site_directory(self):
        config = (ROOT / "netlify.toml").read_text(encoding="utf-8")
        self.assertIn('publish = "site"', config)


if __name__ == "__main__":
    unittest.main()
