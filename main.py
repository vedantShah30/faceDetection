
import shutil

from config import DATASET_DIR, MIN_SAMPLES

from database import (
    initialize_database,
    create_student,
    activate_student,
    delete_student,
    get_all_active_students,
    get_all_periods,
    get_period
)

from dataset import generate_dataset
from trainer import train_classifier
from recognizer import run_recognition

from period_manager import (
    create_new_period,
    start_attendance_period
)

from attendance_manager import (
    display_attendance_report
)

from database import close_period


# -------------------------------------------------
# STUDENT REGISTRATION
# -------------------------------------------------

def register_student():

    print("\n========== STUDENT REGISTRATION ==========")

    roll_number = input(
        "Enter roll number: "
    ).strip()

    name = input(
        "Enter student name: "
    ).strip()

    if not roll_number or not name:
        print("Name and roll number are required.")
        return

    student_id = None
    activated = False

    try:

        student_id = create_student(
            roll_number,
            name
        )

        print(f"Generated student ID: {student_id}")

        samples = generate_dataset(student_id)

        if samples < MIN_SAMPLES:

            print("Insufficient face samples.")

            delete_student(student_id)

            student_dir = DATASET_DIR / str(student_id)

            if student_dir.exists():
                shutil.rmtree(student_dir)

            return

        activate_student(student_id)
        activated = True

        print("Student registered successfully.")

        train_classifier()

    except Exception as e:

        print(f"Registration failed: {e}")

        if student_id is not None and not activated:

            delete_student(student_id)

            student_dir = DATASET_DIR / str(student_id)

            if student_dir.exists():
                shutil.rmtree(student_dir)

        elif student_id is not None and activated:

            # Retain the student's registration if training fails.
            print(
                "Student registration is retained. "
                "Retry model training."
            )


# -------------------------------------------------
# VIEW STUDENTS
# -------------------------------------------------

def view_students():

    students = get_all_active_students()

    print("\n========== REGISTERED STUDENTS ==========")

    if not students:
        print("No registered students.")
        return

    for student in students:

        print(
            f"ID: {student['id']} | "
            f"Roll: {student['roll_number']} | "
            f"Name: {student['name']}"
        )


# -------------------------------------------------
# VIEW PERIODS
# -------------------------------------------------

def view_periods():

    periods = get_all_periods()

    print("\n========== PERIOD HISTORY ==========")

    if not periods:
        print("No periods created.")
        return

    for period in periods:

        print(
            f"ID: {period['id']} | "
            f"Subject: {period['subject']} | "
            f"Date: {period['date']} | "
            f"Status: {period['status']} | "
            f"Duration: {period['duration_minutes']} minutes"
        )


# -------------------------------------------------
# START ATTENDANCE
# -------------------------------------------------

def start_attendance():

    period_id = start_attendance_period()

    if period_id is None:
        return

    try:

        print("\nStarting attendance camera...")

        run_recognition(period_id)

    except Exception as e:

        print(f"Recognition error: {e}")

    finally:

        # Close period when camera session ends.
        close_period(period_id)

        print("Attendance period closed.")


# -------------------------------------------------
# VIEW ATTENDANCE REPORT
# -------------------------------------------------

def view_report():

    view_periods()

    period_id = input(
        "\nEnter period ID for report: "
    ).strip()

    if not period_id.isdigit():
        print("Invalid period ID.")
        return

    period = get_period(int(period_id))

    if not period:
        print("Period not found.")
        return

    display_attendance_report(int(period_id))


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():

    initialize_database()

    while True:

        print("\n")
        print("=" * 50)
        print("       FACE RECOGNITION ATTENDANCE")
        print("=" * 50)

        print("1. Register New Student")
        print("2. Train Classifier")
        print("3. Start Face Recognition")
        print("4. Create Attendance Period")
        print("5. Start Attendance")
        print("6. View Attendance Report")
        print("7. View All Periods")
        print("8. View Registered Students")
        print("9. Exit")

        choice = input(
            "\nEnter your choice: "
        ).strip()

        try:

            if choice == "1":

                register_student()

            elif choice == "2":

                train_classifier()

            elif choice == "3":

                run_recognition()

            elif choice == "4":

                create_new_period()

            elif choice == "5":

                start_attendance()

            elif choice == "6":

                view_report()

            elif choice == "7":

                view_periods()

            elif choice == "8":

                view_students()

            elif choice == "9":

                print("Exiting application.")
                break

            else:

                print("Invalid choice.")

        except Exception as e:

            print(f"\nApplication error: {e}")


if __name__ == "__main__":

    main()
