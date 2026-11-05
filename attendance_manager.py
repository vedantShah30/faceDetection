
from database import (
    mark_attendance,
    get_period_report
)


def process_recognized_student(student_id, period_id):

    result = mark_attendance(
        student_id,
        period_id
    )

    if result == "marked":

        print(
            f"[ATTENDANCE] Student ID {student_id} marked PRESENT."
        )

    elif result == "already_marked":

        print(
            f"[ATTENDANCE] Student ID {student_id} "
            f"already marked."
        )

    elif result == "period_closed":

        print(
            "[ATTENDANCE] Period has expired."
        )

    return result


def display_attendance_report(period_id):

    records = get_period_report(period_id)

    print("\n========== ATTENDANCE REPORT ==========\n")

    print(
        f"{'ROLL NUMBER':<20}"
        f"{'NAME':<25}"
        f"{'STATUS':<12}"
        f"{'TIME':<20}"
    )

    print("-" * 77)

    present = 0
    absent = 0

    for record in records:

        status = record["attendance_status"]

        if status == "Present":
            present += 1
        else:
            absent += 1

        print(
            f"{record['roll_number']:<20}"
            f"{record['name']:<25}"
            f"{status:<12}"
            f"{(record['marked_at'] or '-'):<20}"
        )

    print("\n========== SUMMARY ==========")

    print(f"Present: {present}")
    print(f"Absent: {absent}")
    print(f"Total: {len(records)}")
