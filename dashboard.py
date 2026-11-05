
import streamlit as st

from dashboard_utils.styling import apply_dashboard_theme

from dashboard_pages import (
    overview,
    students,
    attendance,
    periods,
    analytics,
    reports
)


st.set_page_config(
    page_title="FaceAttend | Admin",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_dashboard_theme()


# -----------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------

with st.sidebar:

    st.markdown(
        '<div class="brand">FaceAttend.</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="brand-subtitle">'
        'SMART ATTENDANCE MANAGEMENT'
        '</div>',
        unsafe_allow_html=True
    )

    st.caption("MAIN MENU")

    selected_page = st.radio(
        "Navigation",
        [
            "Overview",
            "Students",
            "Attendance",
            "Periods",
            "Analytics",
            "Reports"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.caption("ADMINISTRATION")
    st.caption("Face Recognition System")
    st.caption("Version 1.0")


# -----------------------------------------
# PAGE ROUTING
# -----------------------------------------

if selected_page == "Overview":

    overview.render()

elif selected_page == "Students":

    students.render()

elif selected_page == "Attendance":

    attendance.render()

elif selected_page == "Periods":

    periods.render()

elif selected_page == "Analytics":

    analytics.render()

elif selected_page == "Reports":

    reports.render()
