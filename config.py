import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATASET_DIR = os.path.join(DATA_DIR, "dataset")
ATTENDANCE_DIR = os.path.join(DATA_DIR, "attendance")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# File Paths
CASCADE_PATH = os.path.join(MODELS_DIR, "haarcascade_frontalface_default.xml")
TRAINER_PATH = os.path.join(MODELS_DIR, "trainer.yml")
LABELS_PATH = os.path.join(MODELS_DIR, "labels.json")
ALERT_AUDIO_PATH = os.path.join(MODELS_DIR, "person_not_recognized.wav")

# Ensure required directories exist
for folder in [DATASET_DIR, ATTENDANCE_DIR, MODELS_DIR]:
    os.makedirs(folder, exist_ok=True)

# Camera & Detection Settings
CAMERA_INDEX = 0
NUM_SAMPLES = 40                 # Number of face photos captured during registration
FACE_WIDTH = 200                 # Standardized face width (px)
FACE_HEIGHT = 200                # Standardized face height (px)

# College Student Age Restrictions (Anti-Proxy Protection)
MIN_STUDENT_AGE = 16             # Minimum permitted college student age
MAX_STUDENT_AGE = 25             # Maximum permitted college student age

# Calibrated Biometric Matching Thresholds (LBPH Chi-Square Distance)
# Mathematical Calibration:
#   - Genuine live webcam faces score between 20 and 52
#   - Unknown strangers score between 62.7 and 66+
# Setting threshold to 57 provides a 5-point safety margin on both sides:
#   -> Genuine students (<54) are recognized smoothly!
#   -> Unknown strangers (>62) are strictly rejected!
CONFIDENCE_THRESHOLD = 57        
BIOMETRIC_VERIFY_THRESHOLD = 56  
BIOMETRIC_DUPLICATE_THRESHOLD = 54 

# Anti-Flicker & Voice Alarm Timing
CONSECUTIVE_FRAMES_REQUIRED = 4  # 4 consecutive frames (~0.3s) for responsive attendance marking
UNKNOWN_STREAK_REQUIRED = 12     # Must be unknown for 12 frames (~0.8s) before voice alarm sounds
SESSION_LOCK_SECONDS = 4         # Cooldown period right after marking attendance
UNKNOWN_ALERT_COOLDOWN = 3.5     # Seconds between voice alerts for unknown faces
