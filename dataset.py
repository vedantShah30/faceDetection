
import cv2

from config import (
    DATASET_DIR,
    CASCADE_PATH,
    CAMERA_INDEX,
    IMAGE_WIDTH,
    IMAGE_HEIGHT,
    TARGET_SAMPLES,
    CAPTURE_EVERY_N_FRAMES,
    FACE_SCALE_FACTOR,
    FACE_MIN_NEIGHBORS
)
from pathlib import Path


def generate_dataset(student_id, output_dir=None):

    face_classifier = cv2.CascadeClassifier(
        str(CASCADE_PATH)
    )

    if face_classifier.empty():
        raise FileNotFoundError(
            "Haar Cascade classifier not found."
        )

    # Student-specific directory
    student_dir = (
        Path(output_dir)
        if output_dir is not None
        else DATASET_DIR / str(student_id)
    )

    student_dir.mkdir(parents=True, exist_ok=True)

    # Camera initialization
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        raise RuntimeError("Cannot open camera.")

    img_id = 0
    frame_count = 0

    print("\nStarting dataset collection.")
    print("Look directly at the camera.")
    print("Move your face slightly to capture different angles.")
    print("Press ENTER or Q to stop.\n")

    try:

        while img_id < TARGET_SAMPLES:

            ret, frame = cap.read()

            if not ret or frame is None:
                print("Unable to capture frame.")
                break

            frame_count += 1

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            faces = face_classifier.detectMultiScale(
                gray,
                scaleFactor=FACE_SCALE_FACTOR,
                minNeighbors=FACE_MIN_NEIGHBORS
            )

            status = "No face detected"

            # Capture only when exactly one face is visible
            if len(faces) == 1:

                x, y, w, h = faces[0]

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x+w, y+h),
                    (0, 255, 0),
                    2
                )

                status = "Face detected"

                # Capture periodically
                if frame_count % CAPTURE_EVERY_N_FRAMES == 0:

                    cropped_face = gray[y:y+h, x:x+w]

                    face = cv2.resize(
                        cropped_face,
                        (IMAGE_WIDTH, IMAGE_HEIGHT)
                    )

                    img_id += 1

                    file_path = (
                        student_dir / f"image_{img_id:03d}.png"
                    )

                    saved = cv2.imwrite(
                        str(file_path),
                        face
                    )

                    if not saved:
                        img_id -= 1
                        print("Failed to save image.")

                    else:
                        status = "Image captured"

            elif len(faces) > 1:

                status = "Multiple faces detected"

            # Display status
            cv2.putText(
                frame,
                f"Samples: {img_id}/{TARGET_SAMPLES}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                status,
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )

            cv2.imshow(
                "Student Dataset Collection",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == 13 or key == ord('q'):
                break

    finally:

        cap.release()
        cv2.destroyAllWindows()

    print(f"\nDataset collection finished.")
    print(f"Student ID: {student_id}")
    print(f"Images captured: {img_id}")

    return img_id
