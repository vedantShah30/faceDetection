
import sqlite3

from datetime import datetime

from config import DATABASE_PATH


def get_connection():

    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=10
    )

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def initialize_database():

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            roll_number TEXT UNIQUE NOT NULL,

            name TEXT NOT NULL,

            created_at TEXT NOT NULL,

            is_active INTEGER DEFAULT 0

        )
    """)

    # Period table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS periods (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            subject TEXT NOT NULL,

            date TEXT NOT NULL,

            start_time TEXT NOT NULL,

            end_time TEXT NOT NULL,

            duration_minutes INTEGER NOT NULL DEFAULT 60,

            status TEXT NOT NULL DEFAULT 'scheduled'
                CHECK(status IN ('scheduled', 'active', 'closed')),

            created_at TEXT NOT NULL

        )
    """)

    # Only one active period is allowed at a time.
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        one_active_period
        ON periods(status)
        WHERE status = 'active'
    """)

    # Attendance table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER NOT NULL,

            period_id INTEGER NOT NULL,

            marked_at TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'present'
                CHECK(status IN ('present')),

            FOREIGN KEY(student_id)
                REFERENCES students(id),

            FOREIGN KEY(period_id)
                REFERENCES periods(id),

            UNIQUE(student_id, period_id)

        )
    """)

    conn.commit()
    conn.close()

    print("Database initialized successfully.")


# -------------------------------------------------
# STUDENT OPERATIONS
# -------------------------------------------------

def create_student(roll_number, name):

    conn = get_connection()

    try:

        cursor = conn.execute("""
            INSERT INTO students
            (roll_number, name, created_at, is_active)

            VALUES (?, ?, ?, 0)
        """, (
            roll_number,
            name,
            datetime.now().isoformat()
        ))

        conn.commit()

        return cursor.lastrowid

    except sqlite3.IntegrityError:

        raise ValueError(
            "Student roll number already exists."
        )

    finally:
        conn.close()


def activate_student(student_id):

    conn = get_connection()

    conn.execute("""
        UPDATE students
        SET is_active = 1
        WHERE id = ?
    """, (student_id,))

    conn.commit()
    conn.close()


def deactivate_student(student_id):

    conn = get_connection()

    conn.execute("""
        UPDATE students
        SET is_active = 0
        WHERE id = ?
    """, (student_id,))

    conn.commit()
    conn.close()


def delete_student(student_id):

    conn = get_connection()

    try:

        conn.execute("""
            DELETE FROM students

            WHERE id = ?

            AND NOT EXISTS (
                SELECT 1
                FROM attendance
                WHERE attendance.student_id = students.id
            )
        """, (student_id,))

        conn.commit()

    finally:
        conn.close()


def get_student_by_roll(roll_number):

    conn = get_connection()

    student = conn.execute("""
        SELECT *
        FROM students
        WHERE roll_number = ?
    """, (roll_number,)).fetchone()

    conn.close()

    return dict(student) if student else None


def get_student_by_id(student_id):

    conn = get_connection()

    student = conn.execute("""
        SELECT *
        FROM students
        WHERE id = ? AND is_active = 1
    """, (student_id,)).fetchone()

    conn.close()

    return dict(student) if student else None


def get_all_active_students():

    conn = get_connection()

    students = conn.execute("""
        SELECT *
        FROM students
        WHERE is_active = 1
        ORDER BY id
    """).fetchall()

    conn.close()

    return [dict(s) for s in students]


# -------------------------------------------------
# PERIOD OPERATIONS
# -------------------------------------------------

def create_period(subject, duration_minutes=60):

    if not subject.strip():
        raise ValueError("Subject name cannot be empty.")

    if duration_minutes <= 0:
        raise ValueError("Duration must be positive.")

    conn = get_connection()

    now = datetime.now()

    start_time = now
    end_time = now.replace(
        second=0,
        microsecond=0
    )

    from datetime import timedelta

    end_time = start_time + timedelta(
        minutes=duration_minutes
    )

    cursor = conn.execute("""
        INSERT INTO periods
        (
            subject,
            date,
            start_time,
            end_time,
            duration_minutes,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, 'scheduled', ?)
    """, (
        subject.strip(),
        start_time.strftime("%Y-%m-%d"),
        start_time.strftime("%Y-%m-%d %H:%M:%S"),
        end_time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_minutes,
        now.strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()

    period_id = cursor.lastrowid

    conn.close()

    return period_id


def start_period(period_id):

    conn = get_connection()

    try:

        conn.execute("BEGIN IMMEDIATE")

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        period = conn.execute("""
            SELECT *
            FROM periods
            WHERE id = ?
        """, (period_id,)).fetchone()

        if not period:
            raise ValueError("Period does not exist.")

        if period["status"] != "scheduled":
            raise ValueError("Period cannot be started.")

        active = conn.execute("""
            SELECT id
            FROM periods
            WHERE status = 'active'
        """).fetchone()

        if active:
            raise ValueError(
                "Another period is already active."
            )

        # Recalculate the actual period duration from start.
        from datetime import timedelta

        end = datetime.now() + timedelta(
            minutes=period["duration_minutes"]
        )

        conn.execute("""
            UPDATE periods
            SET
                status = 'active',
                start_time = ?,
                end_time = ?,
                date = ?
            WHERE id = ?
        """, (
            now,
            end.strftime("%Y-%m-%d %H:%M:%S"),
            datetime.now().strftime("%Y-%m-%d"),
            period_id
        ))

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()


def close_period(period_id):

    conn = get_connection()

    cursor = conn.execute("""
        UPDATE periods
        SET status = 'closed'
        WHERE id = ? AND status = 'active'
    """, (period_id,))

    conn.commit()

    updated = cursor.rowcount > 0

    conn.close()

    return updated


def get_period(period_id):

    conn = get_connection()

    period = conn.execute("""
        SELECT *
        FROM periods
        WHERE id = ?
    """, (period_id,)).fetchone()

    conn.close()

    return dict(period) if period else None


def get_active_period():

    conn = get_connection()

    period = conn.execute("""
        SELECT *
        FROM periods
        WHERE status = 'active'
        LIMIT 1
    """).fetchone()

    conn.close()

    return dict(period) if period else None


def get_all_periods():

    conn = get_connection()

    periods = conn.execute("""
        SELECT *
        FROM periods
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [dict(p) for p in periods]


# -------------------------------------------------
# ATTENDANCE OPERATIONS
# -------------------------------------------------

def mark_attendance(student_id, period_id):

    conn = get_connection()

    try:

        conn.execute("BEGIN IMMEDIATE")

        now = datetime.now()

        period = conn.execute("""
            SELECT *
            FROM periods
            WHERE id = ?
        """, (period_id,)).fetchone()

        if not period or period["status"] != "active":
            raise ValueError("No active attendance period.")

        end_time = datetime.strptime(
            period["end_time"],
            "%Y-%m-%d %H:%M:%S"
        )

        if now >= end_time:

            conn.execute("""
                UPDATE periods
                SET status = 'closed'
                WHERE id = ?
            """, (period_id,))

            conn.commit()

            return "period_closed"

        student = conn.execute("""
            SELECT id
            FROM students
            WHERE id = ? AND is_active = 1
        """, (student_id,)).fetchone()

        if not student:
            raise ValueError("Student is not active.")

        cursor = conn.execute("""
            INSERT OR IGNORE INTO attendance
            (
                student_id,
                period_id,
                marked_at,
                status
            )
            VALUES (?, ?, ?, 'present')
        """, (
            student_id,
            period_id,
            now.strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()

        if cursor.rowcount == 1:
            return "marked"

        return "already_marked"

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()


def get_period_attendance(period_id):

    conn = get_connection()

    records = conn.execute("""
        SELECT
            s.id AS student_id,
            s.roll_number,
            s.name,
            a.marked_at,
            a.status

        FROM attendance a

        JOIN students s
        ON s.id = a.student_id

        WHERE a.period_id = ?

        ORDER BY s.roll_number
    """, (period_id,)).fetchall()

    conn.close()

    return [dict(r) for r in records]


def get_period_report(period_id):

    conn = get_connection()

    records = conn.execute("""
        SELECT
            s.id,
            s.roll_number,
            s.name,

            a.marked_at,

            CASE
                WHEN a.id IS NOT NULL THEN 'Present'
                ELSE 'Absent'
            END AS attendance_status

        FROM students s

        LEFT JOIN attendance a
            ON s.id = a.student_id
            AND a.period_id = ?

        WHERE s.is_active = 1

        ORDER BY s.roll_number
    """, (period_id,)).fetchall()

    conn.close()

    return [dict(r) for r in records]
