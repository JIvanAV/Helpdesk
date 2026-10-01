import unittest
from pathlib import Path


class HelpdeskReadmeDocsTest(unittest.TestCase):
    def test_readme_documents_mobile_review_flow(self):
        readme = Path(__file__).resolve().parents[3] / "README.md"
        content = readme.read_text(encoding="utf-8")

        self.assertIn("Revisão mobile da tela de triagem", content)
        self.assertIn("Filtros", content)
        self.assertIn("Triagem diária", content)
        self.assertIn("cards de chamados", content)


if __name__ == "__main__":
    unittest.main()
