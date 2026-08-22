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
                INSERT INTO leave_requests (user_id, name, start_date, end_date, reason, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
                """,
                (user_id, user_name, str(start_date), str(end_date), reason.strip()),
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
            SELECT id, start_date, end_date, reason, status,
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

        with st.expander(f"{emoji} Leave #{leave['id']} – {status.title()}"):
            col1, col2 = st.columns(2)

            start = _parse_date(leave["start_date"])
            end = _parse_date(leave["end_date"])
            duration = (end - start).days + 1

            with col1:
                st.write(f"**Request ID:** #{leave['id']}")
                st.write(f"**From:** {start}")
                st.write(f"**To:** {end}")
                st.write(f"**Duration:** {duration} day{'s' if duration != 1 else ''}")

            with col2:
                st.markdown(f"**Status:** {emoji} {status.title()}")
                if leave["hr_comment"]:
                    st.write(f"**HR Comment:** {leave['hr_comment']}")

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

    # Sidebar
    st.sidebar.title(f"👤 {st.session_state.get('user_name', 'Employee')}")
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Dashboard", "📝 Request Leave", "📋 Leave Status", "📜 History"],
    )
    st.sidebar.markdown("---")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    st.title("🏝️ Employee Leave Portal")

    if page == "🏠 Dashboard":
        st.subheader("Welcome to your Leave Dashboard")

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
        col1.metric("Total Requests", sum(counts.values()))
        col2.metric("✅ Approved", counts.get("approved", 0))
        col3.metric("🟡 Pending", counts.get("pending", 0))

        show_leave_status(st.session_state.user_id)

    elif page == "📝 Request Leave":
        request_leave_page()

    elif page == "📋 Leave Status":
        show_leave_status(st.session_state.user_id)

    elif page == "📜 History":
        leave_history_page()
