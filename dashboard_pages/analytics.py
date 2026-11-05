
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import database

from dashboard_utils.styling import page_header


# ==================================================
# DATABASE HELPERS
# ==================================================

def fetch_dataframe(query, params=()):

    with database.get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


def get_closed_periods(start_date=None, end_date=None):

    query = """
        SELECT id, subject, date, start_time, end_time
        FROM periods
        WHERE status = 'closed'
    """

    params = []

    if start_date:
        query += " AND date >= ?"
        params.append(start_date.isoformat())

    if end_date:
        query += " AND date <= ?"
        params.append(end_date.isoformat())

    query += " ORDER BY date"

    return fetch_dataframe(query, tuple(params))


def get_student_attendance(start_date=None, end_date=None):

    query = """
        SELECT
            s.id AS student_id,
            s.name,
            s.roll_number,
            COUNT(DISTINCT p.id) AS total_classes,
            COUNT(DISTINCT a.period_id) AS attended_classes
        FROM students s
        CROSS JOIN periods p
        LEFT JOIN attendance a
            ON a.student_id = s.id
            AND a.period_id = p.id
        WHERE s.is_active = 1
          AND p.status = 'closed'
    """

    params = []

    if start_date:
        query += " AND p.date >= ?"
        params.append(start_date.isoformat())

    if end_date:
        query += " AND p.date <= ?"
        params.append(end_date.isoformat())

    query += """
        GROUP BY s.id, s.name, s.roll_number
        ORDER BY s.roll_number
    """

    df = fetch_dataframe(query, tuple(params))

    if not df.empty:

        df["absent_classes"] = (
            df["total_classes"] - df["attended_classes"]
        )

        df["attendance_percentage"] = (
            df["attended_classes"]
            / df["total_classes"].replace(0, 1)
            * 100
        )

    return df


def get_subject_statistics(start_date=None, end_date=None):

    query = """
        SELECT
            p.subject,
            COUNT(DISTINCT p.id) AS total_periods,
            COUNT(a.id) AS total_present
        FROM periods p
        LEFT JOIN attendance a
            ON a.period_id = p.id
        WHERE p.status = 'closed'
    """

    params = []

    if start_date:
        query += " AND p.date >= ?"
        params.append(start_date.isoformat())

    if end_date:
        query += " AND p.date <= ?"
        params.append(end_date.isoformat())

    query += """
        GROUP BY p.subject
        ORDER BY p.subject
    """

    df = fetch_dataframe(query, tuple(params))

    active_students = fetch_dataframe("""
        SELECT COUNT(*) AS total
        FROM students
        WHERE is_active = 1
    """)

    student_count = (
        int(active_students.iloc[0]["total"])
        if not active_students.empty else 0
    )

    if not df.empty:

        df["expected_attendance"] = (
            df["total_periods"] * student_count
        )

        df["attendance_percentage"] = (
            df["total_present"]
            / df["expected_attendance"].replace(0, 1)
            * 100
        )

    return df


def get_daily_statistics(start_date=None, end_date=None):

    query = """
        SELECT
            p.date,
            COUNT(DISTINCT p.id) AS total_periods,
            COUNT(a.id) AS total_present
        FROM periods p
        LEFT JOIN attendance a
            ON a.period_id = p.id
        WHERE p.status = 'closed'
    """

    params = []

    if start_date:
        query += " AND p.date >= ?"
        params.append(start_date.isoformat())

    if end_date:
        query += " AND p.date <= ?"
        params.append(end_date.isoformat())

    query += """
        GROUP BY p.date
        ORDER BY p.date
    """

    df = fetch_dataframe(query, tuple(params))

    active_students = fetch_dataframe("""
        SELECT COUNT(*) AS total
        FROM students
        WHERE is_active = 1
    """)

    student_count = (
        int(active_students.iloc[0]["total"])
        if not active_students.empty else 0
    )

    if not df.empty:

        df["date"] = pd.to_datetime(df["date"])

        df["expected_attendance"] = (
            df["total_periods"] * student_count
        )

        df["attendance_percentage"] = (
            df["total_present"]
            / df["expected_attendance"].replace(0, 1)
            * 100
        )

    return df


# ==================================================
# CLASS OVERVIEW
# ==================================================

def render_class_overview(student_df, periods_df):

    st.markdown(
        '<div class="section-heading">Class Overview</div>',
        unsafe_allow_html=True
    )

    total_students = len(student_df)

    total_periods = len(periods_df)

    total_present = (
        student_df["attended_classes"].sum()
        if not student_df.empty else 0
    )

    total_expected = (
        student_df["total_classes"].sum()
        if not student_df.empty else 0
    )

    average_attendance = (
        total_present / total_expected * 100
        if total_expected > 0 else 0
    )

    below_threshold = (
        len(
            student_df[
                student_df["attendance_percentage"] < 75
            ]
        )
        if not student_df.empty else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Active Students",
        total_students
    )

    c2.metric(
        "Completed Periods",
        total_periods
    )

    c3.metric(
        "Average Attendance",
        f"{average_attendance:.1f}%"
    )

    c4.metric(
        "Below 75%",
        below_threshold
    )


# ==================================================
# ATTENDANCE TREND
# ==================================================

def render_attendance_trend(
    daily_df,
    chart_key="attendance_trend"
):

    st.markdown(
        '<div class="section-heading">Attendance Trends</div>',
        unsafe_allow_html=True
    )

    if daily_df.empty:

        st.info(
            "No attendance trend data available."
        )
        return

    fig = px.line(
        daily_df,
        x="date",
        y="attendance_percentage",
        markers=True,
        labels={
            "date": "Date",
            "attendance_percentage": "Attendance (%)"
        }
    )

    fig.update_traces(
        line_color="#38BDF8",
        line_width=3,
        marker_size=8
    )

    fig.update_layout(
        paper_bgcolor="#172238",
        plot_bgcolor="#172238",
        font_color="#CBD5E1",
        margin=dict(
            l=15,
            r=15,
            t=25,
            b=15
        ),
        xaxis=dict(
            showgrid=False,
            title=None
        ),
        yaxis=dict(
            gridcolor="#263750",
            title="Attendance %",
            range=[0, 100]
        )
    )

    fig.add_hline(
        y=75,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text="75% Threshold"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=chart_key
    )


# ==================================================
# SUBJECT ANALYTICS
# ==================================================

def render_subject_analytics(subject_df):

    st.markdown(
        '<div class="section-heading">Subject-wise Analytics</div>',
        unsafe_allow_html=True
    )

    if subject_df.empty:

        st.info(
            "No subject statistics available."
        )
        return

    fig = px.bar(
        subject_df,
        x="subject",
        y="attendance_percentage",
        text="attendance_percentage",
        labels={
            "subject": "Subject",
            "attendance_percentage": "Attendance (%)"
        }
    )

    fig.update_traces(
        marker_color="#818CF8",
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig.update_layout(
        paper_bgcolor="#172238",
        plot_bgcolor="#172238",
        font_color="#CBD5E1",
        margin=dict(
            l=15,
            r=15,
            t=30,
            b=15
        ),
        xaxis=dict(
            showgrid=False,
            title=None
        ),
        yaxis=dict(
            gridcolor="#263750",
            title="Attendance %",
            range=[0, 110]
        )
    )

    fig.add_hline(
        y=75,
        line_dash="dash",
        line_color="#F59E0B"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="subject_attendance_chart"
    )

    display_df = subject_df.rename(columns={
        "subject": "Subject",
        "total_periods": "Completed Periods",
        "total_present": "Attendance Marks",
        "attendance_percentage": "Attendance Percentage"
    })

    display_df["Attendance Percentage"] = (
        display_df["Attendance Percentage"].round(2)
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# ==================================================
# STUDENT RANKINGS
# ==================================================

def render_student_rankings(student_df):

    st.markdown(
        '<div class="section-heading">Student Rankings</div>',
        unsafe_allow_html=True
    )

    if student_df.empty:

        st.info(
            "No student statistics available."
        )
        return

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("#### Highest Attendance")

        top_students = student_df.sort_values(
            "attendance_percentage",
            ascending=False
        ).head(10)

        st.dataframe(
            top_students[
                [
                    "roll_number",
                    "name",
                    "attendance_percentage"
                ]
            ].rename(columns={
                "roll_number": "Roll Number",
                "name": "Name",
                "attendance_percentage": "Attendance %"
            }).round(2),
            use_container_width=True,
            hide_index=True
        )

    with col2:

        st.markdown("#### Lowest Attendance")

        low_students = student_df.sort_values(
            "attendance_percentage",
            ascending=True
        ).head(10)

        st.dataframe(
            low_students[
                [
                    "roll_number",
                    "name",
                    "attendance_percentage"
                ]
            ].rename(columns={
                "roll_number": "Roll Number",
                "name": "Name",
                "attendance_percentage": "Attendance %"
            }).round(2),
            use_container_width=True,
            hide_index=True
        )


# ==================================================
# LOW ATTENDANCE ALERTS
# ==================================================

def render_low_attendance(student_df):

    st.markdown(
        '<div class="section-heading">Low Attendance Alerts</div>',
        unsafe_allow_html=True
    )

    if student_df.empty:

        st.info(
            "No student records available."
        )
        return

    threshold = st.slider(
        "Attendance threshold (%)",
        min_value=0,
        max_value=100,
        value=75,
        key="low_attendance_threshold"
    )

    low_df = student_df[
        student_df["attendance_percentage"] < threshold
    ].copy()

    if low_df.empty:

        st.success(
            f"All active students have attendance of at least "
            f"{threshold}%."
        )

        return

    st.warning(
        f"{len(low_df)} students are below {threshold}% attendance."
    )

    display_df = low_df[
        [
            "roll_number",
            "name",
            "total_classes",
            "attended_classes",
            "absent_classes",
            "attendance_percentage"
        ]
    ].rename(columns={
        "roll_number": "Roll Number",
        "name": "Student Name",
        "total_classes": "Total Classes",
        "attended_classes": "Attended",
        "absent_classes": "Absent",
        "attendance_percentage": "Attendance %"
    })

    st.dataframe(
        display_df.round(2),
        use_container_width=True,
        hide_index=True
    )

    csv = display_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download Low Attendance List",
        data=csv,
        file_name="low_attendance_students.csv",
        mime="text/csv",
        key="download_low_attendance"
    )


# ==================================================
# ATTENDANCE DISTRIBUTION
# ==================================================

def render_attendance_distribution(student_df):

    st.markdown(
        '<div class="section-heading">Attendance Distribution</div>',
        unsafe_allow_html=True
    )

    if student_df.empty:

        st.info(
            "No attendance distribution data available."
        )
        return

    bins = [
        0, 50, 60, 75, 85, 100.000001
    ]

    labels = [
        "Below 50%",
        "50–60%",
        "60–75%",
        "75–85%",
        "85–100%"
    ]

    distribution = pd.cut(
        student_df["attendance_percentage"].clip(0, 100),
        bins=bins,
        labels=labels,
        include_lowest=True,
        right=True
    )

    distribution_df = (
        distribution.value_counts()
        .reindex(labels, fill_value=0)
        .reset_index()
    )

    distribution_df.columns = [
        "Attendance Range",
        "Students"
    ]

    fig = px.pie(
        distribution_df,
        names="Attendance Range",
        values="Students",
        hole=0.55
    )

    fig.update_layout(
        paper_bgcolor="#172238",
        font_color="#CBD5E1",
        margin=dict(
            l=15,
            r=15,
            t=25,
            b=15
        ),
        legend_title_text="Attendance Range"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="attendance_distribution_chart"
    )


# ==================================================
# MAIN PAGE
# ==================================================

def render():

    page_header(
        "Attendance Analytics",
        "Analyze attendance patterns, student performance and subject trends."
    )

    # DATE FILTERS

    with st.expander(
        "Analytics Filters",
        expanded=True
    ):

        col1, col2 = st.columns(2)

        today = datetime.now().date()

        with col1:

            start_date = st.date_input(
                "From Date",
                value=today - timedelta(days=30),
                key="analytics_start_date"
            )

        with col2:

            end_date = st.date_input(
                "To Date",
                value=today,
                key="analytics_end_date"
            )

    if start_date > end_date:

        st.error(
            "Start date cannot be later than end date."
        )
        return

    # LOAD DATA

    student_df = get_student_attendance(
        start_date,
        end_date
    )

    periods_df = get_closed_periods(
        start_date,
        end_date
    )

    subject_df = get_subject_statistics(
        start_date,
        end_date
    )

    daily_df = get_daily_statistics(
        start_date,
        end_date
    )

    # PAGE TABS

    tabs = st.tabs([
        "Class Overview",
        "Trends",
        "Subjects",
        "Student Rankings",
        "Low Attendance",
        "Distribution"
    ])

    with tabs[0]:

        render_class_overview(
            student_df,
            periods_df
        )

        st.divider()

        render_attendance_trend(
            daily_df,
            chart_key="overview_attendance_trend"
        )

    with tabs[1]:

        render_attendance_trend(
            daily_df,
            chart_key="detailed_attendance_trend"
        )

    with tabs[2]:

        render_subject_analytics(
            subject_df
        )

    with tabs[3]:

        render_student_rankings(
            student_df
        )

    with tabs[4]:

        render_low_attendance(
            student_df
        )

    with tabs[5]:

        render_attendance_distribution(
            student_df
        )
