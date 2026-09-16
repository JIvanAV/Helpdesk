import unittest

from fastapi.testclient import TestClient

from main import app


class HelpdeskHealthEndpointTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint_reports_ready_api(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "version": "1.0.0"})


if __name__ == "__main__":
    unittest.main()
