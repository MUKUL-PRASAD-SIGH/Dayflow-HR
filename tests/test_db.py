"""
tests/test_db.py – Tests for database connection and schema initialization.

Run with:
    pytest tests/ -v
"""

import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Patch DB_PATH to a temp file so tests don't touch the real database
# ---------------------------------------------------------------------------

@pytest.fixture()
def temp_db(tmp_path):
    """Provide a temporary DB path and patch app.db to use it."""
    db_file = tmp_path / "test_hr.db"

    with patch("app.db.DB_PATH", db_file):
        from app.db import init_db
        init_db()
        yield db_file


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestConnectDb:
    def test_returns_connection(self, temp_db):
        with patch("app.db.DB_PATH", temp_db):
            from app.db import connect_db
            conn = connect_db()
            assert conn is not None
            conn.close()

    def test_row_factory_is_row(self, temp_db):
        with patch("app.db.DB_PATH", temp_db):
            from app.db import connect_db
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 AS value")
            row = cursor.fetchone()
            # sqlite3.Row supports both index and key access
            assert row["value"] == 1
            conn.close()


class TestInitDb:
    def test_creates_users_table(self, temp_db):
        with patch("app.db.DB_PATH", temp_db):
            from app.db import connect_db
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            )
            assert cursor.fetchone() is not None
            conn.close()

    def test_creates_leave_requests_table(self, temp_db):
        with patch("app.db.DB_PATH", temp_db):
            from app.db import connect_db
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='leave_requests'"
            )
            assert cursor.fetchone() is not None
            conn.close()

    def test_idempotent(self, temp_db):
        """Calling init_db() twice should not raise."""
        with patch("app.db.DB_PATH", temp_db):
            from app.db import init_db
            init_db()  # second call
            init_db()  # third call – should still be fine

    def test_users_schema_columns(self, temp_db):
        with patch("app.db.DB_PATH", temp_db):
            from app.db import connect_db
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = {row["name"] for row in cursor.fetchall()}
            expected = {"id", "gmail", "password", "role", "name", "created_at"}
            assert expected.issubset(columns)
            conn.close()

    def test_leave_requests_schema_columns(self, temp_db):
        with patch("app.db.DB_PATH", temp_db):
            from app.db import connect_db
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(leave_requests)")
            columns = {row["name"] for row in cursor.fetchall()}
            expected = {
                "id", "user_id", "name", "start_date", "end_date",
                "reason", "status", "hr_comment", "created_at", "updated_at",
            }
            assert expected.issubset(columns)
            conn.close()
