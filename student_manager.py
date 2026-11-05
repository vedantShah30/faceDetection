
import shutil
import os

from config import DATASET_DIR, MIN_SAMPLES

from database import (
    get_all_students,
    get_student_record,
    search_students,
    update_student_details,
    activate_student,
    deactivate_student,
    get_all_active_students
)

from dataset import generate_dataset
from trainer import train_classifier


# -------------------------------------------------
# VIEW ALL STUDENTS
# -------------------------------------------------

def display_students():

    students = get_all_students()

    print("\n========== STUDENT DIRECTORY ==========\n")

    if not students:
        print("No students found.")
        return

    print(
        f"{'ID':<8}"
        f"{'ROLL NUMBER':<20}"
        f"{'NAME':<25}"
        f"{'STATUS':<12}"
    )

    print("-" * 65)

    for s in students:

        status = (
            "Active"
            if s["is_active"]
            else "Inactive"
        )

        print(
            f"{s['id']:<8}"
            f"{s['roll_number']:<20}"
            f"{s['name']:<25}"
            f"{status:<12}"
        )


# -------------------------------------------------
# SEARCH STUDENT
# -------------------------------------------------

def search_student():

    query = input(
        "\nEnter name or roll number: "
    ).strip()

    if not query:
        print("Search query cannot be empty.")
        return

    students = search_students(query)

    print("\n========== SEARCH RESULTS ==========")

    if not students:
        print("No matching students.")
        return

    for s in students:

        status = "Active" if s["is_active"] else "Inactive"

        print(
            f"ID: {s['id']} | "
            f"Roll: {s['roll_number']} | "
            f"Name: {s['name']} | "
            f"Status: {status}"
        )


# -------------------------------------------------
# UPDATE STUDENT
# -------------------------------------------------

def edit_student():

    display_students()

    try:

        student_id = int(
            input("\nEnter student ID: ")
        )

        student = get_student_record(student_id)

        if not student:
            print("Student not found.")
            return

        print(f"Current name: {student['name']}")
        print(f"Current roll: {student['roll_number']}")

        name = input(
            "New name (press Enter to retain): "
        ).strip()

        roll = input(
            "New roll number (press Enter to retain): "
        ).strip()

        name = name or student["name"]
        roll = roll or student["roll_number"]

        update_student_details(
            student_id,
            name,
            roll
        )

        print("Student details updated successfully.")

    except (ValueError, Exception) as e:

        print(f"Update failed: {e}")


# -------------------------------------------------
# DEACTIVATE STUDENT
# -------------------------------------------------

def remove_student():

    display_students()

    try:

        student_id = int(
            input("\nEnter student ID to deactivate: ")
        )

        student = get_student_record(student_id)

        if not student:
            print("Student not found.")
            return

        if not student["is_active"]:
            print("Student is already inactive.")
            return

        confirm = input(
            f"Deactivate {student['name']}? (yes/no): "
        ).strip().lower()

        if confirm != "yes":
            print("Operation cancelled.")
            return

        deactivate_student(student_id)

        # Retrain without the inactive student
        remaining = get_all_active_students()

        if remaining:
            train_classifier()
        else:
            print(
                "No active students remain. "
                "Recognition cannot be started."
            )

        print("Student deactivated successfully.")

    except Exception as e:

        print(f"Deactivation failed: {e}")


# -------------------------------------------------
# REACTIVATE STUDENT
# -------------------------------------------------

def restore_student():

    display_students()

    try:

        student_id = int(
            input("\nEnter student ID to reactivate: ")
        )

        student = get_student_record(student_id)

        if not student:
            print("Student not found.")
            return

        if student["is_active"]:
            print("Student is already active.")
            return

        student_dir = DATASET_DIR / str(student_id)

        images = (
            list(student_dir.glob("*.png"))
            if student_dir.exists()
            else []
        )

        if len(images) < MIN_SAMPLES:

            print(
                "Student dataset is insufficient. "
                "Please re-register their face."
            )

            return

        activate_student(student_id)

        try:
            train_classifier()

        except Exception:

            deactivate_student(student_id)
            raise

        print("Student reactivated successfully.")

    except Exception as e:

        print(f"Reactivation failed: {e}")


# -------------------------------------------------
# RE-REGISTER STUDENT
# -------------------------------------------------

def reregister_student():

    display_students()

    try:

        student_id = int(
            input("\nEnter student ID: ")
        )

        student = get_student_record(student_id)

        if not student:
            print("Student not found.")
            return

        print(
            f"Capturing a fresh dataset for {student['name']}."
        )

        staging_dir = DATASET_DIR / f".staging_{student_id}"
        backup_dir = DATASET_DIR / f".backup_{student_id}"
        student_dir = DATASET_DIR / str(student_id)

        for directory in [staging_dir, backup_dir]:

            if directory.exists():
                shutil.rmtree(directory)

        # Capture new images without disturbing old dataset
        samples = generate_dataset(
            student_id,
            output_dir=staging_dir
        )

        if samples < MIN_SAMPLES:

            shutil.rmtree(
                staging_dir,
                ignore_errors=True
            )

            print("Insufficient images. Old dataset retained.")
            return

        was_active = bool(student["is_active"])
        old_dataset_moved = False

        try:

            if student_dir.exists():

                os.replace(
                    student_dir,
                    backup_dir
                )

                old_dataset_moved = True

            os.replace(
                staging_dir,
                student_dir
            )

            activate_student(student_id)

            train_classifier()

        except Exception:

            # Restore the previous dataset
            if student_dir.exists():
                shutil.rmtree(student_dir)

            if old_dataset_moved and backup_dir.exists():

                os.replace(
                    backup_dir,
                    student_dir
                )

            if not was_active:
                deactivate_student(student_id)

            raise

        # Training succeeded; remove old backup
        shutil.rmtree(
            backup_dir,
            ignore_errors=True
        )

        print("Student dataset updated successfully.")
        print("Recognition model retrained successfully.")

    except Exception as e:

        print(f"Re-registration failed: {e}")

    finally:

        # Remove incomplete staging directory
        if 'staging_dir' in locals():
            shutil.rmtree(
                staging_dir,
                ignore_errors=True
            )
