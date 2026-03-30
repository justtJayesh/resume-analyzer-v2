"""Tests for the database module."""

import pytest
import os
import tempfile
import database


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
