
import shutil
from pathlib import Path

import pandas as pd
import streamlit as st

import database
import dataset
import trainer
import analytics

from config import DATASET_DIR, MIN_SAMPLES

from dashboard_utils.styling import page_header


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def get_student_by_roll_number(roll_number):

    with database.get_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM students
            WHERE roll_number = ?
            """,
            (roll_number,)
        ).fetchone()


def get_student_by_id(student_id):

    with database.get_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM students
            WHERE id = ?
            """,
            (student_id,)
        ).fetchone()


def get_student_list():

    students = database.get_all_students()

    return [dict(student) for student in students]


def get_dataset_count(student_id):

    folder = Path(DATASET_DIR) / str(student_id)

    if not folder.exists():
        return 0

    return len(list(folder.glob("*.png")))


def cleanup_folder(folder):

    folder = Path(folder)

    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)


# ==================================================
# STUDENT REGISTRATION
# ==================================================

def register_student(roll_number, name):

    student_id = None
    student_folder = None

    try:

        # 1. Create inactive student record

        database.create_student(
            roll_number,
            name
        )

        student = get_student_by_roll_number(roll_number)

        if student is None:
            raise RuntimeError(
                "Could not retrieve the newly created student."
            )

        student_id = student["id"]

        student_folder = (
            Path(DATASET_DIR) / str(student_id)
        )

        # 2. Capture face dataset

        sample_count = dataset.generate_dataset(
            student_id
        )

        if sample_count is None:
            sample_count = 0

        # 3. Validate samples

        if sample_count < MIN_SAMPLES:

            database.delete_student(student_id)

            cleanup_folder(student_folder)

            return (
                False,
                f"Only {sample_count} images were captured. "
                f"At least {MIN_SAMPLES} are required."
            )

        # 4. Activate student

        database.activate_student(student_id)

        # 5. Train classifier

        try:

            trainer.train_classifier()

        except Exception as training_error:

            # Keep the student record and dataset,
            # but deactivate the student because the
            # current classifier may not contain them.

            database.deactivate_student(student_id)

            return (
                False,
                f"Face dataset captured successfully, but model "
                f"training failed: {training_error}. "
                f"The student has been kept inactive. "
                f"You can retry activation after resolving the issue."
            )

        return (
            True,
            f"Registration successful! {name} has been registered "
            f"with {sample_count} face samples."
        )

    except Exception as error:

        # Roll back incomplete registration

        if student_id is not None:

            try:
                database.delete_student(student_id)
            except Exception:
                pass

        if student_folder is not None:
            cleanup_folder(student_folder)

        return False, str(error)


# ==================================================
# FACE RE-REGISTRATION
# ==================================================

def reregister_student_face(student_id):

    student = get_student_by_id(student_id)

    if student is None:
        return False, "Student record not found."

    final_folder = (
        Path(DATASET_DIR) / str(student_id)
    )

    staging_folder = (
        Path(DATASET_DIR) / f".staging_{student_id}"
    )

    backup_folder = (
        Path(DATASET_DIR) / f".backup_{student_id}"
    )

    cleanup_folder(staging_folder)
    cleanup_folder(backup_folder)

    try:

        # 1. Capture a new dataset in a staging folder

        sample_count = dataset.generate_dataset(
            student_id,
            output_dir=staging_folder
        )

        if sample_count is None:
            sample_count = 0

        if sample_count < MIN_SAMPLES:

            cleanup_folder(staging_folder)

            return (
                False,
                f"Only {sample_count} samples captured. "
                f"Existing dataset has been preserved."
            )

        # 2. Back up the old dataset

        if final_folder.exists():
            final_folder.rename(backup_folder)

        # 3. Replace with the new dataset

        staging_folder.rename(final_folder)

        # 4. Retrain if the student is active

        if student["is_active"] == 1:

            try:
                trainer.train_classifier()

            except Exception as training_error:

                # Restore previous dataset

                cleanup_folder(final_folder)

                if backup_folder.exists():
                    backup_folder.rename(final_folder)

                return (
                    False,
                    f"Model training failed: {training_error}. "
                    f"The previous face dataset has been restored."
                )

        cleanup_folder(backup_folder)

        return (
            True,
            f"Face dataset updated successfully. "
            f"{sample_count} new samples captured."
        )

    except Exception as error:

        # Attempt rollback

        cleanup_folder(staging_folder)

        if backup_folder.exists():

            cleanup_folder(final_folder)
            backup_folder.rename(final_folder)

        return False, str(error)


# ==================================================
# STUDENT ACTIVATION / DEACTIVATION
# ==================================================

def deactivate_student_from_dashboard(student_id):

    try:

        database.deactivate_student(student_id)

        # Retrain using only active students

        active_students = database.get_all_active_students()

        if active_students:
            trainer.train_classifier()

        return True, "Student deactivated successfully."

    except Exception as error:

        return False, str(error)


def reactivate_student_from_dashboard(student_id):

    try:

        sample_count = get_dataset_count(student_id)

        if sample_count < MIN_SAMPLES:

            return (
                False,
                f"Student has only {sample_count} images. "
                f"At least {MIN_SAMPLES} are required. "
                f"Please re-register their face dataset."
            )

        database.activate_student(student_id)

        try:
            trainer.train_classifier()

        except Exception as training_error:

            # Roll back activation

            database.deactivate_student(student_id)

            return (
                False,
                f"Model training failed: {training_error}. "
                f"Student remains inactive."
            )

        return True, "Student reactivated successfully."

    except Exception as error:

        return False, str(error)


# ==================================================
# REGISTRATION PAGE
# ==================================================

def render_registration():

    st.markdown(
        '<div class="section-heading">Register New Student</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Create a student record and capture their face dataset."
    )

    with st.container(border=True):

        with st.form("student_registration_form"):

            col1, col2 = st.columns(2)

            with col1:

                name = st.text_input(
                    "Full Name",
                    placeholder="Enter student name"
                )

            with col2:

                roll_number = st.text_input(
                    "Roll Number",
                    placeholder="Enter unique roll number"
                )

            st.markdown("---")

            st.markdown("**Face Dataset Requirements**")

            c1, c2 = st.columns(2)

            c1.metric(
                "Target Samples",
                "200"
            )

            c2.metric(
                "Minimum Samples",
                MIN_SAMPLES
            )

            st.caption(
                "The OpenCV camera window will open after submission. "
                "Position the student in front of the camera and press "
                "q when you want to finish capturing."
            )

            submitted = st.form_submit_button(
                "Register Student",
                type="primary",
                use_container_width=True
            )

            if submitted:

                if not name.strip() or not roll_number.strip():

                    st.error(
                        "Both student name and roll number are required."
                    )

                else:

                    st.warning(
                        "Camera capture is starting. "
                        "Do not close the dashboard during registration."
                    )

                    with st.spinner(
                        "Capturing face dataset and training model..."
                    ):

                        success, message = register_student(
                            roll_number.strip(),
                            name.strip()
                        )

                    if success:

                        st.success(message)

                        st.session_state["student_registration_refresh"] = (
                            not st.session_state.get(
                                "student_registration_refresh",
                                False
                            )
                        )

                    else:

                        st.error(message)


# ==================================================
# STUDENT DIRECTORY
# ==================================================

def render_directory():

    st.markdown(
        '<div class="section-heading">Student Directory</div>',
        unsafe_allow_html=True
    )

    students = get_student_list()

    if not students:

        st.info(
            "No students have been registered yet."
        )

        return

    df = pd.DataFrame(students)

    # Search and filters

    col1, col2 = st.columns([2, 1])

    with col1:

        search = st.text_input(
            "Search",
            placeholder="Search by student name or roll number"
        )

    with col2:

        status_filter = st.selectbox(
            "Status",
            ["All", "Active", "Inactive"]
        )

    if search.strip():

        search = search.strip().lower()

        df = df[
            df["name"].str.lower().str.contains(
                search,
                na=False
            )
            |
            df["roll_number"].astype(str).str.lower().str.contains(
                search,
                na=False
            )
        ]

    if status_filter == "Active":

        df = df[df["is_active"] == 1]

    elif status_filter == "Inactive":

        df = df[df["is_active"] == 0]

    df["Status"] = df["is_active"].map({
        1: "Active",
        0: "Inactive"
    })

    display_df = df.rename(columns={
        "id": "Student ID",
        "roll_number": "Roll Number",
        "name": "Name",
        "created_at": "Registered At"
    })

    st.dataframe(
        display_df[
            [
                "Student ID",
                "Roll Number",
                "Name",
                "Status",
                "Registered At"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        f"Showing {len(df)} of {len(students)} students."
    )


# ==================================================
# STUDENT PROFILE
# ==================================================

def render_student_profile():

    st.markdown(
        '<div class="section-heading">Student Profile</div>',
        unsafe_allow_html=True
    )

    students = get_student_list()

    if not students:

        st.info("No student records available.")

        return

    student_options = {
        f"{s['roll_number']} — {s['name']}": s["id"]
        for s in students
    }

    selected_label = st.selectbox(
        "Select Student",
        list(student_options.keys()),
        key="profile_student"
    )

    student_id = student_options[selected_label]

    student = get_student_by_id(student_id)

    if student is None:
        st.error("Student not found.")
        return

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Name",
        student["name"]
    )

    col2.metric(
        "Roll Number",
        student["roll_number"]
    )

    col3.metric(
        "Enrollment Status",
        "Active" if student["is_active"] else "Inactive"
    )

    # Attendance overview

    try:

        overview = analytics.get_student_overview(student_id)

        st.markdown("#### Attendance Overview")

        a, b, c, d = st.columns(4)

        a.metric(
            "Total Classes",
            overview["total_classes"]
        )

        b.metric(
            "Attended",
            overview["attended_classes"]
        )

        c.metric(
            "Absent",
            overview["absent_classes"]
        )

        d.metric(
            "Attendance",
            f"{overview['percentage']:.1f}%"
        )

    except Exception as error:

        st.warning(
            f"Could not load attendance overview: {error}"
        )

    # Subject-wise attendance

    try:

        subject_data = analytics.get_subject_attendance(
            student_id
        )

        st.markdown("#### Subject-wise Attendance")

        if subject_data:

            subject_df = pd.DataFrame(subject_data)

            st.dataframe(
                subject_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No subject-wise attendance records found.")

    except Exception as error:

        st.warning(
            f"Could not load subject statistics: {error}"
        )

    st.markdown("#### Face Dataset")

    st.metric(
        "Available Face Samples",
        get_dataset_count(student_id)
    )


# ==================================================
# EDIT STUDENT
# ==================================================

def render_edit_student():

    st.markdown(
        '<div class="section-heading">Edit Student Details</div>',
        unsafe_allow_html=True
    )

    students = get_student_list()

    if not students:
        st.info("No students available.")
        return

    options = {
        f"{s['roll_number']} — {s['name']}": s["id"]
        for s in students
    }

    selected = st.selectbox(
        "Select Student",
        list(options.keys()),
        key="edit_student_select"
    )

    student_id = options[selected]

    student = get_student_by_id(student_id)

    with st.form("edit_student_form"):

        name = st.text_input(
            "Student Name",
            value=student["name"]
        )

        roll_number = st.text_input(
            "Roll Number",
            value=student["roll_number"]
        )

        submitted = st.form_submit_button(
            "Save Changes",
            type="primary"
        )

        if submitted:

            if not name.strip() or not roll_number.strip():

                st.error("Name and roll number cannot be empty.")

            else:

                try:

                    database.update_student_details(
                        student_id,
                        name.strip(),
                        roll_number.strip()
                    )

                    st.success(
                        "Student details updated successfully."
                    )

                    st.rerun()

                except Exception as error:

                    st.error(str(error))


# ==================================================
# FACE MANAGEMENT
# ==================================================

def render_face_management():

    st.markdown(
        '<div class="section-heading">Face Dataset Management</div>',
        unsafe_allow_html=True
    )

    students = get_student_list()

    if not students:
        st.info("No students available.")
        return

    options = {
        f"{s['roll_number']} — {s['name']}": s["id"]
        for s in students
    }

    selected = st.selectbox(
        "Select Student",
        list(options.keys()),
        key="face_student_select"
    )

    student_id = options[selected]

    student = get_student_by_id(student_id)

    count = get_dataset_count(student_id)

    c1, c2 = st.columns(2)

    c1.metric("Existing Face Samples", count)

    c2.metric(
        "Minimum Required",
        MIN_SAMPLES
    )

    if student["is_active"] == 1:

        st.info(
            "This operation will replace the student's existing "
            "face dataset and retrain the classifier."
        )

    else:

        st.info(
            "This student is inactive. The dataset will be replaced "
            "without activating the student."
        )

    confirm = st.checkbox(
        "I understand that a new face capture will replace the old dataset."
    )

    if st.button(
        "Start Face Re-registration",
        type="primary",
        disabled=not confirm
    ):

        with st.spinner(
            "Capturing new face samples and updating the model..."
        ):

            success, message = reregister_student_face(
                student_id
            )

        if success:
            st.success(message)
        else:
            st.error(message)


# ==================================================
# STUDENT STATUS MANAGEMENT
# ==================================================

def render_student_status():

    st.markdown(
        '<div class="section-heading">Enrollment Management</div>',
        unsafe_allow_html=True
    )

    students = get_student_list()

    if not students:
        st.info("No students available.")
        return

    options = {
        f"{s['roll_number']} — {s['name']} "
        f"({'Active' if s['is_active'] else 'Inactive'})": s["id"]
        for s in students
    }

    selected = st.selectbox(
        "Select Student",
        list(options.keys()),
        key="status_student_select"
    )

    student_id = options[selected]

    student = get_student_by_id(student_id)

    if student["is_active"] == 1:

        st.success("This student is currently active.")

        st.warning(
            "Deactivating a student removes them from future "
            "face-recognition attendance."
        )

        if st.button(
            "Deactivate Student",
            type="primary"
        ):

            success, message = deactivate_student_from_dashboard(
                student_id
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    else:

        st.warning("This student is currently inactive.")

        if st.button(
            "Reactivate Student",
            type="primary"
        ):

            success, message = reactivate_student_from_dashboard(
                student_id
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)


# ==================================================
# MAIN STUDENT PAGE
# ==================================================

def render():

    page_header(
        "Student Management",
        "Register students, manage face datasets and monitor enrollment."
    )

    # Summary metrics

    students = get_student_list()

    total = len(students)

    active = sum(
        1 for s in students if s["is_active"] == 1
    )

    inactive = total - active

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Students", total)

    c2.metric("Active Students", active)

    c3.metric("Inactive Students", inactive)

    st.divider()

    tabs = st.tabs([
        "Register Student",
        "Directory",
        "Student Profile",
        "Edit Details",
        "Face Management",
        "Enrollment Status"
    ])

    with tabs[0]:
        render_registration()

    with tabs[1]:
        render_directory()

    with tabs[2]:
        render_student_profile()

    with tabs[3]:
        render_edit_student()

    with tabs[4]:
        render_face_management()

    with tabs[5]:
        render_student_status()
