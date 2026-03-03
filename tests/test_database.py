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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
