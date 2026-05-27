"""SQLite database setup and helper functions for the resume analyzer app."""

import sqlite3
import os
import json
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager

# Database path - Flask instance folder
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "resume_analyzer.db")


def get_db_path():
    """Return the path to the SQLite database file."""
    return DB_PATH


def init_db():
    """Create the database and tables if they do not exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            score INTEGER NOT NULL,
            tips TEXT NOT NULL,
            detailed_results TEXT,
            uploaded_at TEXT NOT NULL,
            job_title TEXT,
            job_description TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            payload_json TEXT,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            read_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_user_read_created
        ON notifications (user_id, is_read, created_at DESC)
    """)

    # Add detailed_results column if it doesn't exist (for existing databases)
    try:
        cursor.execute("SELECT detailed_results FROM analyses LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE analyses ADD COLUMN detailed_results TEXT")

    # Add job_title column if it doesn't exist (for existing databases)
    try:
        cursor.execute("SELECT job_title FROM analyses LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE analyses ADD COLUMN job_title TEXT")

    # Add job_description column if it doesn't exist (for existing databases)
    try:
        cursor.execute("SELECT job_description FROM analyses LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE analyses ADD COLUMN job_description TEXT")

    # Add feedback_rating column if it doesn't exist (for existing databases)
    try:
        cursor.execute("SELECT feedback_rating FROM analyses LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE analyses ADD COLUMN feedback_rating INTEGER")

    # Add feedback_comment column if it doesn't exist (for existing databases)
    try:
        cursor.execute("SELECT feedback_comment FROM analyses LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE analyses ADD COLUMN feedback_comment TEXT")

    conn.commit()
    conn.close()


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def add_user(username, email, password_hash):
    """
    Add a new user to the database.
    Returns the user id on success, None if username or email already exists.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, datetime.now(timezone.utc).isoformat())
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def get_user_by_username(username):
    """Get a user by username. Returns None if not found."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email(email):
    """Get a user by email. Returns None if not found."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id):
    """Get a user by id. Returns None if not found."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def add_analysis(user_id, filename, score, tips, detailed_results=None, job_title=None, job_description=None):
    """
    Add a resume analysis record.
    tips should be a list of strings; we store as newline-separated text.
    detailed_results is a dict stored as JSON.
    job_title is the selected job position.
    job_description is the job description text used for matching.
    """
    tips_text = "\n".join(tips) if isinstance(tips, list) else tips
    detailed_json = json.dumps(detailed_results) if detailed_results else None

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO analyses (user_id, filename, score, tips, detailed_results, uploaded_at, job_title, job_description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, filename, score, tips_text, detailed_json, datetime.now(timezone.utc).isoformat(), job_title, job_description)
        )
        return cursor.lastrowid


def get_analyses_by_user(user_id, limit=10):
    """Get analyses for a user. Set limit=None to get all records."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if limit:
            cursor.execute(
                "SELECT * FROM analyses WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT ?",
                (user_id, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM analyses WHERE user_id = ? ORDER BY uploaded_at DESC",
                (user_id,)
            )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["tips"] = d["tips"].split("\n") if d["tips"] else []
            d["detailed_results"] = json.loads(d["detailed_results"]) if d.get("detailed_results") else None
            result.append(d)
        return result


def delete_analysis(analysis_id, user_id):
    """Delete an analysis by ID, verifying it belongs to the user. Returns True if deleted."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user_id)
        )
        return cursor.rowcount > 0


def get_analysis_by_id(analysis_id: int, user_id: int) -> dict | None:
    """Get a single analysis by ID, verifying it belongs to the user. Returns None if not found."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user_id)
        )
        row = cursor.fetchone()
        if row:
            d = dict(row)
            d["tips"] = d["tips"].split("\n") if d["tips"] else []
            d["detailed_results"] = json.loads(d["detailed_results"]) if d.get("detailed_results") else None
            return d
        return None


def update_feedback(analysis_id: int, user_id: int, rating: int, comment: str | None) -> bool:
    """
    Submit feedback for an analysis. Feedback can only be submitted once.
    Returns True if successful.
    Raises ValueError if feedback already exists.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        # Check if feedback already exists
        cursor.execute(
            "SELECT feedback_rating FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user_id)
        )
        row = cursor.fetchone()
        if not row:
            return False
        if row["feedback_rating"] is not None:
            raise ValueError("Feedback already submitted for this analysis.")
        cursor.execute(
            "UPDATE analyses SET feedback_rating = ?, feedback_comment = ? WHERE id = ? AND user_id = ?",
            (rating, comment, analysis_id, user_id)
        )
        return cursor.rowcount > 0


def create_notification(user_id: int, type: str, title: str, message: str, payload: dict | None = None) -> int:
    """Create a notification for a user and return its id."""
    payload_json = json.dumps(payload) if payload is not None else None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO notifications (user_id, type, title, message, payload_json, is_read, created_at, read_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, NULL)
            """,
            (user_id, type, title, message, payload_json, datetime.now(timezone.utc).isoformat())
        )
        return cursor.lastrowid


def get_notifications(user_id: int, limit: int = 20, offset: int = 0, unread_only: bool = False) -> list[dict]:
    """Return notifications for a user ordered by most recent first."""
    with get_connection() as conn:
        cursor = conn.cursor()
        base_sql = """
            SELECT * FROM notifications
            WHERE user_id = ?
        """
        params = [user_id]
        if unread_only:
            base_sql += " AND is_read = 0"
        base_sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(base_sql, tuple(params))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["is_read"] = bool(d["is_read"])
            d["payload"] = json.loads(d["payload_json"]) if d.get("payload_json") else None
            result.append(d)
        return result


def get_unread_count(user_id: int) -> int:
    """Return unread notification count for a user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = ? AND is_read = 0",
            (user_id,)
        )
        row = cursor.fetchone()
        return int(row["cnt"]) if row else 0


def mark_notification_read(notification_id: int, user_id: int) -> bool:
    """Mark a single notification as read for a user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE notifications
            SET is_read = 1, read_at = COALESCE(read_at, ?)
            WHERE id = ? AND user_id = ?
            """,
            (datetime.now(timezone.utc).isoformat(), notification_id, user_id)
        )
        return cursor.rowcount > 0


def mark_all_notifications_read(user_id: int) -> int:
    """Mark all unread notifications as read for a user. Returns number updated."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE notifications
            SET is_read = 1, read_at = COALESCE(read_at, ?)
            WHERE user_id = ? AND is_read = 0
            """,
            (datetime.now(timezone.utc).isoformat(), user_id)
        )
        return cursor.rowcount


def delete_expired_notifications(days: int = 30) -> int:
    """Delete notifications older than the retention window. Returns rows deleted."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM notifications WHERE created_at < ?",
            (cutoff.isoformat(),)
        )
        return cursor.rowcount
