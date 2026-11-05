
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

from database import get_all_active_students


def run_recognition():

    # Load Haar Cascade
    face_cascade = cv2.CascadeClassifier(
        str(CASCADE_PATH)
    )

    if face_cascade.empty():
        raise FileNotFoundError(
            "Haar Cascade file not found."
        )

    # Check model
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Classifier not found. Train the model first."
        )

    # Load trained LBPH model
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read(str(MODEL_PATH))

    # Load student information dynamically
    students = get_all_active_students()

    student_map = {
        student["id"]: student
        for student in students
    }

    if not student_map:
        raise ValueError("No registered students found.")

    # Initialize camera
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        raise RuntimeError("Cannot open camera.")

    print("\nFace recognition started.")
    print("Press Q or ENTER to exit.")

    try:

        while True:

            ret, frame = cap.read()

            if not ret or frame is None:
                print("Unable to capture frame.")
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

                # Crop detected face
                face = gray[y:y+h, x:x+w]

                # Resize to training dimensions
                face = cv2.resize(
                    face,
                    (IMAGE_WIDTH, IMAGE_HEIGHT)
                )

                # Predict identity
                student_id, distance = clf.predict(face)

                student = student_map.get(student_id)

                # LBPH returns a distance, not a probability.
                if (
                    student is not None
                    and distance <= RECOGNITION_THRESHOLD
                ):

                    name = student["name"]
                    roll = student["roll_number"]

                    label = f"{name} | {roll}"

                    color = (0, 255, 0)

                else:

                    label = "UNKNOWN"
                    color = (0, 0, 255)

                # Draw bounding box
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x+w, y+h),
                    color,
                    2
                )

                # Display identity
                cv2.putText(
                    frame,
                    label,
                    (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2,
                    cv2.LINE_AA
                )

                # Display LBPH distance for testing
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
                "Face Recognition System",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 13:
                break

    finally:

        cap.release()
        cv2.destroyAllWindows()

    print("Recognition stopped.")
