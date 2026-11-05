
from datetime import datetime
import pandas as pd
import streamlit as st

import database
import recognizer

from dashboard_utils.styling import page_header


# ==================================================
# DATABASE HELPERS
# ==================================================

def get_period_records():

    periods = database.get_all_periods()

    return [dict(period) for period in periods]


def get_period_by_id(period_id):

    with database.get_connection() as conn:

        return conn.execute(
            """
            SELECT *
            FROM periods
            WHERE id = ?
            """,
            (period_id,)
        ).fetchone()


def get_current_active_period():

    return database.get_active_period()


# ==================================================
# CREATE PERIOD
# ==================================================

def render_create_period():

    st.markdown(
        '<div class="section-heading">Create New Period</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):

        with st.form("create_period_form"):

            subject = st.text_input(
                "Subject / Course Name",
                placeholder="Example: Digital Electronics"
            )

            duration = st.number_input(
                "Period Duration (minutes)",
                min_value=1,
                max_value=300,
                value=60,
                step=5
            )

            submitted = st.form_submit_button(
                "Create Period",
                type="primary",
                use_container_width=True
            )

            if submitted:

                if not subject.strip():

                    st.error("Please enter a subject name.")

                else:

                    try:

                        database.create_period(
                            subject.strip(),
                            int(duration)
                        )

                        st.success(
                            f"Period for {subject.strip()} created successfully."
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(str(error))


# ==================================================
# PERIOD DIRECTORY
# ==================================================

def render_period_directory():

    st.markdown(
        '<div class="section-heading">Period History</div>',
        unsafe_allow_html=True
    )

    periods = get_period_records()

    if not periods:

        st.info("No periods have been created yet.")
        return

    df = pd.DataFrame(periods)

    # Search and status filters

    col1, col2 = st.columns([2, 1])

    with col1:

        search = st.text_input(
            "Search periods",
            placeholder="Search by subject..."
        )

    with col2:

        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Scheduled", "Active", "Closed"]
        )

    if search.strip():

        df = df[
            df["subject"].str.contains(
                search.strip(),
                case=False,
                na=False
            )
        ]

    if status_filter != "All":

        df = df[
            df["status"] == status_filter.lower()
        ]

    display_columns = [
        "id",
        "subject",
        "date",
        "start_time",
        "end_time",
        "duration_minutes",
        "status"
    ]

    display_df = df[display_columns].rename(
        columns={
            "id": "Period ID",
            "subject": "Subject",
            "date": "Date",
            "start_time": "Start Time",
            "end_time": "End Time",
            "duration_minutes": "Duration (min)",
            "status": "Status"
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        f"Showing {len(df)} of {len(periods)} periods."
    )


# ==================================================
# START ATTENDANCE
# ==================================================

def render_start_attendance():

    st.markdown(
        '<div class="section-heading">Start Attendance</div>',
        unsafe_allow_html=True
    )

    active_period = get_current_active_period()

    if active_period:

        st.warning(
            f"An attendance period is already active: "
            f"{active_period['subject']} "
            f"(Period ID: {active_period['id']})."
        )

        st.info(
            "Close the active period before starting another one."
        )

        return

    periods = get_period_records()

    scheduled_periods = [
        p for p in periods
        if p["status"] == "scheduled"
    ]

    if not scheduled_periods:

        st.info("There are no scheduled periods available.")
        return

    options = {
        f"{p['subject']} | {p['date']} | "
        f"{p['duration_minutes']} minutes | ID: {p['id']}":
            p["id"]
        for p in scheduled_periods
    }

    selected = st.selectbox(
        "Select a scheduled period",
        list(options.keys()),
        key="start_period_select"
    )

    period_id = options[selected]

    period = get_period_by_id(period_id)

    if period is None:
        st.error("Selected period could not be found.")
        return

    st.markdown("#### Period Details")

    c1, c2, c3 = st.columns(3)

    c1.metric("Subject", period["subject"])

    c2.metric(
        "Duration",
        f"{period['duration_minutes']} min"
    )

    c3.metric(
        "Period ID",
        period["id"]
    )

    st.warning(
        "Starting attendance will open the computer's webcam "
        "and launch face recognition."
    )

    confirm = st.checkbox(
        "I am ready to start attendance for this period."
    )

    if st.button(
        "Start Attendance & Open Camera",
        type="primary",
        use_container_width=True,
        disabled=not confirm
    ):

        try:

            # Activate selected period

            database.start_period(period_id)

            st.success(
                f"Attendance started for {period['subject']}."
            )

            st.info(
                "The OpenCV camera window should now open. "
                "Press q to finish the session."
            )

            try:

                with st.spinner(
                    "Face recognition is running..."
                ):

                    recognizer.run_recognition(
                        period_id=period_id
                    )

            finally:

                # Close the period after camera exits

                current_period = get_current_active_period()

                if (
                    current_period is not None
                    and current_period["id"] == period_id
                ):

                    database.close_period(period_id)

            st.success(
                "Attendance session completed and period closed."
            )

            st.rerun()

        except Exception as error:

            st.error(
                f"Could not start attendance: {error}"
            )


# ==================================================
# ACTIVE PERIOD
# ==================================================

def render_active_period():

    st.markdown(
        '<div class="section-heading">Current Active Period</div>',
        unsafe_allow_html=True
    )

    active_period = get_current_active_period()

    if active_period is None:

        st.info("There is no active period.")
        return

    st.success("Attendance period is currently active.")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Subject",
        active_period["subject"]
    )

    c2.metric(
        "Period ID",
        active_period["id"]
    )

    c3.metric(
        "Duration",
        f"{active_period['duration_minutes']} minutes"
    )

    st.write(
        f"**Start time:** {active_period['start_time']}"
    )

    st.write(
        f"**Scheduled end:** {active_period['end_time']}"
    )

    st.warning(
        "Closing this period prevents any further attendance "
        "from being marked for it."
    )

    confirm = st.checkbox(
        "Confirm that you want to close this active period.",
        key="confirm_close_period"
    )

    if st.button(
        "Close Active Period",
        type="primary",
        disabled=not confirm
    ):

        try:

            database.close_period(
                active_period["id"]
            )

            st.success("Period closed successfully.")

            st.rerun()

        except Exception as error:

            st.error(str(error))


# ==================================================
# MAIN PAGE
# ==================================================

def render():

    page_header(
        "Period Management",
        "Create classroom periods and manage attendance sessions."
    )

    periods = get_period_records()

    total_periods = len(periods)

    scheduled = sum(
        1 for p in periods
        if p["status"] == "scheduled"
    )

    active = sum(
        1 for p in periods
        if p["status"] == "active"
    )

    closed = sum(
        1 for p in periods
        if p["status"] == "closed"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Periods", total_periods)

    c2.metric("Scheduled", scheduled)

    c3.metric("Active", active)

    c4.metric("Completed", closed)

    st.divider()

    tabs = st.tabs([
        "Create Period",
        "Start Attendance",
        "Active Period",
        "Period History"
    ])

    with tabs[0]:

        render_create_period()

    with tabs[1]:

        render_start_attendance()

    with tabs[2]:

        render_active_period()

    with tabs[3]:

        render_period_directory()
