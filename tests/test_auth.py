"""
tests/test_auth.py – Tests for login and signup logic.
"""

import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Shared fixture: temp DB with schema
# ---------------------------------------------------------------------------

@pytest.fixture()
def db(tmp_path):
    """Set up a fresh in-memory-ish temp DB and patch app.db.DB_PATH."""
    db_file = tmp_path / "test_auth.db"
    with patch("app.db.DB_PATH", db_file):
        from app.db import init_db
        init_db()
        yield db_file


def _seed_user(db_path, user_id="EMP001", gmail="test@example.com",
               password="secret123", role="employee", name="Test User"):
    """Insert a user (with hashed password) directly for test setup."""
    with patch("app.db.DB_PATH", db_path):
        from app.auth import signup_user
        signup_user(user_id, gmail, password, role, name)


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        from app.auth import _hash_password
        hashed = _hash_password("mypassword")
        assert hashed != "mypassword"

    def test_same_input_same_hash(self):
        from app.auth import _hash_password
        assert _hash_password("abc") == _hash_password("abc")

    def test_different_inputs_different_hashes(self):
        from app.auth import _hash_password
        assert _hash_password("abc") != _hash_password("xyz")

    def test_verify_correct_password(self):
        from app.auth import _hash_password, verify_password
        hashed = _hash_password("correct")
        assert verify_password("correct", hashed) is True

    def test_verify_wrong_password(self):
        from app.auth import _hash_password, verify_password
        hashed = _hash_password("correct")
        assert verify_password("wrong", hashed) is False


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------

class TestSignupUser:
    def test_signup_succeeds(self, db):
        with patch("app.db.DB_PATH", db):
            from app.auth import signup_user
            result = signup_user("EMP001", "emp@test.com", "pass123", "employee", "Alice")
            assert result is True

    def test_duplicate_id_fails(self, db):
        with patch("app.db.DB_PATH", db):
            from app.auth import signup_user
            signup_user("EMP001", "alice@test.com", "pass", "employee", "Alice")
            result = signup_user("EMP001", "bob@test.com", "pass", "employee", "Bob")
            assert result is False

    def test_duplicate_email_fails(self, db):
        with patch("app.db.DB_PATH", db):
            from app.auth import signup_user
            signup_user("EMP001", "shared@test.com", "pass", "employee", "Alice")
            result = signup_user("EMP002", "shared@test.com", "pass", "employee", "Bob")
            assert result is False

    def test_signup_hr_role(self, db):
        with patch("app.db.DB_PATH", db):
            from app.auth import signup_user, login_user
            signup_user("HR001", "hr@test.com", "hrpass", "hr", "HR Manager")
            result = login_user("HR001", "hrpass")
            assert result is not None
            assert result[1] == "hr"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLoginUser:
    def test_login_success(self, db):
        _seed_user(db)
        with patch("app.db.DB_PATH", db):
            from app.auth import login_user
            result = login_user("EMP001", "secret123")
            assert result is not None
            assert result[0] == "EMP001"
            assert result[1] == "employee"
            assert result[2] == "Test User"

    def test_login_wrong_password(self, db):
        _seed_user(db)
        with patch("app.db.DB_PATH", db):
            from app.auth import login_user
            result = login_user("EMP001", "wrongpass")
            assert result is None

    def test_login_nonexistent_user(self, db):
        with patch("app.db.DB_PATH", db):
            from app.auth import login_user
            result = login_user("NOBODY", "anypass")
            assert result is None

    def test_login_returns_tuple_of_three(self, db):
        _seed_user(db)
        with patch("app.db.DB_PATH", db):
            from app.auth import login_user
            result = login_user("EMP001", "secret123")
            assert isinstance(result, tuple)
            assert len(result) == 3

    def test_login_case_sensitive_id(self, db):
        _seed_user(db, user_id="EMP001")
        with patch("app.db.DB_PATH", db):
            from app.auth import login_user
            # IDs are stored as-is; wrong case should fail
            result = login_user("emp001", "secret123")
            assert result is None


# ---------------------------------------------------------------------------
# user_exists
# ---------------------------------------------------------------------------

class TestUserExists:
    def test_exists_by_id(self, db):
        _seed_user(db)
        with patch("app.db.DB_PATH", db):
            from app.auth import user_exists
            assert user_exists(user_id="EMP001") is True

    def test_exists_by_email(self, db):
        _seed_user(db)
        with patch("app.db.DB_PATH", db):
            from app.auth import user_exists
            assert user_exists(gmail="test@example.com") is True

    def test_not_exists(self, db):
        with patch("app.db.DB_PATH", db):
            from app.auth import user_exists
            assert user_exists(user_id="GHOST") is False

    def test_no_args_returns_false(self, db):
        with patch("app.db.DB_PATH", db):
            from app.auth import user_exists
            assert user_exists() is False
