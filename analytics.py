
from database import (
    get_connection,
    get_all_active_students
)


# -------------------------------------------------
# STUDENT ATTENDANCE OVERVIEW
# -------------------------------------------------

def get_student_overview(student_id):

    conn = get_connection()

    result = conn.execute("""
        SELECT

            s.id,
            s.name,
            s.roll_number,

            COUNT(DISTINCT p.id) AS total_classes,

            COUNT(DISTINCT a.id) AS attended_classes

        FROM students s

        LEFT JOIN periods p
            ON p.status = 'closed'
            AND datetime(p.start_time) >= datetime(s.created_at)

        LEFT JOIN attendance a
            ON a.student_id = s.id
            AND a.period_id = p.id

        WHERE s.id = ?

        GROUP BY s.id

    """, (student_id,)).fetchone()

    conn.close()

    if not result:
        return None

    total = result["total_classes"]
    attended = result["attended_classes"]

    percentage = (
        (attended / total) * 100
        if total > 0
        else 0
    )

    return {
        "student_id": result["id"],
        "name": result["name"],
        "roll_number": result["roll_number"],
        "total_classes": total,
        "attended_classes": attended,
        "absent_classes": total - attended,
        "attendance_percentage": round(percentage, 2)
    }


# -------------------------------------------------
# SUBJECT-WISE ATTENDANCE
# -------------------------------------------------

def get_subject_attendance(student_id):

    conn = get_connection()

    results = conn.execute("""
        SELECT

            p.subject,

            COUNT(DISTINCT p.id) AS total_classes,

            COUNT(DISTINCT a.id) AS attended_classes

        FROM periods p

        LEFT JOIN attendance a
            ON a.period_id = p.id
            AND a.student_id = ?

        WHERE p.status = 'closed'

        AND datetime(p.start_time) >= (
            SELECT datetime(created_at)
            FROM students
            WHERE id = ?
        )

        GROUP BY p.subject

        ORDER BY p.subject

    """, (student_id, student_id)).fetchall()

    conn.close()

    report = []

    for row in results:

        total = row["total_classes"]
        attended = row["attended_classes"]

        percentage = (
            attended / total * 100
            if total > 0
            else 0
        )

        report.append({
            "subject": row["subject"],
            "total_classes": total,
            "attended_classes": attended,
            "absent_classes": total - attended,
            "attendance_percentage": round(
                percentage,
                2
            )
        })

    return report


# -------------------------------------------------
# STUDENTS BELOW ATTENDANCE THRESHOLD
# -------------------------------------------------

def get_low_attendance_students(threshold=75):

    students = get_all_active_students()

    low_attendance = []

    for student in students:

        report = get_student_overview(
            student["id"]
        )

        if report and report["total_classes"] > 0:

            if report["attendance_percentage"] < threshold:

                low_attendance.append(report)

    return low_attendance


# -------------------------------------------------
# OVERALL CLASS ANALYTICS
# -------------------------------------------------

def get_class_overview():

    conn = get_connection()

    result = conn.execute("""
        SELECT

            COUNT(*) AS total_periods,

            COUNT(DISTINCT subject) AS total_subjects

        FROM periods

        WHERE status = 'closed'

    """).fetchone()

    conn.close()

    students = get_all_active_students()

    return {
        "total_students": len(students),
        "total_periods": result["total_periods"],
        "total_subjects": result["total_subjects"]
    }


# -------------------------------------------------
# DISPLAY STUDENT ANALYTICS
# -------------------------------------------------

def display_student_analytics(student_id):

    report = get_student_overview(student_id)

    if not report:
        print("Student not found.")
        return

    print("\n========== STUDENT ATTENDANCE ==========")

    print(f"Name: {report['name']}")
    print(f"Roll Number: {report['roll_number']}")

    print(f"Total Classes: {report['total_classes']}")
    print(f"Present: {report['attended_classes']}")
    print(f"Absent: {report['absent_classes']}")

    print(
        f"Attendance: "
        f"{report['attendance_percentage']}%"
    )

    print("\n========== SUBJECT-WISE ATTENDANCE ==========")

    subjects = get_subject_attendance(student_id)

    for subject in subjects:

        print(
            f"{subject['subject']}: "
            f"{subject['attended_classes']}/"
            f"{subject['total_classes']} "
            f"({subject['attendance_percentage']}%)"
        )


# -------------------------------------------------
# DISPLAY LOW ATTENDANCE STUDENTS
# -------------------------------------------------

def display_low_attendance(threshold=75):

    students = get_low_attendance_students(threshold)

    print(
        f"\n========== STUDENTS BELOW {threshold}% =========="
    )

    if not students:
        print("No students below the threshold.")
        return

    for student in students:

        print(
            f"{student['roll_number']} | "
            f"{student['name']} | "
            f"{student['attendance_percentage']}%"
        )
