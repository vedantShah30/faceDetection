
from datetime import datetime, timedelta
from io import BytesIO

import pandas as pd
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


def get_attendance_records(start_date, end_date):

    query = """
        SELECT
            a.id AS attendance_id,
            s.id AS student_id,
            s.name AS student_name,
            s.roll_number,
            p.id AS period_id,
            p.subject,
            p.date,
            p.start_time,
            p.end_time,
            a.marked_at,
            'Present' AS status
        FROM attendance a
        JOIN students s
            ON a.student_id = s.id
        JOIN periods p
            ON a.period_id = p.id
        WHERE p.status = 'closed'
          AND p.date BETWEEN ? AND ?
        ORDER BY p.date DESC, s.roll_number
    """

    return fetch_dataframe(
        query,
        (start_date.isoformat(), end_date.isoformat())
    )


def get_student_summary(start_date, end_date):

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
          AND p.date BETWEEN ? AND ?
        GROUP BY s.id, s.name, s.roll_number
        ORDER BY s.roll_number
    """

    df = fetch_dataframe(
        query,
        (start_date.isoformat(), end_date.isoformat())
    )

    if not df.empty:

        df["absent_classes"] = (
            df["total_classes"] - df["attended_classes"]
        )

        df["attendance_percentage"] = (
            df["attended_classes"]
            / df["total_classes"].replace(0, 1)
            * 100
        ).round(2)

    return df


def get_subject_summary(start_date, end_date):

    query = """
        SELECT
            p.subject,
            COUNT(DISTINCT p.id) AS total_periods,
            COUNT(a.id) AS total_present
        FROM periods p
        LEFT JOIN attendance a
            ON a.period_id = p.id
        WHERE p.status = 'closed'
          AND p.date BETWEEN ? AND ?
        GROUP BY p.subject
        ORDER BY p.subject
    """

    df = fetch_dataframe(
        query,
        (start_date.isoformat(), end_date.isoformat())
    )

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
        ).round(2)

    return df


def get_period_summary(start_date, end_date):

    query = """
        SELECT
            p.id AS period_id,
            p.subject,
            p.date,
            p.start_time,
            p.end_time,
            p.duration_minutes,
            COUNT(a.id) AS present_students
        FROM periods p
        LEFT JOIN attendance a
            ON a.period_id = p.id
        WHERE p.status = 'closed'
          AND p.date BETWEEN ? AND ?
        GROUP BY
            p.id,
            p.subject,
            p.date,
            p.start_time,
            p.end_time,
            p.duration_minutes
        ORDER BY p.date DESC
    """

    df = fetch_dataframe(
        query,
        (start_date.isoformat(), end_date.isoformat())
    )

    if not df.empty:

        active_students = fetch_dataframe("""
            SELECT COUNT(*) AS total
            FROM students
            WHERE is_active = 1
        """)

        student_count = (
            int(active_students.iloc[0]["total"])
            if not active_students.empty else 0
        )

        df["total_students"] = student_count

        df["absent_students"] = (
            student_count - df["present_students"]
        ).clip(lower=0)

        df["attendance_percentage"] = (
            df["present_students"]
            / df["total_students"].replace(0, 1)
            * 100
        ).round(2)

    return df


def get_period_report(period_id):

    query = """
        SELECT
            s.id AS student_id,
            s.roll_number,
            s.name AS student_name,
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
# EXCEL EXPORT
# ==================================================

def create_excel_workbook(sheets):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        for sheet_name, dataframe in sheets.items():

            # Excel sheet names must be <= 31 characters.

            safe_name = sheet_name[:31]

            if dataframe is None or dataframe.empty:

                pd.DataFrame({
                    "Information": [
                        "No records available for this report."
                    ]
                }).to_excel(
                    writer,
                    sheet_name=safe_name,
                    index=False
                )

            else:

                dataframe.to_excel(
                    writer,
                    sheet_name=safe_name,
                    index=False
                )

    output.seek(0)

    return output.getvalue()


def export_button(dataframe, filename, label):

    if dataframe is None or dataframe.empty:

        st.info("No data available to export.")
        return

    csv_data = dataframe.to_csv(
        index=False
    ).encode("utf-8-sig")

    col1, col2 = st.columns(2)

    with col1:

        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name=f"{filename}.csv",
            mime="text/csv",
            key=f"{filename}_csv"
        )

    with col2:

        excel_data = create_excel_workbook({
            label: dataframe
        })

        st.download_button(
            "Download Excel",
            data=excel_data,
            file_name=f"{filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{filename}_excel"
        )


# ==================================================
# REPORT PREVIEW
# ==================================================

def show_report(dataframe, empty_message):

    if dataframe is None or dataframe.empty:

        st.info(empty_message)
        return

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        f"Total records: {len(dataframe)}"
    )


# ==================================================
# COMPLETE ATTENDANCE REPORT
# ==================================================

def render_complete_report(start_date, end_date):

    st.markdown(
        '<div class="section-heading">Complete Attendance Report</div>',
        unsafe_allow_html=True
    )

    df = get_attendance_records(
        start_date,
        end_date
    )

    show_report(
        df,
        "No attendance records found in this date range."
    )

    export_button(
        df,
        "complete_attendance_report",
        "Attendance"
    )


# ==================================================
# PERIOD REPORT
# ==================================================

def render_period_report(start_date, end_date):

    st.markdown(
        '<div class="section-heading">Period-wise Report</div>',
        unsafe_allow_html=True
    )

    with database.get_connection() as conn:

        periods = conn.execute("""
            SELECT id, subject, date, start_time
            FROM periods
            WHERE status = 'closed'
              AND date BETWEEN ? AND ?
            ORDER BY date DESC
        """, (
            start_date.isoformat(),
            end_date.isoformat()
        )).fetchall()

    if not periods:

        st.info("No completed periods found.")
        return

    period_options = {
        f"{p['subject']} | {p['date']} | ID: {p['id']}":
            p["id"]
        for p in periods
    }

    selected = st.selectbox(
        "Select Period",
        list(period_options.keys()),
        key="report_period_select"
    )

    period_id = period_options[selected]

    df = get_period_report(period_id)

    if not df.empty:

        present = len(
            df[df["attendance_status"] == "Present"]
        )

        absent = len(
            df[df["attendance_status"] == "Absent"]
        )

        total = len(df)

        percentage = (
            present / total * 100
            if total else 0
        )

        c1, c2, c3 = st.columns(3)

        c1.metric("Present", present)

        c2.metric("Absent", absent)

        c3.metric(
            "Attendance",
            f"{percentage:.1f}%"
        )

    display_df = df.rename(columns={
        "student_id": "Student ID",
        "roll_number": "Roll Number",
        "student_name": "Student Name",
        "attendance_status": "Status",
        "marked_at": "Marked At"
    })

    show_report(
        display_df,
        "No student records available."
    )

    export_button(
        display_df,
        f"period_{period_id}_report",
        "Period Report"
    )


# ==================================================
# STUDENT-WISE REPORT
# ==================================================

def render_student_report(start_date, end_date):

    st.markdown(
        '<div class="section-heading">Student-wise Report</div>',
        unsafe_allow_html=True
    )

    df = get_student_summary(
        start_date,
        end_date
    )

    if df.empty:

        st.info("No student attendance statistics available.")
        return

    search = st.text_input(
        "Search student",
        placeholder="Name or roll number",
        key="student_report_search"
    )

    filtered_df = df.copy()

    if search.strip():

        query = search.strip().lower()

        filtered_df = filtered_df[
            filtered_df["name"].str.lower().str.contains(
                query,
                na=False
            )
            |
            filtered_df["roll_number"].astype(str).str.lower().str.contains(
                query,
                na=False
            )
        ]

    display_df = filtered_df.rename(columns={
        "student_id": "Student ID",
        "name": "Student Name",
        "roll_number": "Roll Number",
        "total_classes": "Total Classes",
        "attended_classes": "Attended",
        "absent_classes": "Absent",
        "attendance_percentage": "Attendance %"
    })

    show_report(
        display_df,
        "No matching students found."
    )

    export_button(
        display_df,
        "student_attendance_report",
        "Student Report"
    )


# ==================================================
# SUBJECT-WISE REPORT
# ==================================================

def render_subject_report(start_date, end_date):

    st.markdown(
        '<div class="section-heading">Subject-wise Report</div>',
        unsafe_allow_html=True
    )

    df = get_subject_summary(
        start_date,
        end_date
    )

    if df.empty:

        st.info("No subject reports available.")
        return

    fig_data = df.sort_values(
        "attendance_percentage",
        ascending=True
    )

    import plotly.express as px

    fig = px.bar(
        fig_data,
        x="attendance_percentage",
        y="subject",
        orientation="h",
        text="attendance_percentage",
        labels={
            "subject": "Subject",
            "attendance_percentage": "Attendance (%)"
        }
    )

    fig.update_traces(
        marker_color="#38BDF8",
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig.update_layout(
        paper_bgcolor="#172238",
        plot_bgcolor="#172238",
        font_color="#CBD5E1",
        xaxis=dict(
            range=[0, 110],
            title="Attendance (%)",
            gridcolor="#263750"
        ),
        yaxis=dict(
            title=None,
            showgrid=False
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="reports_subject_chart"
    )

    display_df = df.rename(columns={
        "subject": "Subject",
        "total_periods": "Completed Periods",
        "total_present": "Attendance Marks",
        "expected_attendance": "Expected Attendance",
        "attendance_percentage": "Attendance %"
    })

    show_report(
        display_df,
        "No subject statistics available."
    )

    export_button(
        display_df,
        "subject_attendance_report",
        "Subject Report"
    )


# ==================================================
# LOW ATTENDANCE REPORT
# ==================================================

def render_low_attendance_report(start_date, end_date):

    st.markdown(
        '<div class="section-heading">Low Attendance Report</div>',
        unsafe_allow_html=True
    )

    threshold = st.slider(
        "Minimum attendance requirement (%)",
        min_value=0,
        max_value=100,
        value=75,
        key="report_attendance_threshold"
    )

    df = get_student_summary(
        start_date,
        end_date
    )

    if df.empty:

        st.info("No student attendance statistics available.")
        return

    low_df = df[
        df["attendance_percentage"] < threshold
    ].copy()

    if low_df.empty:

        st.success(
            f"All students have at least {threshold}% attendance."
        )
        return

    st.warning(
        f"{len(low_df)} students are below the "
        f"{threshold}% attendance requirement."
    )

    display_df = low_df.rename(columns={
        "student_id": "Student ID",
        "name": "Student Name",
        "roll_number": "Roll Number",
        "total_classes": "Total Classes",
        "attended_classes": "Attended",
        "absent_classes": "Absent",
        "attendance_percentage": "Attendance %"
    })

    show_report(
        display_df,
        "No students below the selected threshold."
    )

    export_button(
        display_df,
        "low_attendance_report",
        "Low Attendance"
    )


# ==================================================
# COMPLETE EXCEL WORKBOOK
# ==================================================

def render_complete_workbook(start_date, end_date):

    st.markdown(
        '<div class="section-heading">Complete Excel Workbook</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Generate a single Excel workbook containing all "
        "major attendance reports."
    )

    if st.button(
        "Generate Complete Excel Workbook",
        type="primary",
        use_container_width=True
    ):

        with st.spinner("Generating Excel workbook..."):

            attendance_df = get_attendance_records(
                start_date,
                end_date
            )

            student_df = get_student_summary(
                start_date,
                end_date
            )

            subject_df = get_subject_summary(
                start_date,
                end_date
            )

            period_df = get_period_summary(
                start_date,
                end_date
            )

            threshold = 75

            low_df = student_df[
                student_df["attendance_percentage"] < threshold
            ].copy() if not student_df.empty else pd.DataFrame()

            sheets = {
                "Attendance Records": attendance_df,
                "Student Summary": student_df,
                "Subject Summary": subject_df,
                "Period Summary": period_df,
                "Low Attendance": low_df
            }

            workbook = create_excel_workbook(sheets)

            st.download_button(
                "Download Complete Excel Workbook",
                data=workbook,
                file_name=(
                    f"attendance_report_"
                    f"{start_date}_{end_date}.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                key="complete_workbook_download"
            )


# ==================================================
# MAIN PAGE
# ==================================================

def render():

    page_header(
        "Reports & Exports",
        "Generate, preview and download attendance reports."
    )

    # ------------------------------------------
    # DATE FILTERS
    # ------------------------------------------

    with st.container(border=True):

        st.markdown("#### Report Period")

        col1, col2 = st.columns(2)

        today = datetime.now().date()

        with col1:

            start_date = st.date_input(
                "From Date",
                value=today - timedelta(days=30),
                key="reports_start_date"
            )

        with col2:

            end_date = st.date_input(
                "To Date",
                value=today,
                key="reports_end_date"
            )

    if start_date > end_date:

        st.error("Start date cannot be later than end date.")
        return

    st.divider()

    # ------------------------------------------
    # REPORT TABS
    # ------------------------------------------

    tabs = st.tabs([
        "Complete Attendance",
        "Period Report",
        "Student Report",
        "Subject Report",
        "Low Attendance",
        "Excel Workbook"
    ])

    with tabs[0]:

        render_complete_report(
            start_date,
            end_date
        )

    with tabs[1]:

        render_period_report(
            start_date,
            end_date
        )

    with tabs[2]:

        render_student_report(
            start_date,
            end_date
        )

    with tabs[3]:

        render_subject_report(
            start_date,
            end_date
        )

    with tabs[4]:

        render_low_attendance_report(
            start_date,
            end_date
        )

    with tabs[5]:

        render_complete_workbook(
            start_date,
            end_date
        )
