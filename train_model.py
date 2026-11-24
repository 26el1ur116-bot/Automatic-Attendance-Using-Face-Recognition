"""
Module: Model Training
Trains the OpenCV LBPH (Local Binary Patterns Histograms) Face Recognizer
using the images collected in the dataset directory with Histogram Equalization.
"""

import os
import cv2
import json
import numpy as np
import winsound
import config

def train_model():
    """
    Scans the dataset directory, applies Histogram Equalization,
    trains the LBPH model, and saves trainer.yml + labels.json.
    Returns (True, message) on success, or (False, error) on failure.
    """
    if not os.path.exists(config.DATASET_DIR):
        return False, "Dataset directory does not exist. Please register students first."

    all_folders = [f for f in os.listdir(config.DATASET_DIR) if os.path.isdir(os.path.join(config.DATASET_DIR, f))]
    # Filter only folders that actually contain image files
    student_folders = []
    for f in all_folders:
        fpath = os.path.join(config.DATASET_DIR, f)
        imgs = [img for img in os.listdir(fpath) if img.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if len(imgs) > 0:
            student_folders.append(f)

    if not student_folders:
        if os.path.exists(config.TRAINER_PATH):
            os.remove(config.TRAINER_PATH)
        if os.path.exists(config.LABELS_PATH):
            os.remove(config.LABELS_PATH)
        return False, "No student face images found in 'data/dataset'. Please click 'Register Student' first."

    print("\n[INFO] Starting model training with Histogram Equalization...")
    print(f"[INFO] Found {len(student_folders)} registered student(s):")

    faces = []
    labels = []
    label_map = {}

    current_id = 0
    total_images = 0

    for folder_name in sorted(student_folders):
        folder_path = os.path.join(config.DATASET_DIR, folder_name)

        parts = folder_name.split("_", 1)
        roll_no = parts[0]
        name = parts[1].replace("_", " ") if len(parts) > 1 else folder_name
        age = 19

        info_path = os.path.join(folder_path, "info.json")
        if os.path.exists(info_path):
            try:
                with open(info_path, "r") as info_file:
                    info_data = json.load(info_file)
                    roll_no = str(info_data.get("roll_no", roll_no))
                    name = str(info_data.get("name", name))
                    age = int(info_data.get("age", age))
            except Exception:
                pass

        label_map[current_id] = {
            "id": current_id,
            "roll_no": roll_no,
            "name": name,
            "age": age,
            "folder": folder_name
        }

        print(f"  --> Student {current_id + 1}: {name} (Roll: {roll_no} | Age: {age})")

        image_names = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        for img_name in image_names:
            img_path = os.path.join(folder_path, img_name)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            if img.shape != (config.FACE_HEIGHT, config.FACE_WIDTH):
                img = cv2.resize(img, (config.FACE_WIDTH, config.FACE_HEIGHT))

            # Apply Histogram Equalization
            img = cv2.equalizeHist(img)

            faces.append(img)
            labels.append(current_id)
            total_images += 1

        current_id += 1

    if total_images == 0:
        return False, "No valid face images found in the dataset folders."

    print(f"\n[INFO] Training LBPH Face Recognizer on {total_images} facial images across {len(student_folders)} student(s)...")

    recognizer = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
    recognizer.train(faces, np.array(labels))

    recognizer.write(config.TRAINER_PATH)
    with open(config.LABELS_PATH, "w") as f:
        json.dump(label_map, f, indent=4)

    try:
        winsound.Beep(1400, 200)
    except Exception:
        pass

    msg = f"Training completed successfully! {len(student_folders)} student(s) and {total_images} image samples trained."
    print(f"[SUCCESS] {msg}")
    print(f"[INFO] Model saved to: {config.TRAINER_PATH}")
    print(f"[INFO] Labels saved to: {config.LABELS_PATH}")
    print("[NEXT STEP] Click 'Start Attendance' to begin recording.")
    return True, msg

if __name__ == "__main__":
    print("=" * 60)
    print("        FACE RECOGNITION ATTENDANCE SYSTEM - MODEL TRAINING     ")
    print("=" * 60)
    success, message = train_model()
