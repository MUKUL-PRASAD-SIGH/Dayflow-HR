"""Quick import check for all app modules."""
from app.db import init_db, connect_db
init_db()
conn = connect_db()
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [r[0] for r in c.fetchall()])
conn.close()
print("DB OK")

from app.auth import _hash_password, verify_password, login_user, signup_user, user_exists
print("auth.py imports OK")
from app.otp_utils import generate_otp, verify_otp, clear_otp, send_otp_email, otp_storage
print("otp_utils.py imports OK")
from app.leave_employee import employee_leave_page, request_leave_page, show_leave_status, leave_history_page
print("leave_employee.py imports OK")
from app.leave_hr import hr_leave_page, approve_leave_page, employee_details_page
print("leave_hr.py imports OK")
from app.gmail_reader import read_emails, display_emails
print("gmail_reader.py imports OK")
from app.email_classifier import classify_emails_with_gemini
print("email_classifier.py imports OK")
print("ALL IMPORTS PASS")
