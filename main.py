
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

from student_manager import (
    display_students,
    search_student,
    edit_student,
    remove_student,
    restore_student,
    reregister_student
)

from analytics import (
    display_student_analytics,
    display_low_attendance,
    get_class_overview
)


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
    
def display_class_analytics():

    report = get_class_overview()

    print("\n========== CLASS OVERVIEW ==========")

    print(f"Active students: {report['total_students']}")
    print(f"Completed periods: {report['total_periods']}")
    print(f"Subjects: {report['total_subjects']}")


# -------------------------------------------------
# MAIN
# -------------------------------------------------


def main():

    initialize_database()

    while True:

        print("\n")
        print("=" * 55)
        print("          FACE RECOGNITION ATTENDANCE")
        print("=" * 55)

        print("\n--- CORE OPERATIONS ---")
        print("1. Register New Student")
        print("2. Train Classifier")
        print("3. Start Face Recognition")
        print("4. Create Attendance Period")
        print("5. Start Attendance")
        print("6. View Attendance Report")
        print("7. View All Periods")

        print("\n--- STUDENT MANAGEMENT ---")
        print("8. View All Students")
        print("9. Search Student")
        print("10. Update Student")
        print("11. Deactivate Student")
        print("12. Reactivate Student")
        print("13. Re-register Student Face")

        print("\n--- ATTENDANCE ANALYTICS ---")
        print("14. Student Attendance Analytics")
        print("15. Students Below 75%")
        print("16. Overall Class Analytics")

        print("\n17. Exit")

        choice = input("\nEnter your choice: ").strip()

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
                display_students()

            elif choice == "9":
                search_student()

            elif choice == "10":
                edit_student()

            elif choice == "11":
                remove_student()

            elif choice == "12":
                restore_student()

            elif choice == "13":
                reregister_student()

            elif choice == "14":

                display_students()

                student_id = input(
                    "\nEnter student ID: "
                ).strip()

                if student_id.isdigit():

                    display_student_analytics(
                        int(student_id)
                    )

                else:
                    print("Invalid student ID.")

            elif choice == "15":
                display_low_attendance(75)

            elif choice == "16":
                display_class_analytics()

            elif choice == "17":
                print("Exiting application.")
                break

            else:
                print("Invalid choice.")

        except Exception as e:

            print(f"\nApplication error: {e}")


if __name__ == "__main__":
    main()

