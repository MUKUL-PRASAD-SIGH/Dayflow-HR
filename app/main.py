"""
app/main.py – Dayflow HR entry point.

Run with:
    streamlit run app/main.py

Handles authentication (login / signup with OTP) and routes users to their
role-based dashboard after login.
"""

import streamlit as st

from app.auth import login_user, signup_user, user_exists, validate_password
from app.db import init_db
from app.otp_utils import (
    clear_otp,
    generate_otp,
    otp_storage,
    send_otp_email,
    verify_otp,
)

# ── Schema bootstrap ──────────────────────────────────────────────────────────
init_db()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dayflow HR",
    page_icon="🧠",
    layout="centered",
)

from app.ui_utils import inject_custom_css
inject_custom_css()

# ── Session-state defaults ────────────────────────────────────────────────────
for key, default in [
    ("logged_in", False),
    ("user_id", ""),
    ("user_role", None),
    ("user_name", ""),
    ("show_login", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# =============================================================================
# AUTH VIEWS  (only shown when not logged in)
# =============================================================================

if not st.session_state.logged_in:

    # ── LOGIN VIEW ────────────────────────────────────────────────────────────
    if st.session_state.show_login:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 style="color: #ffffff; font-size: 3rem; margin-bottom: 0px;">🧠 Dayflow <span style="color: #3363b0;">HR</span></h1>
                <p style="color: #a0aec0; font-size: 1.1rem; margin-top: 5px;">Every workday, perfectly aligned.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.subheader("Login to Your Account")

        with st.form("login_form"):
            uid = st.text_input("Employee ID / Email", key="login_id")
            pwd = st.text_input("Password", type="password", key="login_pass")
            submitted = st.form_submit_button("Login")

        if submitted:
            if uid and pwd:
                result = login_user(uid, pwd)
                if result:
                    # Clear state, set new session
                    st.session_state.clear()
                    st.session_state.logged_in = True
                    st.session_state.user_id = result[0]
                    st.session_state.user_role = result[1]
                    st.session_state.user_name = result[2]
                    st.rerun()
                else:
                    st.error("❌ Invalid ID or password. Please try again.")
            else:
                st.warning("Please enter both ID and password.")

        if st.button("← Back to Sign Up"):
            st.session_state.show_login = False
            st.rerun()

    # ── SIGNUP VIEW ───────────────────────────────────────────────────────────
    else:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 style="color: #ffffff; font-size: 3rem; margin-bottom: 0px;">🧠 Dayflow <span style="color: #3363b0;">HR</span></h1>
                <p style="color: #a0aec0; font-size: 1.1rem; margin-top: 5px;">Every workday, perfectly aligned.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.subheader("Create a New Account")

        # ── OTP Verification Step ─────────────────────────────────────────
        if (
            "signup_data" in st.session_state
            and st.session_state.signup_data.get("otp_sent")
        ):
            signup_data = st.session_state.signup_data
            st.info("📧 An OTP has been sent to your email address. Please check your inbox.")

            entered_otp = st.text_input("Enter OTP", key="otp_input")

            col_verify, col_resend, col_back = st.columns(3)

            with col_verify:
                if st.button("✅ Verify OTP", use_container_width=True):
                    if not entered_otp:
                        st.error("Please enter the OTP.")
                    else:
                        if verify_otp(signup_data["gmail"], entered_otp):
                            # OTP valid → complete registration
                            ok = signup_user(
                                signup_data["id"],
                                signup_data["gmail"],
                                signup_data["password"],
                                signup_data["role"],
                                signup_data["name"],
                            )
                            if ok:
                                clear_otp(signup_data["gmail"])
                                
                                # Log the user in automatically
                                st.session_state.logged_in = True
                                st.session_state.user_id = signup_data["id"]
                                st.session_state.user_role = signup_data["role"]
                                st.session_state.user_name = signup_data["name"]
                                
                                del st.session_state.signup_data
                                st.success("🎉 Account created successfully!")
                                st.rerun()
                            else:
                                st.error(
                                    "Account could not be created. "
                                    "The ID or email may already be in use."
                                )
                        else:
                            signup_data["otp_attempts"] = (
                                signup_data.get("otp_attempts", 0) + 1
                            )
                            remaining = 3 - signup_data["otp_attempts"]
                            if remaining <= 0:
                                st.error("Too many failed attempts. Please sign up again.")
                                clear_otp(signup_data["gmail"])
                                del st.session_state.signup_data
                                st.rerun()
                            else:
                                st.error(
                                    f"Invalid OTP. {remaining} attempt(s) remaining."
                                )

            with col_resend:
                if st.button("🔄 Resend OTP", use_container_width=True):
                    new_otp = generate_otp(signup_data["gmail"])
                    if send_otp_email(signup_data["gmail"], new_otp):
                        st.success("New OTP sent!")
                    else:
                        st.error("Failed to resend OTP. Check your SMTP settings.")

            with col_back:
                if st.button("← Back", use_container_width=True):
                    clear_otp(signup_data["gmail"])
                    del st.session_state.signup_data
                    st.rerun()

        # ── Initial Signup Form ───────────────────────────────────────────
        else:
            with st.form("signup_form"):
                uid = st.text_input("Employee / HR ID", key="signup_id")
                gmail = st.text_input("Email Address", key="signup_gmail")
                name = st.text_input("Full Name", key="signup_name")
                role = st.selectbox("Role", ["employee", "hr"], key="signup_role")
                pwd = st.text_input("Password", type="password", key="signup_pass")
                confirm_pwd = st.text_input(
                    "Confirm Password", type="password", key="signup_confirm"
                )
                submitted = st.form_submit_button("Sign Up")

            if submitted:
                if not all([uid, gmail, name, pwd, confirm_pwd]):
                    st.warning("Please fill in all fields.")
                elif pwd != confirm_pwd:
                    st.error("Passwords do not match.")
                elif not validate_password(pwd):
                    st.error("Password must be at least 8 characters long.")
                elif user_exists(user_id=uid, gmail=gmail):
                    st.error(
                        f"A user with ID '{uid}' or email '{gmail}' already exists."
                    )
                else:
                    otp = generate_otp(gmail)
                    if send_otp_email(gmail, otp):
                        st.session_state.signup_data = {
                            "id": uid,
                            "gmail": gmail,
                            "password": pwd,
                            "role": role,
                            "name": name,
                            "otp_sent": True,
                            "otp_attempts": 0,
                        }
                        st.success("OTP sent to your email!")
                        st.rerun()
                    else:
                        st.error(
                            "Failed to send OTP. Please check your email settings in .env."
                        )

        # Login link
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(":blue[Already have an account?]")
        with col2:
            if st.button("Login →"):
                st.session_state.show_login = True
                st.rerun()


# =============================================================================
# ROLE-BASED DASHBOARDS  (shown after login)
# =============================================================================

if st.session_state.logged_in:
    role = st.session_state.get("user_role", "")
    name = st.session_state.get("user_name", "User")

    if role == "employee":
        from app.leave_employee import employee_leave_page

        st.markdown(f"# 👋 Welcome, :blue[{name}]")
        employee_leave_page()

    elif role == "hr":
        from app.leave_hr import hr_leave_page

        st.markdown(f"# 👋 Welcome, :blue[HR – {name}]")
        hr_leave_page()

    else:
        st.error("⚠️ Invalid user role. Please contact support.")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
