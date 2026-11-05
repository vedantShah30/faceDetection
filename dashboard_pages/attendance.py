
import pandas as pd
import streamlit as st

import database
import analytics

from dashboard_utils.styling import page_header


# ==================================================
# DATABASE HELPERS
# ==================================================

def get_periods():

    periods = database.get_all_periods()

    return [dict(p) for p in periods]


def get_students():

    students = database.get_all_students()

    return [dict(s) for s in students]


def fetch_dataframe(query, params=()):

    with database.get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


def get_attendance_summary():

    with database.get_connection() as conn:

        total_students = conn.execute("""
            SELECT COUNT(*)
            FROM students
            WHERE is_active = 1
        """).fetchone()[0]

        total_periods = conn.execute("""
            SELECT COUNT(*)
            FROM periods
            WHERE status = 'closed'
        """).fetchone()[0]

        total_records = conn.execute("""
            SELECT COUNT(*)
            FROM attendance
        """).fetchone()[0]

        total_present_today = conn.execute("""
            SELECT COUNT(*)
            FROM attendance a
            JOIN periods p ON a.period_id = p.id
            WHERE p.date = DATE('now', 'localtime')
        """).fetchone()[0]

    denominator = total_students * total_periods

    attendance_rate = (
        total_records / denominator * 100
        if denominator > 0 else 0
    )

    return {
        "students": total_students,
        "periods": total_periods,
        "records": total_records,
        "today": total_present_today,
        "rate": attendance_rate
    }


# ==================================================
# ATTENDANCE RECORDS
# ==================================================

def get_attendance_records(
    start_date=None,
    end_date=None,
    subject=None,
    search=None
):

    query = """
        SELECT
            a.id AS attendance_id,
            s.id AS student_id,
            s.name,
            s.roll_number,
            p.id AS period_id,
            p.subject,
            p.date,
            p.start_time,
            a.marked_at,
            'Present' AS status
        FROM attendance a
        JOIN students s
            ON a.student_id = s.id
        JOIN periods p
            ON a.period_id = p.id
        WHERE 1=1
    """

    params = []

    if start_date:

        query += " AND p.date >= ?"
        params.append(start_date.isoformat())

    if end_date:

        query += " AND p.date <= ?"
        params.append(end_date.isoformat())

    if subject and subject != "All Subjects":

        query += " AND p.subject = ?"
        params.append(subject)

    if search:

        query += """
            AND (
                s.name LIKE ?
                OR s.roll_number LIKE ?
            )
        """

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value
        ])

    query += " ORDER BY p.date DESC, a.marked_at DESC"

    return fetch_dataframe(query, tuple(params))


# ==================================================
# PERIOD-WISE REPORT
# ==================================================

def get_period_attendance_report(period_id):

    # Active students are included in the present/absent
    # calculation, consistent with the existing backend.

    query = """
        SELECT
            s.id AS student_id,
            s.roll_number,
            s.name,
            CASE
                WHEN a.id IS NOT NULL THEN 'Present'
                ELSE 'Absent'
            END AS attendance_status,
            a.marked_at
        FROM students s
        LEFT JOIN attendance a
            ON s.id = a.student_id
            AND a.period_id = ?
        WHERE s.is_active = 1
        ORDER BY s.roll_number
    """

    return fetch_dataframe(
        query,
        (period_id,)
    )


# ==================================================
# STUDENT ATTENDANCE HISTORY
# ==================================================

def get_student_history(student_id):

    query = """
        SELECT
            p.id AS period_id,
            p.subject,
            p.date,
            p.start_time,
            a.marked_at,
            'Present' AS status
        FROM attendance a
        JOIN periods p
            ON a.period_id = p.id
        WHERE a.student_id = ?
        ORDER BY p.date DESC, a.marked_at DESC
    """

    return fetch_dataframe(
        query,
        (student_id,)
    )


# ==================================================
# OVERVIEW
# ==================================================

def render_overview():

    st.markdown(
        '<div class="section-heading">'
        'Attendance Overview'
        '</div>',
        unsafe_allow_html=True
    )

    summary = get_attendance_summary()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Active Students",
        summary["students"]
    )

    c2.metric(
        "Completed Periods",
        summary["periods"]
    )

    c3.metric(
        "Attendance Records",
        summary["records"]
    )

    c4.metric(
        "Attendance Rate",
        f"{summary['rate']:.1f}%"
    )

    st.divider()

    st.markdown("#### Attendance Records")

    col1, col2, col3 = st.columns(3)

    with col1:

        start_date = st.date_input(
            "From Date",
            value=None,
            key="attendance_start_date"
        )

    with col2:

        end_date = st.date_input(
            "To Date",
            value=None,
            key="attendance_end_date"
        )

    with col3:

        subjects = sorted(set(
            p["subject"] for p in get_periods()
        ))

        selected_subject = st.selectbox(
            "Subject",
            ["All Subjects"] + subjects
        )

    search = st.text_input(
        "Search student",
        placeholder="Enter student name or roll number"
    )

    if start_date and end_date and start_date > end_date:

        st.error("Start date cannot be later than end date.")
        return

    df = get_attendance_records(
        start_date=start_date,
        end_date=end_date,
        subject=selected_subject,
        search=search.strip()
    )

    if not df.empty:

        display_df = df.rename(columns={
            "attendance_id": "Record ID",
            "student_id": "Student ID",
            "name": "Student Name",
            "roll_number": "Roll Number",
            "period_id": "Period ID",
            "subject": "Subject",
            "date": "Date",
            "start_time": "Period Start",
            "marked_at": "Marked At",
            "status": "Status"
        })

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            f"{len(df)} attendance records found."
        )

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Attendance CSV",
            data=csv,
            file_name="attendance_records.csv",
            mime="text/csv"
        )

    else:

        st.info("No attendance records match these filters.")


# ==================================================
# PERIOD REPORT
# ==================================================

def render_period_report():

    st.markdown(
        '<div class="section-heading">'
        'Period-wise Attendance Report'
        '</div>',
        unsafe_allow_html=True
    )

    periods = get_periods()

    completed_periods = [
        p for p in periods
        if p["status"] == "closed"
    ]

    if not completed_periods:

        st.info("No completed periods are available.")
        return

    options = {
        f"{p['subject']} | {p['date']} | ID: {p['id']}":
            p["id"]
        for p in completed_periods
    }

    selected = st.selectbox(
        "Select Period",
        list(options.keys()),
        key="attendance_period_report"
    )

    period_id = options[selected]

    report = get_period_attendance_report(period_id)

    if report.empty:

        st.info("No student records available.")
        return

    present = report[
        report["attendance_status"] == "Present"
    ]

    absent = report[
        report["attendance_status"] == "Absent"
    ]

    total = len(report)

    attendance_rate = (
        len(present) / total * 100
        if total else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Students", total)

    c2.metric("Present", len(present))

    c3.metric("Absent", len(absent))

    c4.metric(
        "Attendance",
        f"{attendance_rate:.1f}%"
    )

    st.divider()

    present_tab, absent_tab, complete_tab = st.tabs([
        "Present Students",
        "Absent Students",
        "Complete Report"
    ])

    with present_tab:

        st.dataframe(
            present[
                [
                    "roll_number",
                    "name",
                    "marked_at"
                ]
            ].rename(columns={
                "roll_number": "Roll Number",
                "name": "Student Name",
                "marked_at": "Marked At"
            }),
            use_container_width=True,
            hide_index=True
        )

    with absent_tab:

        st.dataframe(
            absent[
                [
                    "roll_number",
                    "name"
                ]
            ].rename(columns={
                "roll_number": "Roll Number",
                "name": "Student Name"
            }),
            use_container_width=True,
            hide_index=True
        )

    with complete_tab:

        complete_report = report.rename(columns={
            "student_id": "Student ID",
            "roll_number": "Roll Number",
            "name": "Student Name",
            "attendance_status": "Status",
            "marked_at": "Marked At"
        })

        st.dataframe(
            complete_report,
            use_container_width=True,
            hide_index=True
        )

        csv = complete_report.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download Period Report",
            data=csv,
            file_name=f"period_{period_id}_attendance.csv",
            mime="text/csv"
        )


# ==================================================
# STUDENT HISTORY
# ==================================================

def render_student_history():

    st.markdown(
        '<div class="section-heading">'
        'Individual Student Attendance'
        '</div>',
        unsafe_allow_html=True
    )

    students = get_students()

    if not students:

        st.info("No students are registered.")
        return

    options = {
        f"{s['roll_number']} — {s['name']}": s["id"]
        for s in students
    }

    selected = st.selectbox(
        "Select Student",
        list(options.keys()),
        key="attendance_student_history"
    )

    student_id = options[selected]

    student = next(
        s for s in students
        if s["id"] == student_id
    )

    history = get_student_history(student_id)

    # Existing analytics implementation

    try:

        overview = analytics.get_student_overview(
            student_id
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Total Classes",
            overview["total_classes"]
        )

        c2.metric(
            "Attended",
            overview["attended_classes"]
        )

        c3.metric(
            "Absent",
            overview["absent_classes"]
        )

        c4.metric(
            "Attendance",
            f"{overview['percentage']:.1f}%"
        )

    except Exception as error:

        st.warning(
            f"Could not calculate attendance statistics: {error}"
        )

    st.divider()

    st.markdown(
        f"#### Attendance History — {student['name']}"
    )

    if history.empty:

        st.info("No attendance records found for this student.")

    else:

        st.dataframe(
            history.rename(columns={
                "period_id": "Period ID",
                "subject": "Subject",
                "date": "Date",
                "start_time": "Period Start",
                "marked_at": "Marked At",
                "status": "Status"
            }),
            use_container_width=True,
            hide_index=True
        )

        csv = history.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download Student History",
            data=csv,
            file_name=f"student_{student_id}_attendance.csv",
            mime="text/csv"
        )


# ==================================================
# MAIN PAGE
# ==================================================

def render():

    page_header(
        "Attendance Management",
        "Explore attendance records, period reports and student history."
    )

    tabs = st.tabs([
        "Overview",
        "Period Report",
        "Student History"
    ])

    with tabs[0]:

        render_overview()

    with tabs[1]:

        render_period_report()

    with tabs[2]:

        render_student_history()
