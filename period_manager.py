
from datetime import datetime

from config import DEFAULT_PERIOD_DURATION

from database import (
    create_period,
    start_period,
    close_period,
    get_active_period,
    get_all_periods
)


def create_new_period():

    print("\n========== CREATE PERIOD ==========")

    subject = input(
        "Enter subject name: "
    ).strip()

    duration_input = input(
        f"Enter duration in minutes "
        f"(default {DEFAULT_PERIOD_DURATION}): "
    ).strip()

    duration = (
        int(duration_input)
        if duration_input
        else DEFAULT_PERIOD_DURATION
    )

    period_id = create_period(
        subject,
        duration
    )

    print(f"\nPeriod created successfully.")
    print(f"Period ID: {period_id}")

    return period_id


def start_attendance_period():

    active = get_active_period()

    if active:

        print(
            f"Period {active['id']} is already active."
        )

        return None

    print("\n========== AVAILABLE PERIODS ==========")

    periods = get_all_periods()

    scheduled = [
        p for p in periods
        if p["status"] == "scheduled"
    ]

    if not scheduled:

        print("No scheduled periods available.")
        return None

    for period in scheduled:

        print(
            f"ID: {period['id']} | "
            f"Subject: {period['subject']} | "
            f"Duration: {period['duration_minutes']} minutes"
        )

    period_id = int(
        input("\nEnter period ID to start: ")
    )

    start_period(period_id)

    print("\nAttendance period started.")

    return period_id


def stop_attendance_period():

    period = get_active_period()

    if not period:

        print("No active period.")
        return

    close_period(period["id"])

    print(
        f"Period {period['subject']} closed successfully."
    )


def check_period_expiry():

    period = get_active_period()

    if not period:
        return None

    end_time = datetime.strptime(
        period["end_time"],
        "%Y-%m-%d %H:%M:%S"
    )

    if datetime.now() >= end_time:

        close_period(period["id"])

        print("\nPeriod duration completed.")
        print("Attendance period automatically closed.")

        return None

    return period
