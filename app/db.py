"""
app/db.py – Database connection and schema initialization.

Uses SQLite (no server required). On first run, init_db() creates all
required tables automatically.
"""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Resolve DB path relative to project root regardless of where app is invoked from
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = _PROJECT_ROOT / "hr_management.db"


def connect_db() -> sqlite3.Connection:
    """Return a SQLite connection with row_factory set to sqlite3.Row."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrent read performance
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn
    except sqlite3.Error as exc:
        raise RuntimeError(f"Failed to connect to database at {DB_PATH}: {exc}") from exc


def init_db() -> None:
    """
    Create all required tables if they do not already exist.
    Safe to call multiple times (idempotent).
    """
    conn = connect_db()
    try:
        cursor = conn.cursor()

        # Users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id       TEXT PRIMARY KEY,
                gmail    TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role     TEXT NOT NULL CHECK(role IN ('employee', 'hr')),
                name     TEXT NOT NULL,
                email_verified BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Leave requests table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS leave_requests (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT NOT NULL REFERENCES users(id),
                name       TEXT NOT NULL,
                leave_type TEXT NOT NULL DEFAULT 'Paid Leave',
                start_date TEXT NOT NULL,
                end_date   TEXT NOT NULL,
                reason     TEXT NOT NULL,
                status     TEXT NOT NULL DEFAULT 'pending'
                           CHECK(status IN ('pending', 'approved', 'rejected', 'cancelled')),
                hr_comment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Employees table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id           TEXT PRIMARY KEY REFERENCES users(id),
                phone        TEXT,
                address      TEXT,
                department   TEXT,
                designation  TEXT,
                joining_date DATE,
                profile_pic  BLOB
            )
            """
        )

        # Documents table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id   TEXT REFERENCES users(id),
                document_name TEXT,
                document_url  TEXT,
                uploaded_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Attendance table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id  TEXT NOT NULL REFERENCES users(id),
                date         DATE NOT NULL,
                check_in     TIME,
                check_out    TIME,
                status       TEXT DEFAULT 'absent'
                             CHECK(status IN ('present', 'absent', 'half_day', 'leave')),
                UNIQUE(employee_id, date)
            )
            """
        )

        # Payroll table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS payroll (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id  TEXT UNIQUE REFERENCES users(id),
                basic_salary REAL DEFAULT 0,
                allowances   REAL DEFAULT 0,
                deductions   REAL DEFAULT 0,
                updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.commit()
    finally:
        conn.close()
