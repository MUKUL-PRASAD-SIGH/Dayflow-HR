import streamlit as st
from app.db import connect_db
import pandas as pd
from app.ui_utils import inject_custom_css, render_profile_badge

def get_profile(user_id: str):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.phone, e.address, e.department, e.designation, e.joining_date,
                   u.name, u.gmail, u.role
            FROM users u
            LEFT JOIN employees e ON u.id = e.id
            WHERE u.id = ?
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def update_profile(user_id: str, data: dict):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        # Check if exists
        cursor.execute("SELECT id FROM employees WHERE id = ?", (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute(
                """
                UPDATE employees
                SET phone = ?, address = ?, department = ?, designation = ?, joining_date = ?
                WHERE id = ?
                """,
                (
                    data.get('phone'),
                    data.get('address'),
                    data.get('department'),
                    data.get('designation'),
                    data.get('joining_date'),
                    user_id
                )
            )
        else:
            cursor.execute(
                """
                INSERT INTO employees (id, phone, address, department, designation, joining_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    data.get('phone'),
                    data.get('address'),
                    data.get('department'),
                    data.get('designation'),
                    data.get('joining_date')
                )
            )
        conn.commit()
    finally:
        conn.close()

def profile_page(user_id: str, is_hr: bool = False, view_only: bool = False):
    inject_custom_css()
    profile = get_profile(user_id)
    
    if not profile:
        st.error("User not found.")
        return

    st.markdown(
        render_profile_badge(
            profile.get('name', 'Employee'),
            user_id,
            profile.get('role', 'employee')
        ),
        unsafe_allow_html=True
    )

    # If it's an employee viewing their own, or HR viewing someone else
    with st.form(f"profile_form_{user_id}"):
        st.subheader("Personal Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Name", value=profile.get('name', ''), disabled=True)
            phone = st.text_input("Phone Number", value=profile.get('phone') or '', disabled=view_only)
        with col2:
            st.text_input("Email", value=profile.get('gmail', ''), disabled=True)
            address = st.text_input("Address", value=profile.get('address') or '', disabled=view_only)
            
        st.subheader("Employment Details")
        col3, col4 = st.columns(2)
        
        with col3:
            department = st.text_input("Department", value=profile.get('department') or '', disabled=view_only or not is_hr)
            designation = st.text_input("Designation", value=profile.get('designation') or '', disabled=view_only or not is_hr)
        with col4:
            # For date input, we need to convert string to date object if it exists
            joining_date_val = None
            if profile.get('joining_date'):
                try:
                    joining_date_val = pd.to_datetime(profile['joining_date']).date()
                except:
                    pass
            joining_date = st.date_input("Joining Date", value=joining_date_val, disabled=view_only or not is_hr)
            
        if not view_only:
            submitted = st.form_submit_button("Save Profile")
            if submitted:
                update_data = {
                    'phone': phone,
                    'address': address,
                    'department': department if is_hr else profile.get('department'),
                    'designation': designation if is_hr else profile.get('designation'),
                    'joining_date': str(joining_date) if is_hr else profile.get('joining_date')
                }
                update_profile(user_id, update_data)
                st.success("Profile updated successfully!")
                st.rerun()
