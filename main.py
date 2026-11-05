
import shutil

from config import DATASET_DIR, MIN_SAMPLES

from database import (
    initialize_database,
    create_student,
    activate_student,
    delete_student,
    get_all_active_students
)

from dataset import generate_dataset

from trainer import train_classifier

from recognizer import run_recognition


def register_student():

    print("\n========== STUDENT REGISTRATION ==========")

    roll_number = input(
        "Enter student roll number: "
    ).strip()

    name = input(
        "Enter student name: "
    ).strip()

    if not roll_number or not name:
        print("Name and roll number cannot be empty.")
        return

    try:

        # Create inactive student record
        student_id = create_student(
            roll_number,
            name
        )

        print(f"\nStudent ID generated: {student_id}")

        # Generate face dataset
        samples = generate_dataset(student_id)

        # Check minimum dataset size
        if samples < MIN_SAMPLES:

            print(
                f"\nRegistration cancelled. "
                f"Minimum {MIN_SAMPLES} images required."
            )

            delete_student(student_id)

            student_dir = DATASET_DIR / str(student_id)

            if student_dir.exists():
                shutil.rmtree(student_dir)

            return

        # Activate student
        activate_student(student_id)

        print("\nStudent registered successfully.")

        # Retrain model automatically
        print("\nUpdating recognition model...")

        train_classifier()

        print("\nRegistration and model update completed.")

    except (ValueError, RuntimeError, FileNotFoundError) as e:

        print(f"\nRegistration error: {e}")

        if 'student_id' in locals():

            delete_student(student_id)

            student_dir = DATASET_DIR / str(student_id)

            if student_dir.exists():
                shutil.rmtree(student_dir)

    except Exception as e:

        print(f"\nUnexpected error: {e}")

        if 'student_id' in locals():

            delete_student(student_id)

            student_dir = DATASET_DIR / str(student_id)

            if student_dir.exists():
                shutil.rmtree(student_dir)


def view_students():

    students = get_all_active_students()

    print("\n========== REGISTERED STUDENTS ==========")

    if not students:
        print("No registered students.")
        return

    print(
        f"{'ID':<8}"
        f"{'ROLL NUMBER':<20}"
        f"{'NAME':<25}"
    )

    print("-" * 53)

    for student in students:

        print(
            f"{student['id']:<8}"
            f"{student['roll_number']:<20}"
            f"{student['name']:<25}"
        )


def main():

    initialize_database()

    while True:

        print("\n")
        print("=" * 45)
        print("       FACE RECOGNITION ATTENDANCE")
        print("=" * 45)

        print("1. Register New Student")
        print("2. Train Classifier")
        print("3. Start Face Recognition")
        print("4. View Registered Students")
        print("5. Exit")

        choice = input("\nEnter your choice: ").strip()

        try:

            if choice == "1":

                register_student()

            elif choice == "2":

                train_classifier()

            elif choice == "3":

                run_recognition()

            elif choice == "4":

                view_students()

            elif choice == "5":

                print("Exiting application.")
                break

            else:

                print("Invalid choice. Try again.")

        except Exception as e:

            print(f"\nError: {e}")


if __name__ == "__main__":

    main()
