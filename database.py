
import sqlite3
from datetime import datetime

from config import DATABASE_PATH


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
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

    conn.commit()
    conn.close()

    print("Database initialized successfully.")


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

        student_id = cursor.lastrowid

        return student_id

    except sqlite3.IntegrityError:

        raise ValueError(
            "A student with this roll number already exists."
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


def delete_student(student_id):

    conn = get_connection()

    conn.execute("""
        DELETE FROM students
        WHERE id = ?
    """, (student_id,))

    conn.commit()
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
        SELECT id, roll_number, name, created_at
        FROM students
        WHERE is_active = 1
        ORDER BY id
    """).fetchall()

    conn.close()

    return [dict(student) for student in students]
