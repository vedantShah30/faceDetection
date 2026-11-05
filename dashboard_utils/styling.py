
import streamlit as st


def apply_dashboard_theme():

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: #0B1120;
        color: #E5E7EB;
    }

    [data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #263247;
    }

    [data-testid="stSidebar"] * {
        color: #D1D5DB;
    }

    .brand {
        font-size: 27px;
        font-weight: 800;
        color: #60A5FA;
        letter-spacing: -1px;
    }

    .brand-subtitle {
        font-size: 10px;
        letter-spacing: 2px;
        color: #94A3B8;
        margin-top: 4px;
        margin-bottom: 30px;
    }

    .page-heading {
        font-size: 30px;
        font-weight: 800;
        color: #F8FAFC;
        letter-spacing: -1px;
    }

    .page-subtitle {
        color: #94A3B8;
        font-size: 14px;
        margin-top: 5px;
        margin-bottom: 25px;
    }

    .section-heading {
        color: #F1F5F9;
        font-size: 18px;
        font-weight: 700;
        margin-top: 15px;
        margin-bottom: 12px;
    }

    [data-testid="stMetric"] {
        background: #172238;
        border: 1px solid #263750;
        padding: 20px;
        border-radius: 14px;
    }

    [data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
    }

    [data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-weight: 700;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #263750;
        border-radius: 12px;
        overflow: hidden;
    }

    .stButton > button {
        border-radius: 9px;
        border: 1px solid #334155;
        background: #172238;
        color: #E2E8F0;
        min-height: 40px;
    }

    .stButton > button:hover {
        border-color: #60A5FA;
        color: #60A5FA;
    }

    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #172238;
    }

    hr {
        border-color: #263247;
    }

    </style>
    """, unsafe_allow_html=True)


def page_header(title, subtitle):

    st.markdown(
        f'<div class="page-heading">{title}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="page-subtitle">{subtitle}</div>',
        unsafe_allow_html=True
    )
