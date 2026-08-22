import streamlit as st
import datetime
from app.db import connect_db
import pandas as pd

def get_today_attendance(user_id: str):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        today = datetime.date.today()
        cursor.execute(
            "SELECT * FROM attendance WHERE employee_id = ? AND date = ?",
            (user_id, today)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def check_in(user_id: str):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        today = datetime.date.today()
        now = datetime.datetime.now().time().strftime("%H:%M:%S")
        
        # Insert or ignore (if already checked in, don't overwrite)
        cursor.execute(
            """
            INSERT INTO attendance (employee_id, date, check_in, status)
            VALUES (?, ?, ?, 'present')
            """,
            (user_id, today, now)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Check-in error: {e}")
        return False
    finally:
        conn.close()

def check_out(user_id: str):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        today = datetime.date.today()
        now = datetime.datetime.now().time().strftime("%H:%M:%S")
        
        cursor.execute(
            """
            UPDATE attendance
            SET check_out = ?
            WHERE employee_id = ? AND date = ? AND check_out IS NULL
            """,
            (now, user_id, today)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Check-out error: {e}")
        return False
    finally:
        conn.close()

def employee_attendance_page(user_id: str):
    st.header("🕒 Attendance")
    
    today_rec = get_today_attendance(user_id)
    
    st.subheader("Today's Status")
    if not today_rec:
        st.info("You have not checked in today.")
        if st.button("Check In"):
            if check_in(user_id):
                st.success("Checked in successfully!")
                st.rerun()
            else:
                st.error("Check-in failed. You might already be checked in.")
    elif today_rec and not today_rec.get('check_out'):
        st.success(f"Checked in at {today_rec['check_in']}")
        if st.button("Check Out"):
            if check_out(user_id):
                st.success("Checked out successfully!")
                st.rerun()
            else:
                st.error("Check-out failed.")
    else:
        st.success(f"Checked in at {today_rec['check_in']}")
        st.info(f"Checked out at {today_rec['check_out']}")
        st.write("Done for the day!")

    st.markdown("---")
    st.subheader("Attendance History")
    
    conn = connect_db()
    try:
        df = pd.read_sql_query(
            "SELECT date, check_in, check_out, status FROM attendance WHERE employee_id = ? ORDER BY date DESC",
            conn,
            params=(user_id,)
        )
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No attendance history found.")
    finally:
        conn.close()

def hr_attendance_page():
    st.header("🕒 Daily Attendance Overview")
    
    view_date = st.date_input("Select Date", value=datetime.date.today())
    
    conn = connect_db()
    try:
        df = pd.read_sql_query(
            """
            SELECT u.id as Employee_ID, u.name as Name, 
                   COALESCE(a.check_in, '-') as Check_In, 
                   COALESCE(a.check_out, '-') as Check_Out, 
                   COALESCE(a.status, 'absent') as Status
            FROM users u
            LEFT JOIN attendance a ON u.id = a.employee_id AND a.date = ?
            WHERE u.role = 'employee'
            ORDER BY u.name
            """,
            conn,
            params=(view_date,)
        )
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No employees found.")
    finally:
        conn.close()
