
import streamlit as st


def apply_dashboard_theme():
    """
    Global light theme for FaceAttend.
    Presentation-only changes. No database or application logic is modified.
    """

    st.markdown(
        """
        <style>

        /* =========================================
           GLOBAL THEME
        ========================================= */

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --primary: #1D4ED8;
            --primary-dark: #1E3A8A;
            --primary-light: #DBEAFE;
            --teal: #0F766E;

            --background: #F4F7FB;
            --surface: #FFFFFF;
            --surface-secondary: #F8FAFC;

            --text-primary: #172033;
            --text-secondary: #64748B;
            --border: #E2E8F0;

            --success: #15803D;
            --warning: #B45309;
            --danger: #B91C1C;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background-color: var(--background);
            color: var(--text-primary);
        }

        [data-testid="stAppViewContainer"] {
            background-color: var(--background);
        }

        [data-testid="stHeader"] {
            background-color: rgba(244, 247, 251, 0.95);
        }

        [data-testid="stToolbar"] {
            background-color: transparent;
        }

        /* =========================================
           MAIN CONTENT
        ========================================= */

        .main .block-container {
            padding-top: 2.2rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }

        h1, h2, h3, h4, h5 {
            color: var(--text-primary) !important;
            font-weight: 700 !important;
            letter-spacing: -0.4px;
        }

        p, label, span, div {
            font-family: 'Inter', sans-serif;
        }

        [data-testid="stMarkdownContainer"] p {
            color: var(--text-secondary);
        }

        /* =========================================
           SIDEBAR
        ========================================= */

        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] > div {
            background-color: #FFFFFF;
        }

        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: var(--text-primary);
        }

        section[data-testid="stSidebar"] hr {
            border-color: var(--border);
            margin-top: 1.5rem;
            margin-bottom: 1.5rem;
        }

        /* Sidebar navigation labels */

        section[data-testid="stSidebar"] .stRadio label {
            color: #334155 !important;
            font-weight: 500;
            padding: 8px 12px;
            border-radius: 8px;
            transition: all 0.2s ease;
        }

        section[data-testid="stSidebar"] .stRadio label:hover {
            background-color: #EFF6FF;
            color: var(--primary) !important;
        }

        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
            color: #64748B !important;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* =========================================
           PAGE HEADER
        ========================================= */

        .brand-title {
            font-size: 1.8rem;
            font-weight: 800;
            color: var(--primary-dark);
            letter-spacing: -1px;
            margin-bottom: 0.1rem;
        }

        .brand-subtitle {
            font-size: 0.68rem;
            color: #64748B;
            letter-spacing: 2.2px;
            text-transform: uppercase;
            font-weight: 600;
        }

        .page-heading {
            font-size: 1.9rem;
            font-weight: 800;
            color: var(--text-primary);
            letter-spacing: -0.8px;
            margin-bottom: 0.25rem;
        }

        .page-subtitle {
            color: var(--text-secondary);
            font-size: 0.95rem;
            margin-bottom: 1.8rem;
        }

        .section-heading {
            color: var(--text-primary);
            font-size: 1.25rem;
            font-weight: 700;
            margin-top: 1.4rem;
            margin-bottom: 1rem;
        }

        /* =========================================
           METRIC CARDS
        ========================================= */

        [data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px 22px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
            transition: all 0.2s ease;
        }

        [data-testid="stMetric"]:hover {
            border-color: #BFDBFE;
            box-shadow: 0 5px 16px rgba(37, 99, 235, 0.08);
            transform: translateY(-2px);
        }

        [data-testid="stMetricLabel"] {
            color: #64748B !important;
            font-size: 0.9rem !important;
            font-weight: 500 !important;
        }

        [data-testid="stMetricValue"] {
            color: #172554 !important;
            font-size: 2rem !important;
            font-weight: 800 !important;
        }

        [data-testid="stMetricDelta"] {
            font-weight: 600;
        }

        /* Custom metric cards, if used by pages */

        .metric-card {
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px 22px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
        }

        .metric-label {
            color: #64748B;
            font-size: 0.9rem;
            font-weight: 500;
        }

        .metric-value {
            color: #172554;
            font-size: 2rem;
            font-weight: 800;
        }

        /* =========================================
           BUTTONS
        ========================================= */

        .stButton > button,
        .stDownloadButton > button {
            background-color: var(--primary);
            color: #FFFFFF !important;
            border: 1px solid var(--primary);
            border-radius: 9px;
            padding: 0.55rem 1.15rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            background-color: var(--primary-dark);
            border-color: var(--primary-dark);
            color: #FFFFFF !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        }

        .stButton > button:focus,
        .stDownloadButton > button:focus {
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
        }

        /* =========================================
           INPUTS AND SELECT BOXES
        ========================================= */

        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stTimeInput input,
        .stTextArea textarea {
            background-color: #FFFFFF !important;
            color: var(--text-primary) !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 9px !important;
        }

        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stDateInput input:focus,
        .stTextArea textarea:focus {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.12) !important;
        }

        .stSelectbox [data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            border-color: #CBD5E1 !important;
            border-radius: 9px !important;
        }

        .stSelectbox [data-baseweb="select"] *,
        .stMultiSelect [data-baseweb="select"] * {
            color: var(--text-primary) !important;
        }

        [data-testid="stWidgetLabel"] p {
            color: #334155 !important;
            font-weight: 600 !important;
        }

        /* =========================================
           TABS
        ========================================= */

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid var(--border);
        }

        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            color: #64748B !important;
            border-radius: 8px 8px 0 0;
            font-weight: 600;
            padding: 10px 16px;
        }

        .stTabs [aria-selected="true"] {
            color: var(--primary) !important;
            border-bottom: 3px solid var(--primary) !important;
        }

        /* =========================================
           DATAFRAMES AND TABLES
        ========================================= */

        [data-testid="stDataFrame"] {
            background-color: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }

        [data-testid="stTable"] {
            background-color: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 10px;
            overflow: hidden;
        }

        /* =========================================
           EXPANDERS
        ========================================= */

        [data-testid="stExpander"] {
            background-color: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 10px;
        }

        [data-testid="stExpander"] summary {
            color: var(--text-primary) !important;
            font-weight: 600;
        }

        /* =========================================
           ALERTS AND STATUS MESSAGES
        ========================================= */

        [data-testid="stAlert"] {
            border-radius: 10px;
            border: 1px solid var(--border);
        }

        /* =========================================
           DIVIDERS AND SPACING
        ========================================= */

        hr {
            border-color: var(--border) !important;
            margin-top: 1.5rem;
            margin-bottom: 1.5rem;
        }

        /* =========================================
           CHECKBOXES AND RADIO BUTTONS
        ========================================= */

        .stCheckbox label,
        .stRadio label {
            color: #334155 !important;
        }

        /* =========================================
           SCROLLBAR
        ========================================= */

        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #F1F5F9;
        }

        ::-webkit-scrollbar-thumb {
            background: #CBD5E1;
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #94A3B8;
        }

        /* =========================================
           RESPONSIVE SPACING
        ========================================= */

        @media (max-width: 768px) {
            .main .block-container {
                padding: 1.2rem 1rem 2rem 1rem;
            }

            .page-heading {
                font-size: 1.5rem;
            }

            [data-testid="stMetric"] {
                padding: 14px;
            }
        }

        </style>
        """,
        unsafe_allow_html=True
    )


def page_header(title, subtitle=""):
    st.markdown(
        f"""
        <div style="margin-bottom: 1.8rem;">
            <div class="page-heading">{title}</div>
            <div class="page-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
