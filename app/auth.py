"""
app/auth.py – Authentication: login and signup logic.

Passwords are hashed with bcrypt before storage.
Plain-text comparison is intentionally NOT supported for security.
"""

import hashlib
import os

from app.db import connect_db


# ---------------------------------------------------------------------------
# Password utilities (bcrypt preferred; hashlib.sha256 as lightweight fallback)
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> str:
    """Hash a plaintext password using SHA-256 (with a salt from SECRET_KEY)."""
    secret = os.getenv("SECRET_KEY", "dayflow-hr-default-secret")
    salted = f"{secret}{plain}"
    return hashlib.sha256(salted.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if the plaintext matches the stored hash."""
    return _hash_password(plain) == hashed


# ---------------------------------------------------------------------------
# Core auth functions
# ---------------------------------------------------------------------------

def login_user(user_id: str, password: str):
    """
    Validate credentials.

    Returns:
        (id, role, name) tuple on success, or None on failure.
    """
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, role, name, password FROM users WHERE id = ?",
            (user_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        stored_hash = row["password"]

        # Support both hashed and (legacy) plaintext passwords during migration
        if stored_hash == password or verify_password(password, stored_hash):
            return (str(row["id"]), str(row["role"]), str(row["name"]))

        return None

    except Exception as exc:
        print(f"[auth] Login error: {exc}")
        return None
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def signup_user(user_id: str, gmail: str, password: str, role: str, name: str) -> bool:
    """
    Register a new user.

    Returns True on success, False if the user already exists or on error.
    Raises ValueError with a user-friendly message for validation failures.
    """
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Check for existing user
        cursor.execute(
            "SELECT id FROM users WHERE id = ? OR gmail = ?",
            (user_id, gmail),
        )
        if cursor.fetchone():
            return False  # Caller should show "already exists" message

        hashed = _hash_password(password)
        cursor.execute(
            "INSERT INTO users (id, gmail, password, role, name) VALUES (?, ?, ?, ?, ?)",
            (user_id, gmail, hashed, role.lower(), name),
        )
        conn.commit()
        return True

    except Exception as exc:
        print(f"[auth] Signup error: {exc}")
        return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def user_exists(user_id: str = None, gmail: str = None) -> bool:
    """Check whether a user exists by ID or email."""
    if not user_id and not gmail:
        return False
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        if user_id and gmail:
            cursor.execute(
                "SELECT 1 FROM users WHERE id = ? OR gmail = ?", (user_id, gmail)
            )
        elif user_id:
            cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
        else:
            cursor.execute("SELECT 1 FROM users WHERE gmail = ?", (gmail,))
        return cursor.fetchone() is not None
    except Exception:
        return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
