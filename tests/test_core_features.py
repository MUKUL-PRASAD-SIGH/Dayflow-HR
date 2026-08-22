import os
import sqlite3
import pytest
from pathlib import Path
from app.db import init_db, connect_db
from app.auth import _hash_password as hash_password, verify_password, user_exists, validate_password
from app.otp_utils import generate_otp
import datetime

# --- Test DB Setup ---
TEST_DB = Path("test_hr_management.db").resolve()

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    import app.db
    original_db_path = app.db.DB_PATH
    app.db.DB_PATH = TEST_DB
    init_db()
    
    yield
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    app.db.DB_PATH = original_db_path

# --- 1. Authentication Tests ---
def test_password_validation():
    assert not validate_password("short")
    assert validate_password("longenoughpass")

def test_password_hashing():
    pwd = "SecurePassword123"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed)
    assert not verify_password("WrongPassword123", hashed)

def test_user_creation_and_exists():
    conn = connect_db()
    c = conn.cursor()
    # Insert test user
    uid = "EMP999"
    gmail = "emp999@test.com"
    c.execute(
        "INSERT INTO users (id, gmail, password, role, name) VALUES (?, ?, ?, ?, ?)",
        (uid, gmail, hash_password("ValidPassword123"), "employee", "Test Employee")
    )
    conn.commit()
    conn.close()

    assert user_exists(user_id=uid)
    assert user_exists(gmail=gmail)
    assert not user_exists(user_id="UNKNOWN")

def test_generate_otp():
    otp = generate_otp("test@example.com")
    assert len(otp) == 6
    assert otp.isdigit()

# --- 2. Leave Management Tests ---
def test_leave_request_lifecycle():
    conn = connect_db()
    c = conn.cursor()
    
    # 1. Create a leave request
    uid = "EMP999"
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(days=2)
    reason = "Medical checkup"
    
    c.execute(
        """
        INSERT INTO leave_requests 
        (user_id, name, start_date, end_date, reason, status) 
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (uid, "Test Employee", start_date, end_date, reason, "pending")
    )
    req_id = c.lastrowid
    conn.commit()
    
    # 2. Verify it's pending
    c.execute("SELECT status FROM leave_requests WHERE id = ?", (req_id,))
    assert c.fetchone()[0] == "pending"
    
    # 3. Approve it
    hr_comment = "Approved, take care."
    c.execute(
        "UPDATE leave_requests SET status = ?, hr_comment = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        ("approved", hr_comment, req_id)
    )
    conn.commit()
    
    # 4. Verify it's approved
    c.execute("SELECT status, hr_comment FROM leave_requests WHERE id = ?", (req_id,))
    row = c.fetchone()
    assert row[0] == "approved"
    assert row[1] == hr_comment
    conn.close()

if __name__ == "__main__":
    # Allows running directly via `python test_core_features.py`
    pytest.main(["-v", __file__])
