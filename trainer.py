
import cv2
import os

import numpy as np

from config import (
    DATASET_DIR,
    MODEL_PATH,
    IMAGE_WIDTH,
    IMAGE_HEIGHT
)

from database import get_all_active_students


def train_classifier():

    # Check LBPH availability
    if not hasattr(cv2, "face"):
        raise RuntimeError(
            "OpenCV contrib is missing. "
            "Install opencv-contrib-python."
        )

    students = get_all_active_students()

    if not students:
        raise ValueError("No active students available.")

    faces = []
    labels = []

    student_counts = {}

    print("\nStarting model training...\n")

    for student in students:

        student_id = student["id"]

        student_dir = DATASET_DIR / str(student_id)

        if not student_dir.exists():
            raise FileNotFoundError(
                f"Dataset missing for student {student_id}"
            )

        image_files = sorted(
            student_dir.glob("*.png")
        )

        count = 0

        for image_path in image_files:

            img = cv2.imread(
                str(image_path),
                cv2.IMREAD_GRAYSCALE
            )

            if img is None:
                print(f"Skipping invalid image: {image_path}")
                continue

            img = cv2.resize(
                img,
                (IMAGE_WIDTH, IMAGE_HEIGHT)
            )

            faces.append(img)
            labels.append(student_id)

            count += 1

        if count == 0:
            raise ValueError(
                f"No valid images for student {student_id}"
            )

        student_counts[student_id] = count

        print(
            f"{student['name']} "
            f"({student['roll_number']}): {count} images"
        )

    # Convert labels into NumPy array
    labels = np.array(labels, dtype=np.int32)

    # Create LBPH recognizer
    clf = cv2.face.LBPHFaceRecognizer_create()

    # Train
    clf.train(faces, labels)

    # Save to temporary file first
    temp_model_path = MODEL_PATH.with_name(
        "classifier.tmp.xml"
    )

    try:

        clf.write(str(temp_model_path))

        # Replace existing model only after successful training
        os.replace(
            temp_model_path,
            MODEL_PATH
        )

    finally:

        if temp_model_path.exists():
            temp_model_path.unlink()

    print("\nModel training completed.")
    print(f"Total students: {len(students)}")
    print(f"Total training images: {len(faces)}")
    print(f"Model saved at: {MODEL_PATH}")

    return True
