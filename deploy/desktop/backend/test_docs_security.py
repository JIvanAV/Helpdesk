import os
import unittest

from fastapi.testclient import TestClient

from docs_security import DEFAULT_LOCAL_DOCS_KEY
from main import app


class HelpdeskDocsSecurityTest(unittest.TestCase):
    def setUp(self):
        self.original_key = os.environ.get("HELPDESK_DOCS_KEY")
        os.environ["HELPDESK_DOCS_KEY"] = "entrevista-tecnica"
        self.client = TestClient(app)

    def tearDown(self):
        if self.original_key is None:
            os.environ.pop("HELPDESK_DOCS_KEY", None)
        else:
            os.environ["HELPDESK_DOCS_KEY"] = self.original_key

    def test_blocks_swagger_without_key(self):
        response = self.client.get("/docs")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Chave da documentação inválida ou ausente")

    def test_serves_swagger_with_query_key(self):
        response = self.client.get("/docs?key=entrevista-tecnica")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Ivan Helpdesk API - Documentação", response.text)
        self.assertIn("/openapi.json?key=entrevista-tecnica", response.text)

    def test_serves_openapi_with_header_key(self):
        response = self.client.get(
            "/openapi.json",
            headers={"X-Helpdesk-Docs-Key": "entrevista-tecnica"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["info"]["title"], "Ivan Helpdesk API")
        self.assertIn("/tickets", body["paths"])

    def test_uses_local_fallback_for_clean_dev_machine(self):
        os.environ.pop("HELPDESK_DOCS_KEY", None)

        response = self.client.get(f"/openapi.json?key={DEFAULT_LOCAL_DOCS_KEY}")

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
