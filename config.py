
from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent

# Directories
DATASET_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
DATABASE_DIR = BASE_DIR / "database"

# Files
CASCADE_PATH = BASE_DIR / "haarcascade_frontalface_default.xml"
MODEL_PATH = MODEL_DIR / "classifier.xml"
DATABASE_PATH = DATABASE_DIR / "attendance.db"

# Camera
CAMERA_INDEX = 0

# Face dataset settings
IMAGE_WIDTH = 200
IMAGE_HEIGHT = 200

TARGET_SAMPLES = 200
MIN_SAMPLES = 30
CAPTURE_EVERY_N_FRAMES = 3

# Face detection
FACE_SCALE_FACTOR = 1.3
FACE_MIN_NEIGHBORS = 5

# LBPH recognition
# Lower distance means a better match.
# This is an initial threshold and must be calibrated experimentally.
RECOGNITION_THRESHOLD = 70

# Create directories automatically
DATASET_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

# Period management
DEFAULT_PERIOD_DURATION = 60

# Time format is local machine time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
