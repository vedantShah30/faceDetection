
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard_utils.database_helpers import (
    fetch_one,
    fetch_all
)

from dashboard_utils.styling import page_header


def get_dashboard_summary():

    today = datetime.now().strftime("%Y-%m-%d")

    students = fetch_one("""
        SELECT COUNT(*) AS total
        FROM students
        WHERE is_active = 1
    """)["total"]

    periods_today = fetch_one("""
        SELECT COUNT(*) AS total
        FROM periods
        WHERE date = ?
    """, (today,))["total"]

    present_today = fetch_one("""
        SELECT COUNT(*) AS total
        FROM attendance a
        JOIN periods p ON a.period_id = p.id
        WHERE p.date = ?
    """, (today,))["total"]

    closed_periods = fetch_one("""
        SELECT COUNT(*) AS total
        FROM periods
        WHERE status = 'closed'
    """)["total"]

    total_present = fetch_one("""
        SELECT COUNT(*) AS total
        FROM attendance a
        JOIN periods p ON a.period_id = p.id
        WHERE p.status = 'closed'
    """)["total"]

    denominator = students * closed_periods

    attendance_rate = (
        (total_present / denominator) * 100
        if denominator else 0
    )

    return {
        "students": students,
        "periods_today": periods_today,
        "present_today": present_today,
        "attendance_rate": attendance_rate
    }


def get_weekly_attendance():

    today = datetime.now().date()
    start_date = today - timedelta(days=6)

    rows = fetch_all("""
        SELECT
            p.date AS attendance_date,
            COUNT(a.id) AS present_count
        FROM periods p
        LEFT JOIN attendance a
            ON a.period_id = p.id
        WHERE p.date BETWEEN ? AND ?
          AND p.status = 'closed'
        GROUP BY p.date
        ORDER BY p.date
    """, (
        start_date.isoformat(),
        today.isoformat()
    ))

    df = pd.DataFrame(
        [dict(row) for row in rows]
    )

    if not df.empty:
        df["attendance_date"] = pd.to_datetime(
            df["attendance_date"]
        )

    return df


def get_recent_activity():

    rows = fetch_all("""
        SELECT
            s.name,
            s.roll_number,
            p.subject,
            p.date,
            a.marked_at
        FROM attendance a
        JOIN students s
            ON a.student_id = s.id
        JOIN periods p
            ON a.period_id = p.id
        ORDER BY a.id DESC
        LIMIT 10
    """)

    return pd.DataFrame(
        [dict(row) for row in rows]
    )


def get_active_period():

    return fetch_one("""
        SELECT
            id,
            subject,
            start_time,
            end_time,
            duration_minutes
        FROM periods
        WHERE status = 'active'
        LIMIT 1
    """)


def render():

    page_header(
        "Dashboard Overview",
        "Monitor attendance, students and classroom activity."
    )

    summary = get_dashboard_summary()

    # METRIC CARDS

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Active Students",
        summary["students"]
    )

    col2.metric(
        "Periods Today",
        summary["periods_today"]
    )

    col3.metric(
        "Attendance Marks Today",
        summary["present_today"]
    )

    col4.metric(
        "Overall Attendance",
        f'{summary["attendance_rate"]:.1f}%'
    )

    st.write("")

    # ACTIVE PERIOD

    active_period = get_active_period()

    if active_period:

        st.success(
            f"Live session: {active_period['subject']} "
            f"| Period ID: {active_period['id']}"
        )

        c1, c2 = st.columns(2)

        c1.write(
            f"**Start:** {active_period['start_time']}"
        )

        c2.write(
            f"**End:** {active_period['end_time']}"
        )

    else:

        st.info("There is currently no active attendance session.")

    st.divider()

    # CHART AND RECENT ACTIVITY

    left, right = st.columns([1.5, 1])

    with left:

        st.markdown(
            '<div class="section-heading">'
            'Weekly Attendance Trend'
            '</div>',
            unsafe_allow_html=True
        )

        weekly_df = get_weekly_attendance()

        if not weekly_df.empty:

            fig = px.bar(
                weekly_df,
                x="attendance_date",
                y="present_count",
                labels={
                    "attendance_date": "Date",
                    "present_count": "Attendance Marks"
                }
            )

            fig.update_traces(
                marker_color="#38BDF8"
            )

            fig.update_layout(
                paper_bgcolor="#172238",
                plot_bgcolor="#172238",
                font_color="#CBD5E1",
                margin=dict(l=15, r=15, t=25, b=15),
                xaxis=dict(showgrid=False, title=None),
                yaxis=dict(
                    gridcolor="#263750",
                    title=None
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info(
                "No completed attendance sessions in the last 7 days."
            )

    with right:

        st.markdown(
            '<div class="section-heading">'
            'Recent Attendance'
            '</div>',
            unsafe_allow_html=True
        )

        recent_df = get_recent_activity()

        if not recent_df.empty:

            recent_df.columns = [
                "Student",
                "Roll Number",
                "Subject",
                "Date",
                "Marked At"
            ]

            st.dataframe(
                recent_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No attendance records found.")

    st.divider()

    st.caption(
        "Last refreshed: "
        + datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
    )

    if st.button("Refresh Dashboard"):
        st.rerun()
