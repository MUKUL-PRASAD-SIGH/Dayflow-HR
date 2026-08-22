"""
app/leave_employee.py – Employee leave management UI.

Fixes applied:
- Replaced sqlite3 context-manager cursor (not supported) with direct cursor usage
- Fixed conn.open check (MySQL-ism → try/except close)
- All DB access goes through app.db.connect_db (no duplicate local copy)
- Fixed leave_history_page() import bug
- Date strings parsed correctly before arithmetic
"""

from datetime import date, datetime

import streamlit as st

from app.db import connect_db
from app.ui_utils import inject_custom_css, render_metric, render_profile_badge, render_badge


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _close(conn) -> None:
    """Safely close a SQLite connection."""
    try:
        if conn:
            conn.close()
    except Exception:
        pass


def _parse_date(value) -> date:
    """Convert a SQLite date string (YYYY-MM-DD) or date object to a date."""
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    raise ValueError(f"Cannot parse date from: {value!r}")


# ---------------------------------------------------------------------------
# Leave request form
# ---------------------------------------------------------------------------

def request_leave_page() -> None:
    """Render the leave request form."""
    st.header("📝 Request Leave")

    if "user_id" not in st.session_state:
        st.error("Please log in first.")
        return

    user_id = st.session_state.user_id
    user_name = st.session_state.get("user_name", "")

    if st.session_state.pop("leave_submitted", False):
        st.success("✅ Leave request submitted successfully!")
        st.balloons()

    with st.form("leave_form"):
        st.subheader("New Leave Request")
        today = date.today()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", min_value=today, value=today)
        with col2:
            end_date = st.date_input("To Date", min_value=start_date, value=start_date)

        leave_type = st.selectbox("Leave Type", ["Paid Leave", "Sick Leave", "Unpaid Leave"])
        reason = st.text_area("Reason for Leave", placeholder="Describe your reason…")
        submitted = st.form_submit_button("Submit Request")

    if submitted:
        if not reason.strip():
            st.error("Please enter a reason for leave.")
            return

        if end_date < start_date:
            st.error("End date cannot be before start date.")
            return

        conn = None
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO leave_requests (user_id, name, leave_type, start_date, end_date, reason, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
                """,
                (user_id, user_name, leave_type, str(start_date), str(end_date), reason.strip()),
            )
            conn.commit()
            st.session_state.leave_submitted = True
            st.rerun()
        except Exception as exc:
            st.error(f"❌ Error submitting request: {exc}")
        finally:
            _close(conn)

    show_leave_status(user_id)


# ---------------------------------------------------------------------------
# Leave status view
# ---------------------------------------------------------------------------

def show_leave_status(user_id: str) -> None:
    """Show all leave requests for the given user."""
    st.subheader("📋 My Leave Requests")

    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, leave_type, start_date, end_date, reason, status,
                   COALESCE(hr_comment, '') AS hr_comment,
                   created_at
            FROM leave_requests
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        leaves = cursor.fetchall()
    except Exception as exc:
        st.error(f"❌ Error loading leave requests: {exc}")
        return
    finally:
        _close(conn)

    if not leaves:
        st.info("No leave requests found. Use the form above to submit one.")
        return

    _STATUS_EMOJI = {
        "pending": "🟡",
        "approved": "✅",
        "rejected": "❌",
        "cancelled": "🔘",
    }

    for leave in leaves:
        status = str(leave["status"]).lower()
        emoji = _STATUS_EMOJI.get(status, "❓")
        badge_html = render_badge(status.title(), status)

        with st.expander(f"{emoji} Leave #{leave['id']} — {leave.get('leave_type', 'Paid Leave')} ({status.title()})"):
            start = _parse_date(leave["start_date"])
            end = _parse_date(leave["end_date"])
            duration = (end - start).days + 1

            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div>
                        <b>Duration:</b> {duration} day{'s' if duration != 1 else ''} ({start} to {end})
                    </div>
                    <div>
                        {badge_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if leave["hr_comment"]:
                st.markdown(f"**HR Comment:** *{leave['hr_comment']}*")

            st.write("**Reason:**")
            st.write(leave["reason"] or "No reason provided.")


# ---------------------------------------------------------------------------
# Leave history (approved only)
# ---------------------------------------------------------------------------

def leave_history_page() -> None:
    """Show only approved leave requests."""
    st.subheader("📜 Leave History (Approved)")

    if "user_id" not in st.session_state:
        st.warning("Please log in.")
        return

    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT start_date, end_date, reason, status
            FROM leave_requests
            WHERE user_id = ? AND status = 'approved'
            ORDER BY start_date DESC
            """,
            (st.session_state.user_id,),
        )
        leaves = cursor.fetchall()
    except Exception as exc:
        st.error(f"❌ Error: {exc}")
        return
    finally:
        _close(conn)

    if not leaves:
        st.info("No approved leave history found.")
        return

    for leave in leaves:
        start = _parse_date(leave["start_date"])
        end = _parse_date(leave["end_date"])
        duration = (end - start).days + 1
        st.markdown(
            f"🟢 **{start} → {end}** ({duration} day{'s' if duration != 1 else ''})  \n"
            f"✏️ **Reason:** {leave['reason']}  \n"
            f"✅ **Status:** Approved\n\n---"
        )


# ---------------------------------------------------------------------------
# Resign stub
# ---------------------------------------------------------------------------

def resign_page() -> None:
    st.subheader("📤 Resignation Request")
    st.warning("This feature is coming soon.")


# ---------------------------------------------------------------------------
# Main employee page (entry point from main.py)
# ---------------------------------------------------------------------------

def employee_leave_page() -> None:
    """Full employee portal with sidebar navigation."""
    if "user_id" not in st.session_state:
        st.error("Please log in to access this page.")
        return

    inject_custom_css()

    # Sidebar
    st.sidebar.title(f"👤 {st.session_state.get('user_name', 'Employee')}")
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Dashboard", "👤 Profile", "🕒 Attendance", "💰 Payroll", "📝 Request Leave", "📋 Leave Status", "📜 History"],
    )
    st.sidebar.markdown("---")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    # Premium Profile Badge Header at top of portal
    st.markdown(
        render_profile_badge(
            st.session_state.get("user_name", "Employee"),
            st.session_state.user_id,
            "employee"
        ),
        unsafe_allow_html=True
    )

    if page == "🏠 Dashboard":
        # Today's Attendance Quick Actions
        st.markdown("### 🕒 Today's Attendance")
        from app.attendance import get_today_attendance, check_in, check_out
        today_rec = get_today_attendance(st.session_state.user_id)
        
        col_a, col_b = st.columns([3, 2])
        with col_a:
            if not today_rec:
                st.markdown(
                    f"<div style='margin-top: 10px;'>Status: {render_badge('Absent', 'absent')}</div>", 
                    unsafe_allow_html=True
                )
            else:
                checkout_str = f" | Out: {today_rec['check_out']}" if today_rec.get('check_out') else ""
                st.markdown(
                    f"<div style='margin-top: 10px;'>Status: {render_badge('Present', 'present')} <span style='color:#a0aec0;font-size:14px;margin-left:10px;'>(In: {today_rec['check_in']}{checkout_str})</span></div>", 
                    unsafe_allow_html=True
                )
        with col_b:
            if not today_rec:
                if st.button("Check In Now", use_container_width=True):
                    check_in(st.session_state.user_id)
                    st.rerun()
            elif not today_rec.get('check_out'):
                if st.button("Check Out Now", use_container_width=True):
                    check_out(st.session_state.user_id)
                    st.rerun()
            else:
                st.markdown("<div style='color:#10b981;font-weight:600;margin-top:10px;'>Done for the day! 🎉</div>", unsafe_allow_html=True)
                    
        st.markdown("### 📋 Leave Overview")

        # Quick stats from DB
        conn = None
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status, COUNT(*) AS cnt FROM leave_requests WHERE user_id = ? GROUP BY status",
                (st.session_state.user_id,),
            )
            counts = {row["status"]: row["cnt"] for row in cursor.fetchall()}
        except Exception:
            counts = {}
        finally:
            _close(conn)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(render_metric("Total Requests", str(sum(counts.values())), 'blue'), unsafe_allow_html=True)
        with col2:
            st.markdown(render_metric("Approved Leaves", str(counts.get("approved", 0)), 'green'), unsafe_allow_html=True)
        with col3:
            st.markdown(render_metric("Pending Leaves", str(counts.get("pending", 0)), 'orange'), unsafe_allow_html=True)

        show_leave_status(st.session_state.user_id)

    elif page == "👤 Profile":
        from app.profile import profile_page
        profile_page(st.session_state.user_id, is_hr=False)

    elif page == "🕒 Attendance":
        from app.attendance import employee_attendance_page
        employee_attendance_page(st.session_state.user_id)
        
    elif page == "💰 Payroll":
        from app.payroll import employee_payroll_page
        employee_payroll_page(st.session_state.user_id)

    elif page == "📝 Request Leave":
        request_leave_page()

    elif page == "📋 Leave Status":
        show_leave_status(st.session_state.user_id)

    elif page == "📜 History":
        leave_history_page()
