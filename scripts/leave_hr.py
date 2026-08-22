# leave_hr.py
import streamlit as st
from db import connect_db
from streamlit_option_menu import option_menu

def approve_leave_page():
    st.title("📋 Leave Requests Dashboard")
    st.markdown("---")

    # Only HR can access this page
    if st.session_state.user_role != 'hr':
        st.warning("⛔ You don't have permission to access this page.")
        return

    # Add tabs for different statuses
    tab1, tab2, tab3 = st.tabs(["⏳ Pending", "✅ Approved", "❌ Rejected"])
    
    with tab1:
        show_leave_requests('pending', "No pending leave requests! 🎉")
    
    with tab2:
        show_leave_requests('approved', "No approved leave requests yet.")
    
    with tab3:
        show_leave_requests('rejected', "No rejected leave requests.")

def show_leave_requests(status, empty_message):
    """Helper function to display leave requests by status"""
    conn = None
    cursor = None
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get leave requests with the specified status
        cursor.execute("""
            SELECT lr.id, lr.user_id, lr.name, lr.start_date, lr.end_date, 
                   lr.reason, lr.status, lr.created_at,
                   COALESCE(lr.hr_comment, '') as hr_comment
            FROM leave_requests lr
            WHERE lr.status = ?
            ORDER BY lr.created_at DESC
        """, (status,))
        
        requests = cursor.fetchall()
        
        if not requests:
            st.info(empty_message)
            return
        
        # Display each request
        for req in requests:
            with st.container():
                # Calculate days requested
                days = (req['end_date'] - req['start_date']).days + 1
                
                # Create expandable section for each request
                with st.expander(f"📅 {req['name']} - {days} day{'s' if days > 1 else ''} ({req['start_date']} to {req['end_date']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Employee ID:** {req['user_id']}")
                        st.markdown(f"**Requested On:** {req['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        st.markdown(f"**Status:** {req['status'].capitalize()}")
                    
                    with col2:
                        st.markdown(f"**From:** {req['start_date']}")
                        st.markdown(f"**To:** {req['end_date']}")
                        st.markdown(f"**Duration:** {days} day{'s' if days > 1 else ''}")
                    
                    st.markdown("**Reason:**")
                    st.info(req['reason'])
                    
                    # Show HR comment if available
                    if req['hr_comment']:
                        st.markdown("**Your Comment:**")
                        st.warning(req['hr_comment'])
                    
                    # Action buttons for pending requests
                    if status == 'pending':
                        st.markdown("### Take Action")
                        
                        # Use a form to handle the comment and action together
                        with st.form(key=f"action_form_{req['id']}"):
                            comment = st.text_area("Add a comment (optional)", 
                                                key=f"comment_{req['id']}",
                                                help="Add any notes for the employee")
                            
                            col1, col2, _ = st.columns([1, 1, 2])
                            with col1:
                                if st.form_submit_button("✅ Approve", use_container_width=True):
                                    update_leave_status(req['id'], 'approved', comment)
                                    st.rerun()
                            with col2:
                                if st.form_submit_button("❌ Reject", use_container_width=True):
                                    update_leave_status(req['id'], 'rejected', comment)
                                    st.rerun()
                    
                    st.markdown("---")  # Divider between requests
    
    except Exception as e:
        st.error(f"❌ Error loading {status} leave requests: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_leave_status(request_id, status, comment=None):
    """Update the status of a leave request and add optional HR comment"""
    conn = None
    cursor = None
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Update the leave request status and add HR comment if provided
        if comment and comment.strip():
            cursor.execute(
                """
                UPDATE leave_requests 
                SET status = ?, 
                    hr_comment = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, comment.strip(), request_id)
            )
        else:
            cursor.execute(
                """
                UPDATE leave_requests 
                SET status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, request_id)
            )
            
        conn.commit()
        st.success(f"✅ Leave request {status} successfully!")
        
        # Get request details for notification
        cursor.execute(
            "SELECT user_id, name, start_date, end_date FROM leave_requests WHERE id = ?",
            (request_id,)
        )
        req = cursor.fetchone()
        
        if req:
            # In a real app, you might want to send an email notification here
            st.toast(f"Notification: {req[1]}'s leave request has been {status}")
    
    except Exception as e:
        error_msg = f"❌ Error updating leave status: {str(e)}"
        st.error(error_msg)
        import traceback
        st.error(f"Technical details: {traceback.format_exc()}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def employee_details_page():
    st.subheader("Employee Details")
    con = None
    cur = None
    try:
        # Connect to database
        con = connect_db()
        if not con:
            st.error("Failed to connect to database")
            return
            
        cur = con.cursor()
        
        # Get all employees from users table
        cur.execute("""
            SELECT id, name, gmail, role 
            FROM users 
            WHERE role = 'employee' OR role = 'hr'
            ORDER BY name
        """)

        employees = cur.fetchall()
        
        if not employees:
            st.info("No employees found in the database.")
            return

        for emp in employees:
            user_id = emp['id']
            
            # Count approved leaves for this user
            leave_count = 0
            try:
                cur.execute("""
                    SELECT COUNT(*) as count 
                    FROM leave_requests 
                    WHERE user_id = ? AND status = 'approved'
                """, (user_id,))
                result = cur.fetchone()
                leave_count = result['count'] if result else 0
            except Exception as e:
                st.warning(f"Could not fetch leave count for user {user_id}: {e}")

            # Display employee card
            st.markdown(
                f"""
                <div style='
                    background-color: #262525; 
                    padding: 15px; 
                    border-radius: 10px; 
                    margin-bottom: 15px;
                    border: 2px solid #F7F7F7;
                '>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <h4 style='margin: 0 0 10px 0;'>{emp['name']} <span style='font-size: 0.9em; color: #888;'>({emp['role'].title()})</span></h4>
                        <p style='margin: 5px 0;'><b>🆔 ID:</b> {emp['id']}</p>
                        <p style='margin: 5px 0;'><b>📧 Email:</b> {emp['gmail']}</p>
                    </div>
                    <div style='text-align: right;'>
                        <div style='background-color: #333; padding: 5px 10px; border-radius: 15px; display: inline-block;'>
                            <b>📝 Leaves:</b> {leave_count}
                        </div>
                    </div>
                </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    except Exception as e:
        st.error(f"Database error: {str(e)}")
        import traceback
        st.text(traceback.format_exc())
        
    finally:
        if cur:
            try:
                cur.close()
            except:
                pass
        if con:
            try:
                con.close()
            except:
                pass


def hr_leave_page():
    class MultiApp:
        def __init__(self):
            self.apps = []

        def add_app(self, title, func):
            self.apps.append({
                "title": title,
                "function": func
            })

        def run(self):
            with st.sidebar:
                app = option_menu(
                    menu_title='HR Portal',
                    options=[
                        'Approve/Reject Leave', 
                        'Employee Details', 
                        'Email', 
                        'Logout'
                    ],
                    icons=['check2-square', 'people', 'envelope', 'box-arrow-left'],
                    menu_icon='briefcase',
                    default_index=0,
                    styles={
                        "container": {"padding": "5!important", "background-color": '#000'},
                        "icon": {"color": "white", "font-size": "23px"},
                        "nav-link": {"color": "white", "font-size": "20px", "--hover-color": "#3363b0"},
                        "nav-link-selected": {"background-color": "#3363b0"},
                    }
                )

            if app == "Approve/Reject Leave":
                approve_leave_page()
            elif app == "Employee Details":
                employee_details_page()
            elif app == "Email":
                from gmail_reader import read_emails, display_emails
                from email_classifier import classify_emails_with_gemini
                import time

                st.title("📬 Email Dashboard")
                
                # Add a refresh button
                if st.button("🔄 Refresh Emails"):
                    st.rerun()
                
                # Show loading spinner while fetching emails
                with st.spinner("Fetching your emails..."):
                    emails = read_emails(max_results=15)
                
                if not emails:
                    st.warning("No emails found or there was an error fetching your emails.")
                else:
                    # Display emails in a tabbed interface
                    tab1, tab2 = st.tabs(["📧 All Emails", "🔍 Smart Classification"])
                    
                    with tab1:
                        st.subheader("Your Inbox")
                        display_emails(emails)
                    
                    with tab2:
                        st.subheader("Smart Email Classification")
                        st.info("Classifying emails using AI...")
                        try:
                            with st.spinner("Analyzing emails with Gemini AI..."):
                                result = classify_emails_with_gemini(emails)
                                
                            if result:
                                category_emojis = {
                                    "Important": "🚨",
                                    "General": "📂",
                                    "Spam": "📢"
                                }

                                # Rename categories
                                renamed_result = {
                                    "Important": result.get("Important", []),
                                    "General": result.get("General", []),
                                    "Spam": result.get("Spam", [])
                                }

                                for category in ["Important", "General", "Spam"]:
                                    with st.expander(f"{category_emojis[category]} {category} Emails", expanded=True):
                                        if renamed_result[category]:
                                            for mail in renamed_result[category]:
                                                st.write(f"➡️ {mail}")
                                        else:
                                            st.info("No emails in this category.")
                            else:
                                st.error("Failed to classify emails. Please try again later.")
                        except Exception as e:
                            st.error(f"An error occurred during email classification: {str(e)}")


            elif app == "Logout":
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.user_role = None
                st.rerun()

    app = MultiApp()
    app.run()
