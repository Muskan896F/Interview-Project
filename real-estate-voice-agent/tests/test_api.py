import unittest
from fastapi.testclient import TestClient
from main import app

class TestAPIRouter(unittest.TestCase):
    """Verifies FastAPI routing logic and schema inputs."""

    def setUp(self):
        self.client = TestClient(app)

    def test_invalid_lead_phone(self):
        """Checks bad mobile inputs return status 400."""
        payload = {
            "name": "Dev",
            "phone": "invalid-phone",
            "email": "dev@test.com"
        }
        res = self.client.post("/api/create-lead", json=payload)
        self.assertEqual(res.status_code, 400)

if __name__ == "__main__":
    unittest.main()
