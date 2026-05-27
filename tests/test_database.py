"""Tests for the database module."""

import pytest
import database
from datetime import datetime, timezone, timedelta


class TestDatabase:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Use temporary database for tests."""
        self.original_db_path = database.DB_PATH
        database.DB_PATH = str(tmp_path / "test.db")
        database.init_db()
        yield
        database.DB_PATH = self.original_db_path

    def test_add_user(self):
        user_id = database.add_user("testuser", "test@test.com", "hash123")
        assert user_id is not None
        assert user_id > 0

    def test_get_user_by_username(self):
        database.add_user("testuser", "test@test.com", "hash123")
        user = database.get_user_by_username("testuser")
        assert user is not None
        assert user["username"] == "testuser"
        assert user["email"] == "test@test.com"

    def test_get_user_by_username_not_found(self):
        user = database.get_user_by_username("nonexistent")
        assert user is None

    def test_add_analysis(self):
        user_id = database.add_user("testuser", "test@test.com", "hash123")
        analysis_id = database.add_analysis(user_id, "resume.pdf", 75, ["Tip 1"])
        assert analysis_id is not None

    def test_get_analyses_by_user(self):
        user_id = database.add_user("testuser", "test@test.com", "hash123")
        database.add_analysis(user_id, "resume1.pdf", 75, ["Tip 1"])
        database.add_analysis(user_id, "resume2.pdf", 80, ["Tip 2"])

        analyses = database.get_analyses_by_user(user_id)
        assert len(analyses) == 2
        assert analyses[0]["filename"] == "resume2.pdf"  # Most recent first

    def test_update_feedback_success(self):
        user_id = database.add_user("testuser", "test@test.com", "hash123")
        analysis_id = database.add_analysis(user_id, "resume.pdf", 75, ["Tip 1"])

        result = database.update_feedback(analysis_id, user_id, 5, "Great analysis!")
        assert result is True

        # Verify feedback was stored
        analysis = database.get_analysis_by_id(analysis_id, user_id)
        assert analysis["feedback_rating"] == 5
        assert analysis["feedback_comment"] == "Great analysis!"

    def test_update_feedback_without_comment(self):
        user_id = database.add_user("testuser", "test@test.com", "hash123")
        analysis_id = database.add_analysis(user_id, "resume.pdf", 75, ["Tip 1"])

        result = database.update_feedback(analysis_id, user_id, 3, None)
        assert result is True

        analysis = database.get_analysis_by_id(analysis_id, user_id)
        assert analysis["feedback_rating"] == 3
        assert analysis["feedback_comment"] is None

    def test_update_feedback_already_exists(self):
        user_id = database.add_user("testuser", "test@test.com", "hash123")
        analysis_id = database.add_analysis(user_id, "resume.pdf", 75, ["Tip 1"])

        database.update_feedback(analysis_id, user_id, 5, "First feedback")
        with pytest.raises(ValueError, match="already submitted"):
            database.update_feedback(analysis_id, user_id, 3, "Second feedback")

    def test_update_feedback_wrong_user(self):
        user_id = database.add_user("testuser", "test@test.com", "hash123")
        other_user_id = database.add_user("otheruser", "other@test.com", "hash456")
        analysis_id = database.add_analysis(user_id, "resume.pdf", 75, ["Tip 1"])

        result = database.update_feedback(analysis_id, other_user_id, 5, "Wrong user")
        assert result is False

    def test_get_analyses_includes_feedback(self):
        user_id = database.add_user("testuser", "test@test.com", "hash123")
        analysis_id = database.add_analysis(user_id, "resume.pdf", 75, ["Tip 1"])
        database.update_feedback(analysis_id, user_id, 4, "Good tips")

        analyses = database.get_analyses_by_user(user_id)
        assert analyses[0]["feedback_rating"] == 4
        assert analyses[0]["feedback_comment"] == "Good tips"

    def test_get_analysis_by_id_includes_feedback(self):
        user_id = database.add_user("testuser", "test@test.com", "hash123")
        analysis_id = database.add_analysis(user_id, "resume.pdf", 75, ["Tip 1"])
        database.update_feedback(analysis_id, user_id, 5, None)

        analysis = database.get_analysis_by_id(analysis_id, user_id)
        assert analysis["feedback_rating"] == 5
        assert analysis["feedback_comment"] is None

    def test_notification_create_and_list(self):
        user_id = database.add_user("notifuser", "notif@test.com", "hash123")
        database.create_notification(user_id, "analysis_success", "Done", "Resume analyzed", {"analysis_id": 1})
        items = database.get_notifications(user_id, limit=10, offset=0)
        assert len(items) == 1
        assert items[0]["type"] == "analysis_success"
        assert items[0]["payload"]["analysis_id"] == 1
        assert items[0]["is_read"] is False

    def test_notification_read_and_unread_count(self):
        user_id = database.add_user("countuser", "count@test.com", "hash123")
        n1 = database.create_notification(user_id, "a", "A", "A")
        database.create_notification(user_id, "b", "B", "B")
        assert database.get_unread_count(user_id) == 2
        assert database.mark_notification_read(n1, user_id) is True
        assert database.get_unread_count(user_id) == 1

    def test_mark_all_notifications_read(self):
        user_id = database.add_user("allread", "allread@test.com", "hash123")
        database.create_notification(user_id, "a", "A", "A")
        database.create_notification(user_id, "b", "B", "B")
        updated = database.mark_all_notifications_read(user_id)
        assert updated == 2
        assert database.get_unread_count(user_id) == 0

    def test_notification_user_scoping(self):
        user1 = database.add_user("u1", "u1@test.com", "hash123")
        user2 = database.add_user("u2", "u2@test.com", "hash123")
        n1 = database.create_notification(user1, "a", "A", "A")
        assert database.mark_notification_read(n1, user2) is False
        assert len(database.get_notifications(user2, limit=10, offset=0)) == 0
        assert database.get_unread_count(user1) == 1

    def test_delete_expired_notifications(self):
        user_id = database.add_user("exp", "exp@test.com", "hash123")
        database.create_notification(user_id, "new", "New", "Keep")
        with database.get_connection() as conn:
            cursor = conn.cursor()
            old_date = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
            cursor.execute(
                """
                INSERT INTO notifications (user_id, type, title, message, payload_json, is_read, created_at, read_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, NULL)
                """,
                (user_id, "old", "Old", "Delete", None, old_date)
            )
        deleted = database.delete_expired_notifications(days=30)
        assert deleted == 1
        items = database.get_notifications(user_id, limit=10, offset=0)
        assert len(items) == 1
        assert items[0]["type"] == "new"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
