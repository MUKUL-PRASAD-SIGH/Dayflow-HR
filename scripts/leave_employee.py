import streamlit as st
import sqlite3
import os
from datetime import datetime, date

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hr_management.db')

# Database connection function
def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        return None

def request_leave_page():
    """Simplified leave request page"""
    st.header("📝 Request Leave")
    
    # Check if user is logged in
    if 'user_id' not in st.session_state:
        st.error("Please log in first")
        return
        
    user_id = st.session_state.user_id
    name = st.session_state.user_name
    
    # Show success message if redirected after submission
    if 'leave_submitted' in st.session_state and st.session_state.leave_submitted:
        st.success("✅ Leave request submitted successfully!")
        st.balloons()
        del st.session_state.leave_submitted
    
    # Leave request form
    with st.form("leave_form"):
        st.subheader("New Leave Request")
        today = date.today()
        
        # Date inputs
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", min_value=today)
        with col2:
            end_date = st.date_input("To Date", min_value=start_date)
            
        reason = st.text_area("Reason", placeholder="Enter reason for leave")
        submit = st.form_submit_button("Submit Request")
    
    # Handle form submission
    if submit:
        if not reason.strip():
            st.error("Please enter a reason for leave")
            return
            
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                st.error("❌ Could not connect to database")
                return
                
            with conn.cursor() as cursor:
                # Insert new leave request
                sql = """
                INSERT INTO leave_requests 
                (user_id, name, start_date, end_date, reason, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
                """
                cursor.execute(sql, (user_id, name, start_date, end_date, reason))
                conn.commit()
                
                # Set success flag and reload
                st.session_state.leave_submitted = True
                st.rerun()
                
        except Exception as e:
            st.error(f"Error submitting leave request: {e}")
        finally:
            if conn and hasattr(conn, 'open') and conn.open:
                conn.close()
    
    # Show leave status
    show_leave_status(user_id)

def show_leave_status(user_id):
    """Display leave status for the user"""
    st.subheader("📋 My Leave Status")
    
    # Fetch leave requests
    leaves = []
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            st.error("❌ Could not connect to database")
            return
            
        with conn.cursor() as cursor:
            # Get leave requests for this user
            cursor.execute("""
                SELECT id, start_date, end_date, reason, status, 
                       COALESCE(hr_comment, '') as hr_comment,
                       created_at
                FROM leave_requests 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            leaves = cursor.fetchall()
            
    except Exception as e:
        st.error(f"Error fetching leave requests: {e}")
        return
    finally:
        if conn and hasattr(conn, 'open') and conn.open:
            conn.close()
    
    # Display leave requests
    if not leaves:
        st.info("No leave requests found. Submit a request above.")
        return
    
    # Show each leave request
    for leave in leaves:
        # Format status with emoji
        status = leave.get('status', 'pending').lower()
        status_emoji = {
            'pending': '🟡',
            'approved': '✅',
            'rejected': '❌',
            'cancelled': '❌'
        }.get(status, '❓')
        
        # Format dates
        start_date = leave.get('start_date')
        end_date = leave.get('end_date')
        
        # Create a simple display
        with st.expander(f"{status_emoji} Leave #{leave.get('id')} - {status.title()}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Request ID:** #{leave.get('id')}")
                if start_date and end_date:
                    st.write(f"**From:** {start_date}")
                    st.write(f"**To:** {end_date}")
                
                # Calculate duration if possible
                try:
                    if start_date and end_date:
                        if isinstance(start_date, str):
                            start_date = datetime.strptime(str(start_date), '%Y-%m-%d').date()
                        if isinstance(end_date, str):
                            end_date = datetime.strptime(str(end_date), '%Y-%m-%d').date()
                        duration = (end_date - start_date).days + 1
                        st.write(f"**Duration:** {duration} day{'s' if duration > 1 else ''}")
                except Exception as e:
                    print(f"Error calculating duration: {e}")
            
            with col2:
                status_display = f"**Status:** {status_emoji} {status.title()}"
                st.markdown(status_display)
                
                if leave.get('hr_comment'):
                    st.write(f"**HR Comment:** {leave.get('hr_comment')}")
            
            st.write("**Reason:**")
            st.write(leave.get('reason', 'No reason provided'))

def leave_status_page():
    """Main leave status page that shows the status of all leave requests"""
    if "user_id" not in st.session_state:
        st.warning("Please log in to view your leave status.")
        return
        
    st.title("My Leave Status")
    show_leave_status(st.session_state.user_id)

def leave_history_page():
    st.subheader("📜 Leave History (Approved Only)")
    
    con = None
    cur = None
    try:
        con = connect_db()
        cur = con.cursor()

        query = """
            SELECT start_date, end_date, reason, status
            FROM leave_requests
            WHERE user_id = ? AND status = 'approved'
            ORDER BY start_date DESC
        """
        cur.execute(query, (st.session_state.user_id,))
        leaves = cur.fetchall()

        if leaves:
            for leave in leaves:
                # Convert the row to a dictionary for easier access
                leave_dict = {
                    'start_date': leave[0],
                    'end_date': leave[1],
                    'reason': leave[2],
                    'status': leave[3].capitalize() if leave[3] else 'Pending'
                }
                
                st.markdown(
                    f"""
                    🟢 **{leave_dict['start_date']} to {leave_dict['end_date']}**  
                    ✏️ **Reason:** {leave_dict['reason']}  
                    ✅ **Status:** {leave_dict['status']}
                    ---
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No approved leave history found.")

    except Exception as e:
        st.error(f"Something went wrong: {e}")

    finally:
        if cur: cur.close()
        if con: con.close()

def resign_page():
    st.subheader("Resign Request")
    if st.button("Submit Resignation"):
        st.success("Resignation submitted successfully!")  # Replace with DB logic if needed

def employee_leave_page():
    """Main employee leave management page with simplified navigation"""
    # Check if user is logged in
    if 'user_id' not in st.session_state:
        st.error("Please log in to access this page")
        return
    
    # Sidebar navigation
    st.sidebar.title(f"👤 {st.session_state.get('user_name', 'Employee')}")
    
    # Navigation options
    nav_options = ["🏠 Dashboard", "📝 Request Leave", "📋 Leave Status"]
    selected = st.sidebar.radio("Navigation", nav_options)
    
    # Main content area
    st.title("🏝️ Employee Leave Management")
    
    # Show appropriate page based on selection
    if selected == "🏠 Dashboard":
        st.subheader("Welcome to your Leave Dashboard")
        st.write("Use the menu to manage your leave requests.")
        
        # Quick stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Leave Requests", "5")
        with col2:
            st.metric("Approved", "3")
        with col3:
            st.metric("Pending", "2")
        
        # Show recent leave requests
        show_leave_status(st.session_state.user_id)
        
    elif selected == "📝 Request Leave":
        request_leave_page()
        
    elif selected == "📋 Leave Status":
        show_leave_status(st.session_state.user_id)
    
    # Logout button at bottom of sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_role = None
        st.rerun()
