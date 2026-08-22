"""
app/leave_hr.py – HR leave management dashboard.

Fixes applied:
- Date strings parsed before arithmetic (SQLite returns strings, not date objects)
- created_at parsed to datetime before .strftime() call
- Removed dependency on streamlit_option_menu for core functionality
  (still used for the sidebar menu, but wrapped in a try/except with fallback)
"""

from datetime import date, datetime

import streamlit as st

from app.db import connect_db
from app.ui_utils import inject_custom_css, render_metric, render_profile_badge, render_badge


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _close(conn) -> None:
    try:
        if conn:
            conn.close()
    except Exception:
        pass


def _parse_date(value) -> date:
    """Convert SQLite date string or date object to a date."""
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    raise ValueError(f"Cannot parse date: {value!r}")


def _parse_datetime(value) -> datetime:
    """Convert SQLite datetime string or datetime object to a datetime."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # SQLite stores as "YYYY-MM-DD HH:MM:SS"
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return datetime.now()  # fallback – never crash the UI


# ---------------------------------------------------------------------------
# Leave request views
# ---------------------------------------------------------------------------

def show_leave_requests(status: str, empty_message: str) -> None:
    """Display leave requests filtered by status, with approve/reject actions."""
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT lr.id, lr.user_id, lr.name, lr.leave_type, lr.start_date, lr.end_date,
                   lr.reason, lr.status, lr.created_at,
                   COALESCE(lr.hr_comment, '') AS hr_comment
            FROM leave_requests lr
            WHERE lr.status = ?
            ORDER BY lr.created_at DESC
            """,
            (status,),
        )
        requests = cursor.fetchall()
    except Exception as exc:
        st.error(f"❌ Error loading {status} requests: {exc}")
        return
    finally:
        _close(conn)

    if not requests:
        st.info(empty_message)
        return

    for req in requests:
        start = _parse_date(req["start_date"])
        end = _parse_date(req["end_date"])
        days = (end - start).days + 1
        created = _parse_datetime(req["created_at"])

        badge_html = render_badge(req['status'].title(), req['status'])
        with st.expander(
            f"📅 {req['name']} — {dict(req).get('leave_type', 'Paid Leave')} ({req['status'].capitalize()})"
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Employee ID:** `{req['user_id']}`")
                st.markdown(f"**Type:** {dict(req).get('leave_type', 'Paid Leave')}")
                st.markdown(f"**Requested On:** {created.strftime('%Y-%m-%d %H:%M')}")
                st.markdown(f"**Status:** {badge_html}", unsafe_allow_html=True)

            with col2:
                st.markdown(f"**From:** {start}")
                st.markdown(f"**To:** {end}")
                st.markdown(f"**Duration:** {days} day{'s' if days != 1 else ''}")

            st.markdown("**Reason:**")
            st.info(req["reason"])

            if req["hr_comment"]:
                st.markdown("**HR Comment:**")
                st.warning(req["hr_comment"])

            # Action buttons (only for pending)
            if status == "pending":
                st.markdown("### Take Action")
                with st.form(key=f"action_form_{req['id']}"):
                    comment = st.text_area(
                        "Comment (optional)",
                        key=f"comment_{req['id']}",
                    )
                    col_a, col_r, _ = st.columns([1, 1, 2])
                    with col_a:
                        approve = st.form_submit_button(
                            "✅ Approve", use_container_width=True
                        )
                    with col_r:
                        reject = st.form_submit_button(
                            "❌ Reject", use_container_width=True
                        )

                if approve:
                    _update_leave_status(req["id"], "approved", comment)
                    st.rerun()
                if reject:
                    _update_leave_status(req["id"], "rejected", comment)
                    st.rerun()

            st.markdown("---")


def _update_leave_status(request_id: int, status: str, comment: str = "") -> None:
    """Persist a status change (approve / reject) with an optional HR comment."""
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        if comment and comment.strip():
            cursor.execute(
                """
                UPDATE leave_requests
                SET status = ?, hr_comment = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, comment.strip(), request_id),
            )
        else:
            cursor.execute(
                """
                UPDATE leave_requests
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, request_id),
            )

        conn.commit()
        st.success(f"✅ Leave request {status} successfully!")

        # Fetch employee name for toast
        cursor.execute("SELECT name FROM leave_requests WHERE id = ?", (request_id,))
        row = cursor.fetchone()
        if row:
            st.toast(f"{row['name']}'s leave has been {status}.")

    except Exception as exc:
        st.error(f"❌ Error updating status: {exc}")
    finally:
        _close(conn)


# ---------------------------------------------------------------------------
# HR Dashboard
# ---------------------------------------------------------------------------

def hr_dashboard_page() -> None:
    st.title("📊 HR Dashboard")
    st.subheader("Workforce Metrics (Today)")
    
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Total employees
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'employee'")
        total_emp = cursor.fetchone()['count']
        
        # Present today
        today = datetime.now().date()
        cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE date = ? AND status = 'present'", (today,))
        present_count = cursor.fetchone()['count']
        
        # On leave today
        cursor.execute(
            """
            SELECT COUNT(DISTINCT user_id) as count 
            FROM leave_requests 
            WHERE status = 'approved' AND start_date <= ? AND end_date >= ?
            """,
            (str(today), str(today))
        )
        leave_count = cursor.fetchone()['count']
        
        absent_count = total_emp - present_count - leave_count
        if absent_count < 0:
            absent_count = 0
            
    except Exception as exc:
        st.error(f"Error loading metrics: {exc}")
        total_emp, present_count, leave_count, absent_count = 0, 0, 0, 0
    finally:
        if conn:
            conn.close()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_metric("Total Employees", str(total_emp), 'blue'), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric("Present Today", str(present_count), 'green'), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric("On Leave", str(leave_count), 'orange'), unsafe_allow_html=True)
    with col4:
        st.markdown(render_metric("Absent Today", str(absent_count), 'red'), unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("Quick Actions")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="glass-card" style="padding:15px; border-left:4px solid #3363b0;">
                <h5 style="margin:0 0 5px 0; color:#ffffff;">📝 Leave Approval</h5>
                <p style="margin:0; font-size:12px; color:#a0aec0;">Review and approve pending employee leave requests.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            """
            <div class="glass-card" style="padding:15px; border-left:4px solid #10b981;">
                <h5 style="margin:0 0 5px 0; color:#ffffff;">💰 Payroll Control</h5>
                <p style="margin:0; font-size:12px; color:#a0aec0;">Configure salary structures and verify net payout totals.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            """
            <div class="glass-card" style="padding:15px; border-left:4px solid #f59e0b;">
                <h5 style="margin:0 0 5px 0; color:#ffffff;">📅 Attendance Tracker</h5>
                <p style="margin:0; font-size:12px; color:#a0aec0;">Monitor daily check-in and check-out logs.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )


# ---------------------------------------------------------------------------
# Employee details
# ---------------------------------------------------------------------------

def employee_details_page() -> None:
    st.subheader("👥 Employee Directory")

    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, gmail, role FROM users ORDER BY name"
        )
        employees = cursor.fetchall()
    except Exception as exc:
        st.error(f"❌ Error: {exc}")
        return
    finally:
        _close(conn)

    if not employees:
        st.info("No employees found in the database.")
        return

    for emp in employees:
        # Count approved leaves
        leave_count = 0
        conn2 = None
        try:
            conn2 = connect_db()
            c2 = conn2.cursor()
            c2.execute(
                "SELECT COUNT(*) AS cnt FROM leave_requests WHERE user_id = ? AND status = 'approved'",
                (emp["id"],),
            )
            row = c2.fetchone()
            leave_count = row["cnt"] if row else 0
        except Exception:
            pass
        finally:
            _close(conn2)

        initials = "".join([part[0] for part in emp['name'].split() if part])[:2].upper()
        role_badge = render_badge(emp['role'].title(), emp['role'])
        st.markdown(
            f"""
            <div class="glass-card" style="padding: 18px 24px;">
              <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
                <div style="display:flex;align-items:center;">
                  <div class="avatar-circle">{initials}</div>
                  <div>
                    <h4 style="margin:0 0 4px 0; color:#ffffff; font-family:'Outfit';">
                      {emp['name']}
                      {role_badge}
                    </h4>
                    <p style="margin:2px 0; color:#a0aec0; font-size:13px;">🆔 {emp['id']}</p>
                    <p style="margin:2px 0; color:#a0aec0; font-size:13px;">📧 {emp['gmail']}</p>
                  </div>
                </div>
                <div style="text-align:right;">
                  <span class="custom-badge badge-approved" style="font-size:12px; font-weight:600; padding: 6px 14px;">
                    Approved Leaves: <b>{leave_count}</b>
                  </span>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Approve/reject leave page (tabs)
# ---------------------------------------------------------------------------

def approve_leave_page() -> None:
    st.title("📋 Leave Requests")
    st.markdown("---")

    if st.session_state.get("user_role") != "hr":
        st.warning("⛔ You don't have permission to access this page.")
        return

    tab_pending, tab_approved, tab_rejected = st.tabs(
        ["⏳ Pending", "✅ Approved", "❌ Rejected"]
    )

    with tab_pending:
        show_leave_requests("pending", "No pending leave requests! 🎉")
    with tab_approved:
        show_leave_requests("approved", "No approved leave requests yet.")
    with tab_rejected:
        show_leave_requests("rejected", "No rejected leave requests.")


# ---------------------------------------------------------------------------
# HR Portal entry point (from main.py)
# ---------------------------------------------------------------------------

def hr_leave_page() -> None:
    """Render the full HR portal with sidebar navigation."""
    inject_custom_css()

    st.markdown(
        render_profile_badge(
            st.session_state.get("user_name", "HR Officer"),
            st.session_state.user_id,
            "hr"
        ),
        unsafe_allow_html=True
    )

    # Try to use streamlit-option-menu; fall back to st.sidebar.radio
    try:
        from streamlit_option_menu import option_menu

        with st.sidebar:
            selected = option_menu(
                menu_title="HR Portal",
                options=["Dashboard", "Leave Requests", "Employee Directory", "Profiles", "Attendance", "Payroll", "Email", "Logout"],
                icons=["speedometer2", "clipboard-check", "people", "person-badge", "clock-history", "currency-dollar", "envelope", "box-arrow-right"],
                menu_icon="briefcase",
                default_index=0,
                styles={
                    "container": {"padding": "5!important", "background-color": "#000"},
                    "icon": {"color": "white", "font-size": "22px"},
                    "nav-link": {
                        "color": "white",
                        "font-size": "18px",
                        "--hover-color": "#3363b0",
                    },
                    "nav-link-selected": {"background-color": "#3363b0"},
                },
            )
    except ImportError:
        selected = st.sidebar.radio(
            "HR Portal",
            ["Dashboard", "Leave Requests", "Employee Directory", "Profiles", "Attendance", "Payroll", "Email", "Logout"],
        )

    if selected == "Dashboard":
        hr_dashboard_page()
        
    elif selected == "Leave Requests":
        approve_leave_page()

    elif selected == "Employee Directory":
        employee_details_page()
        
    elif selected == "Profiles":
        _render_profiles_page()

    elif selected == "Attendance":
        from app.attendance import hr_attendance_page
        hr_attendance_page()
        
    elif selected == "Payroll":
        from app.payroll import hr_payroll_page
        hr_payroll_page()

    elif selected == "Email":
        _render_email_page()

    elif selected == "Logout":
        st.session_state.clear()
        st.rerun()

def _render_profiles_page() -> None:
    st.subheader("👤 Manage Employee Profiles")
    conn = None
    try:
        from app.db import connect_db
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users ORDER BY name")
        employees = cursor.fetchall()
    except Exception as exc:
        st.error(f"Error fetching employees: {exc}")
        return
    finally:
        if conn:
            conn.close()
            
    if not employees:
        st.info("No employees found.")
        return
        
    options = {f"{emp['name']} ({emp['id']})": emp['id'] for emp in employees}
    selected_name = st.selectbox("Select Employee", list(options.keys()))
    if selected_name:
        selected_id = options[selected_name]
        st.markdown("---")
        from app.profile import profile_page
        profile_page(selected_id, is_hr=True)


# ---------------------------------------------------------------------------
# Email integration (Gmail + Gemini AI)
# ---------------------------------------------------------------------------

def _render_email_page() -> None:
    st.title("📬 Email Dashboard")

    if st.button("🔄 Refresh Emails"):
        st.rerun()

    try:
        from app.gmail_reader import display_emails, read_emails
        from app.email_classifier import classify_emails_with_gemini, parse_resume_with_gemini
    except ImportError as exc:
        st.error(f"Email modules not available: {exc}")
        return

    with st.spinner("Fetching emails…"):
        emails = read_emails(max_results=15)

    if not emails:
        st.warning("No emails found, or there was an error fetching your inbox.")
        return

    tab_all, tab_ai = st.tabs(["📧 All Emails", "🤖    with tab_ai:
        st.subheader("🤖 Smart Email Classification")
        with st.spinner("Analysing with Gemini AI…"):
            result = classify_emails_with_gemini(emails)

        if result:
            category_emoji = {
                "Job Application": "📄",
                "Important": "🚨", 
                "General": "📂", 
                "Spam": "🗑️"
            }
            category_badge_type = {
                "Job Application": "employee",
                "Important": "rejected",
                "General": "hr",
                "Spam": "cancelled"
            }
            
            for category in ["Job Application", "Important", "General", "Spam"]:
                mails = result.get(category, [])
                badge_lbl = render_badge(category, category_badge_type[category])
                with st.expander(
                    f"{category_emoji[category]} {category} ({len(mails)})",
                    expanded=(category in ["Job Application", "Important"]),
                ):
                    if mails:
                        for mail in mails:
                            subject = mail.get("subject", "(no subject)")
                            sender = mail.get("from", "")
                            
                            st.markdown(
                                f"""
                                <div class="glass-card" style="padding: 12px 18px; margin-bottom: 8px; border-left: 3px solid #3363b0;">
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <div>
                                            <b style="font-size:14px; color:#ffffff;">{subject}</b>
                                            <div style="font-size:12px; color:#a0aec0; margin-top:3px;">From: {sender}</div>
                                        </div>
                                        <div>
                                            {badge_lbl}
                                        </div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            
                            # Parse Resume if it's a Job Application
                            if category == "Job Application":
                                if st.button(f"🔍 AI Analyze Resume", key=f"analyze_{mail['id']}", use_container_width=True):
                                    with st.spinner("Extracting intelligence..."):
                                        parsed = parse_resume_with_gemini(mail.get("body", ""))
                                        if parsed:
                                            candidate_name = parsed.get('Candidate Name', 'Unknown')
                                            role_applied = parsed.get('Role Applied For', 'None Specified')
                                            experience = parsed.get('Years of Experience', 'Unknown')
                                            education = parsed.get('Education', 'Unknown')
                                            skills = parsed.get('Skills', [])
                                            summary = parsed.get('Summary', 'No summary provided.')
                                            
                                            skills_tags = " ".join([f"<span class='custom-badge badge-employee' style='margin-right:5px; margin-bottom:5px;'>{s}</span>" for s in skills])
                                            
                                            st.markdown(
                                                f"""
                                                <div class="glass-card" style="border: 1px solid rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.05); padding: 18px; margin-top: 10px;">
                                                    <h4 style="margin: 0 0 12px 0; color: #10b981; font-family: 'Outfit';">🎯 Candidate Parse Success</h4>
                                                    <div style="font-size: 14px; margin-bottom: 6px;"><b>Candidate Name:</b> {candidate_name}</div>
                                                    <div style="font-size: 14px; margin-bottom: 6px;"><b>Role Applied For:</b> {role_applied}</div>
                                                    <div style="font-size: 14px; margin-bottom: 6px;"><b>Years of Experience:</b> {experience}</div>
                                                    <div style="font-size: 14px; margin-bottom: 6px;"><b>Education:</b> {education}</div>
                                                    <div style="margin-bottom: 12px; font-size: 14px;"><b>Skills:</b><br>{skills_tags if skills_tags else 'None listed'}</div>
                                                    <div style="padding: 10px; background: rgba(255,255,255,0.04); border-radius: 8px; border-left: 3px solid #10b981; font-style: italic; font-size:13px; color:#e2e8f0;">
                                                        "{summary}"
                                                    </div>
                                                </div>
                                                """,
                                                unsafe_allow_html=True
                                            )
                                        else:
                                            st.error("Failed to parse resume intelligence.")
                                st.markdown("---")
                    else:
                        st.info("No emails in this category.")
        else:
            st.error("Classification failed. Check your GEMINI_API_KEY in .env.")")
        else:
            st.error("Classification failed. Check your GEMINI_API_KEY in .env.")
