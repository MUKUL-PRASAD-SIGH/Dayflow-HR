import streamlit as st
import pandas as pd
from app.db import connect_db
from app.ui_utils import inject_custom_css, render_metric

def get_payroll(user_id: str):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT p.basic_salary, p.allowances, p.deductions,
                   (p.basic_salary + p.allowances - p.deductions) as net_salary,
                   p.updated_at, u.name
            FROM payroll p
            JOIN users u ON p.employee_id = u.id
            WHERE p.employee_id = ?
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def update_payroll(user_id: str, basic: float, allowances: float, deductions: float):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM payroll WHERE employee_id = ?", (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute(
                """
                UPDATE payroll
                SET basic_salary = ?, allowances = ?, deductions = ?, updated_at = CURRENT_TIMESTAMP
                WHERE employee_id = ?
                """,
                (basic, allowances, deductions, user_id)
            )
        else:
            cursor.execute(
                """
                INSERT INTO payroll (employee_id, basic_salary, allowances, deductions)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, basic, allowances, deductions)
            )
        conn.commit()
    finally:
        conn.close()

def employee_payroll_page(user_id: str):
    inject_custom_css()
    st.header("💰 My Payroll")
    
    payroll = get_payroll(user_id)
    if not payroll:
        st.info("No payroll information available. Please contact HR.")
        return
        
    st.subheader(f"Salary Structure for {payroll['name']}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_metric("Basic Salary", f"${payroll['basic_salary']:,.2f}", 'blue'), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric("Allowances", f"${payroll['allowances']:,.2f}", 'green'), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric("Deductions", f"${payroll['deductions']:,.2f}", 'orange'), unsafe_allow_html=True)
    with col4:
        st.markdown(render_metric("Net Salary", f"${payroll['net_salary']:,.2f}", 'green'), unsafe_allow_html=True)
    
    st.caption(f"Last updated: {payroll['updated_at']}")

def hr_payroll_page():
    inject_custom_css()
    st.header("💰 Manage Payroll")
    
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users WHERE role = 'employee' ORDER BY name")
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
        
        payroll = get_payroll(selected_id)
        
        if payroll:
            st.markdown("### Current Salary Structure")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(render_metric("Basic Salary", f"${payroll['basic_salary']:,.2f}", 'blue'), unsafe_allow_html=True)
            with col2:
                st.markdown(render_metric("Allowances", f"${payroll['allowances']:,.2f}", 'green'), unsafe_allow_html=True)
            with col3:
                st.markdown(render_metric("Deductions", f"${payroll['deductions']:,.2f}", 'orange'), unsafe_allow_html=True)
            with col4:
                st.markdown(render_metric("Net Salary", f"${payroll['net_salary']:,.2f}", 'green'), unsafe_allow_html=True)
            st.markdown("---")

        with st.form(f"payroll_form_{selected_id}"):
            st.subheader("Update Salary Details")
            
            basic = st.number_input("Basic Salary ($)", min_value=0.0, value=float(payroll['basic_salary']) if payroll else 0.0, step=100.0)
            allowances = st.number_input("Allowances ($)", min_value=0.0, value=float(payroll['allowances']) if payroll else 0.0, step=10.0)
            deductions = st.number_input("Deductions ($)", min_value=0.0, value=float(payroll['deductions']) if payroll else 0.0, step=10.0)
            
            submitted = st.form_submit_button("Update Payroll")
            if submitted:
                update_payroll(selected_id, basic, allowances, deductions)
                st.success("Payroll updated successfully!")
                st.rerun()
