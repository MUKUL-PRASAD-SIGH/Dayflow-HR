import streamlit as st
import os

def inject_custom_css():
    """Reads the custom styling and injects it into the Streamlit app page."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(current_dir, "style.css")
    
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        # Fallback inline minimal style
        st.markdown("""
        <style>
        html, body, [class*="css"], .stApp { font-family: sans-serif; }
        </style>
        """, unsafe_allow_html=True)

def render_badge(text: str, badge_type: str) -> str:
    """Returns the HTML string for a styled badge tag.
    
    badge_type can be: pending, approved, rejected, cancelled, present, absent, half_day, hr, employee
    """
    badge_type = badge_type.lower().replace(" ", "_")
    return f'<span class="custom-badge badge-{badge_type}">{text}</span>'

def render_metric(title: str, value: str, metric_type: str = 'blue') -> str:
    """Returns the HTML string for a custom styled dashboard metric card.
    
    metric_type can be: blue, green, red, orange
    """
    type_class = ""
    if metric_type == 'green':
        type_class = 'metric-box-green'
    elif metric_type == 'red':
        type_class = 'metric-box-red'
    elif metric_type == 'orange':
        type_class = 'metric-box-orange'
        
    return f"""
    <div class="dashboard-metric-box {type_class}">
        <div class="metric-title">{title}</div>
        <div class="metric-val">{value}</div>
    </div>
    """

def render_profile_badge(name: str, user_id: str, role: str) -> str:
    """Returns the HTML string for a profile badge header card."""
    initials = "".join([part[0] for part in name.split() if part])[:2].upper()
    role_badge = render_badge(role.title(), role)
    
    return f"""
    <div class="profile-badge-card">
        <div class="avatar-circle">{initials}</div>
        <div>
            <h2 style="margin: 0 0 4px 0; color: #ffffff; font-family: 'Outfit'; font-size: 22px;">{name}</h2>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 13px; color: #a0aec0;">ID: <b>{user_id}</b></span>
                {role_badge}
            </div>
        </div>
    </div>
    """

def render_glass_card(title: str, body_html: str) -> str:
    """Returns the HTML string for a standard glassmorphic wrapper card."""
    return f"""
    <div class="glass-card">
        <h3 style="margin-top:0; color:#ffffff; font-family:'Outfit';">{title}</h3>
        <div>{body_html}</div>
    </div>
    """
