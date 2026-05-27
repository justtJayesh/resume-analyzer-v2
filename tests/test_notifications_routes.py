"""Route tests for notification endpoints."""

import os
import importlib
import database

os.environ["SECRET_KEY"] = "test-secret-key"
app_module = importlib.import_module("app")
flask_app = app_module.app


class TestNotificationRoutes:
    def setup_method(self):
        self.original_db_path = database.DB_PATH
        database.DB_PATH = "/tmp/test_notifications_routes.db"
        if os.path.exists(database.DB_PATH):
            os.remove(database.DB_PATH)
        database.init_db()
        flask_app.config["TESTING"] = True
        self.client = flask_app.test_client()

    def teardown_method(self):
        database.DB_PATH = self.original_db_path

    def _login_session(self):
        user_id = database.add_user("routeuser", "route@test.com", "hash")
        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["username"] = "routeuser"
            sess["csrf_token"] = "test-csrf"
        return user_id

    def test_auth_required(self):
        resp = self.client.get("/api/notifications")
        assert resp.status_code in (302, 401)

    def test_notifications_json_shape(self):
        user_id = self._login_session()
        database.create_notification(user_id, "analysis_success", "Done", "Resume analyzed")
        resp = self.client.get("/api/notifications?limit=8&offset=0")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "notifications" in data
        assert "unread_count" in data
        assert len(data["notifications"]) == 1

    def test_csrf_protection_on_post(self):
        user_id = self._login_session()
        nid = database.create_notification(user_id, "analysis_success", "Done", "Resume analyzed")
        resp = self.client.post(
            f"/api/notifications/{nid}/read",
            json={}
        )
        assert resp.status_code == 403

    def test_mark_read_and_mark_all(self):
        user_id = self._login_session()
        n1 = database.create_notification(user_id, "a", "A", "A")
        database.create_notification(user_id, "b", "B", "B")

        resp1 = self.client.post(
            f"/api/notifications/{n1}/read",
            headers={"X-CSRF-Token": "test-csrf"}
        )
        assert resp1.status_code == 200
        assert resp1.get_json()["success"] is True

        resp2 = self.client.post(
            "/api/notifications/read-all",
            headers={"X-CSRF-Token": "test-csrf"}
        )
        assert resp2.status_code == 200
        data = resp2.get_json()
        assert data["success"] is True
        assert data["unread_count"] == 0
