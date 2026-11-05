from datetime import datetime

from database import close_period
import cv2

from config import (
    CASCADE_PATH,
    MODEL_PATH,
    CAMERA_INDEX,
    IMAGE_WIDTH,
    IMAGE_HEIGHT,
    FACE_SCALE_FACTOR,
    FACE_MIN_NEIGHBORS,
    RECOGNITION_THRESHOLD
)

from database import (
    get_all_active_students,
    get_active_period,
    get_period
)

from attendance_manager import (
    process_recognized_student
)


def run_recognition(period_id=None):

    face_cascade = cv2.CascadeClassifier(
        str(CASCADE_PATH)
    )

    if face_cascade.empty():
        raise FileNotFoundError(
            "Haar Cascade file not found."
        )

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Classifier not found. Train the model first."
        )

    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read(str(MODEL_PATH))

    students = get_all_active_students()

    student_map = {
        student["id"]: student
        for student in students
    }

    if not student_map:
        raise ValueError("No registered students.")

    if period_id is not None:

        period = get_period(period_id)

        if not period or period["status"] != "active":
            raise ValueError("Attendance period is not active.")

    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        raise RuntimeError("Cannot open camera.")

    # Avoid repeatedly processing the same student
    processed_students = set()

    print("\nRecognition started.")

    if period_id:
        print(f"Attendance enabled for period {period_id}")

    print("Press Q or ENTER to stop.")

    try:

        while True:

            ret, frame = cap.read()

            if not ret or frame is None:
                print("Unable to capture frame.")
                break

            # Check whether the attendance period is still active
            if period_id is not None:

                period = get_period(period_id)

                if not period or period["status"] != "active":
                    print("Attendance period has ended.")
                    break

                end_time = datetime.strptime(
                    period["end_time"],
                    "%Y-%m-%d %H:%M:%S"
                )

                if datetime.now() >= end_time:

                    close_period(period_id)

                    print("60-minute period completed.")
                    break

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=FACE_SCALE_FACTOR,
                minNeighbors=FACE_MIN_NEIGHBORS
            )

            for (x, y, w, h) in faces:

                face = gray[y:y+h, x:x+w]

                face = cv2.resize(
                    face,
                    (IMAGE_WIDTH, IMAGE_HEIGHT)
                )

                student_id, distance = clf.predict(face)

                student = student_map.get(student_id)

                if (
                    student is not None
                    and distance <= RECOGNITION_THRESHOLD
                ):

                    name = student["name"]
                    roll = student["roll_number"]

                    label = f"{name} | {roll}"

                    color = (0, 255, 0)

                    # Attendance integration
                    if (
                        period_id is not None
                        and student_id not in processed_students
                    ):

                        try:

                            result = process_recognized_student(
                                student_id,
                                period_id
                            )

                            processed_students.add(student_id)

                            if result == "marked":
                                label += " | PRESENT"

                            elif result == "already_marked":
                                label += " | ALREADY MARKED"

                            elif result == "period_closed":
                                label += " | PERIOD CLOSED"
                                break

                        except ValueError as e:

                            print(f"Attendance error: {e}")

                    elif (
                        period_id is not None
                        and student_id in processed_students
                    ):

                        label += " | PROCESSED"

                else:

                    label = "UNKNOWN"
                    color = (0, 0, 255)

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x+w, y+h),
                    color,
                    2
                )

                cv2.putText(
                    frame,
                    label,
                    (x, max(y-10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                    cv2.LINE_AA
                )

                cv2.putText(
                    frame,
                    f"Distance: {distance:.1f}",
                    (x, y+h+25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    color,
                    1
                )

            cv2.imshow(
                "Face Attendance System",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 13:
                break

    finally:

        cap.release()
        cv2.destroyAllWindows()

    print("\nRecognition stopped.")

    print(
        f"Students processed in this session: "
        f"{len(processed_students)}"
    )
