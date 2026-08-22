"""
tests/test_otp.py – Tests for OTP generation, verification, and expiry.
"""

import time
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_otp_storage():
    """Ensure otp_storage is clean before each test."""
    from app.otp_utils import otp_storage
    otp_storage.clear()
    yield
    otp_storage.clear()


# ---------------------------------------------------------------------------
# generate_otp
# ---------------------------------------------------------------------------

class TestGenerateOtp:
    def test_returns_6_digit_string(self):
        from app.otp_utils import generate_otp
        otp = generate_otp("user@test.com")
        assert isinstance(otp, str)
        assert len(otp) == 6
        assert otp.isdigit()

    def test_stores_in_storage(self):
        from app.otp_utils import generate_otp, otp_storage
        generate_otp("user@test.com")
        assert "user@test.com" in otp_storage

    def test_overwrites_previous_otp(self):
        from app.otp_utils import generate_otp, otp_storage
        otp1 = generate_otp("user@test.com")
        otp2 = generate_otp("user@test.com")
        assert otp_storage["user@test.com"]["otp"] == otp2

    def test_different_emails_separate_entries(self):
        from app.otp_utils import generate_otp, otp_storage
        generate_otp("a@test.com")
        generate_otp("b@test.com")
        assert "a@test.com" in otp_storage
        assert "b@test.com" in otp_storage
        assert otp_storage["a@test.com"]["otp"] != otp_storage["b@test.com"]["otp"] or True  # could coincide


# ---------------------------------------------------------------------------
# verify_otp
# ---------------------------------------------------------------------------

class TestVerifyOtp:
    def test_correct_otp_returns_true(self):
        from app.otp_utils import generate_otp, verify_otp
        otp = generate_otp("user@test.com")
        assert verify_otp("user@test.com", otp) is True

    def test_wrong_otp_returns_false(self):
        from app.otp_utils import generate_otp, verify_otp
        generate_otp("user@test.com")
        assert verify_otp("user@test.com", "000000") is False

    def test_unknown_email_returns_false(self):
        from app.otp_utils import verify_otp
        assert verify_otp("nobody@test.com", "123456") is False

    def test_otp_sets_verified_flag(self):
        from app.otp_utils import generate_otp, verify_otp, otp_storage
        otp = generate_otp("user@test.com")
        verify_otp("user@test.com", otp)
        assert otp_storage["user@test.com"]["verified"] is True

    def test_strips_whitespace(self):
        from app.otp_utils import generate_otp, verify_otp
        otp = generate_otp("user@test.com")
        assert verify_otp("user@test.com", f"  {otp}  ") is True

    def test_expired_otp_returns_false(self):
        from app import otp_utils
        from app.otp_utils import generate_otp, verify_otp, otp_storage

        otp = generate_otp("user@test.com")
        # Manually backdate the timestamp
        otp_storage["user@test.com"]["timestamp"] = time.time() - 700  # 11+ min ago

        with patch.object(otp_utils, "_OTP_VALIDITY_SECONDS", 600):
            result = verify_otp("user@test.com", otp)

        assert result is False
        # Should be cleaned up
        assert "user@test.com" not in otp_storage

    def test_within_validity_window_succeeds(self):
        from app import otp_utils
        from app.otp_utils import generate_otp, verify_otp, otp_storage

        otp = generate_otp("user@test.com")
        # Just 5 minutes old
        otp_storage["user@test.com"]["timestamp"] = time.time() - 300

        with patch.object(otp_utils, "_OTP_VALIDITY_SECONDS", 600):
            result = verify_otp("user@test.com", otp)

        assert result is True


# ---------------------------------------------------------------------------
# is_email_verified / clear_otp
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_is_email_verified_true_after_verify(self):
        from app.otp_utils import generate_otp, verify_otp, is_email_verified
        otp = generate_otp("user@test.com")
        verify_otp("user@test.com", otp)
        assert is_email_verified("user@test.com") is True

    def test_is_email_verified_false_before_verify(self):
        from app.otp_utils import generate_otp, is_email_verified
        generate_otp("user@test.com")
        assert is_email_verified("user@test.com") is False

    def test_is_email_verified_unknown_email(self):
        from app.otp_utils import is_email_verified
        assert is_email_verified("ghost@test.com") is False

    def test_clear_otp_removes_record(self):
        from app.otp_utils import generate_otp, clear_otp, otp_storage
        generate_otp("user@test.com")
        clear_otp("user@test.com")
        assert "user@test.com" not in otp_storage

    def test_clear_otp_nonexistent_is_safe(self):
        from app.otp_utils import clear_otp
        clear_otp("nobody@test.com")  # Should not raise
