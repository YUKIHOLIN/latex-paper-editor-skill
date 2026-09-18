import tempfile
import unittest
from pathlib import Path

try:
    import fitz
except ImportError:  # pragma: no cover - exercised on minimal hosts
    fitz = None

from bridge.pdf_inspector import inspect_pdf


@unittest.skipUnless(fitz is not None, "PyMuPDF is optional")
class PdfInspectorTests(unittest.TestCase):
    def test_reports_span_font_geometry_and_decoded_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf_path = root / "sample.pdf"
            document = fitz.open()
            page = document.new_page(width=300, height=200)
            page.insert_text((40, 80), "Hello PDF", fontname="helv", fontsize=14, color=(0.1, 0.2, 0.3))
            document.save(pdf_path)
            document.close()

            report = inspect_pdf(pdf_path, page_number=1)

            self.assertEqual(report["page"], 1)
            self.assertEqual(report["engine"], "PyMuPDF")
            self.assertTrue(report["spans"])
            span = report["spans"][0]
            self.assertIn("Hello PDF", span["text"])
            self.assertEqual(span["fontFamily"], "Helvetica")
            self.assertEqual(span["size"], 14)
            self.assertEqual(span["color"]["space"], "rgb")
            self.assertEqual(span["contentLocation"]["block"], 0)
            self.assertIn("bbox", span)

    def test_bbox_filters_spans_in_pdf_coordinates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf_path = root / "sample.pdf"
            document = fitz.open()
            page = document.new_page(width=300, height=200)
            page.insert_text((40, 80), "inside", fontname="helv", fontsize=12)
            page.insert_text((200, 160), "outside", fontname="helv", fontsize=12)
            document.save(pdf_path)
            document.close()

            report = inspect_pdf(pdf_path, page_number=1, bbox=[20, 40, 150, 100])

            self.assertEqual([span["text"] for span in report["spans"]], ["inside"])


if __name__ == "__main__":
    unittest.main()
