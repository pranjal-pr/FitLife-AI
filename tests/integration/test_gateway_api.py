import os
import unittest


os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-thirty-two-bytes"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-with-at-least-thirty-two-bytes"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FRONTEND_URL"] = "http://localhost:3000"
os.environ["GROQ_API_KEY"] = "test-placeholder"

from gateway.app import create_app


class GatewayApiSmokeTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_auth_and_dashboard_flow(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/health").status_code, 200)

        registration = self.client.post(
            "/api/v1/auth/register",
            json={
                "name": "CI User",
                "email": "ci@example.com",
                "password": "strong-password",
            },
        )
        self.assertEqual(registration.status_code, 201)
        tokens = registration.get_json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        self.assertEqual(self.client.get("/api/v1/user", headers=headers).status_code, 200)
        self.assertEqual(
            self.client.post(
                "/api/v1/auth/register",
                json={
                    "name": "CI User",
                    "email": "ci@example.com",
                    "password": "strong-password",
                },
            ).status_code,
            409,
        )
        self.assertEqual(
            self.client.post(
                "/api/v1/auth/login",
                json={"email": "ci@example.com", "password": "wrong-password"},
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.post(
                "/api/v1/auth/login",
                json={"email": "ci@example.com", "password": "strong-password"},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": tokens["refresh_token"]},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.put(
                "/api/v1/user/settings",
                headers=headers,
                json={"age": 30, "goal": "fitness"},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/api/v1/dashboard/stats", headers=headers).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/api/v1/user/scans", headers=headers).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/api/v1/user/workouts", headers=headers).status_code,
            200,
        )
        self.assertEqual(
            self.client.post("/api/v1/nutri-ai/upload", headers=headers).status_code,
            400,
        )
        self.assertEqual(
            self.client.delete("/api/v1/user", headers=headers).status_code,
            200,
        )
        self.assertEqual(self.client.get("/api/v1/user", headers=headers).status_code, 404)


if __name__ == "__main__":
    unittest.main()
