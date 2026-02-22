"""SQLite database setup and helper functions for the resume analyzer app."""

import sqlite3
import os
from datetime import datetime
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
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

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
                (username, email, password_hash, datetime.utcnow().isoformat())
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


def add_analysis(user_id, filename, score, tips):
    """
    Add a resume analysis record.
    tips should be a list of strings; we store as newline-separated text.
    """
    tips_text = "\n".join(tips) if isinstance(tips, list) else tips
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO analyses (user_id, filename, score, tips, uploaded_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, filename, score, tips_text, datetime.utcnow().isoformat())
        )
        return cursor.lastrowid


def get_analyses_by_user(user_id, limit=10):
    """Get recent analyses for a user. Returns list of dicts."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM analyses WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT ?",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["tips"] = d["tips"].split("\n") if d["tips"] else []
            result.append(d)
        return result
