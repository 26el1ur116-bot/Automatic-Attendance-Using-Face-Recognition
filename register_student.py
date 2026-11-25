"""
Module: Student Registration & Face Dataset Collection
Includes Anti-Fraud & Identity Theft Protection:
1. Roll Number & Name Locking: Prevents others from using an existing student's details.
2. Biometric Ownership Challenge: If an existing student updates their photos,
   the camera verifies their face matches their biometric profile before allowing changes.
3. Biometric Uniqueness Check: Prevents an already-registered face from registering
   under a new roll number.
4. Histogram Equalization: Standardizes lighting & contrast for high-accuracy recognition.
5. Age Bracket Enforcement (16 to 25 years).
"""

import cv2
import os
import sys
import json
import time
import shutil
import winsound
import config

def get_registered_students_info():
    """
    Returns dictionaries of registered students (ignoring empty folders with 0 images):
    students_by_roll: { roll_lower: info }
    students_by_name: { name_lower: info }
    """
    students_by_roll = {}
    students_by_name = {}

    if not os.path.exists(config.DATASET_DIR):
        return students_by_roll, students_by_name

    for folder in os.listdir(config.DATASET_DIR):
        folder_path = os.path.join(config.DATASET_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        # Ignore empty folders
        img_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if len(img_files) == 0:
            continue

        parts = folder.split("_", 1)
        roll = parts[0]
        name = parts[1].replace("_", " ") if len(parts) > 1 else folder
        age = 19

        info_path = os.path.join(folder_path, "info.json")
        if os.path.exists(info_path):
            try:
                with open(info_path, "r") as f:
                    data = json.load(f)
                    roll = str(data.get("roll_no", roll))
                    name = str(data.get("name", name))
                    age = int(data.get("age", age))
            except Exception:
                pass

        item = {
            "roll_no": roll,
            "name": name,
            "age": age,
            "folder": folder,
            "folder_path": folder_path,
            "image_count": len(img_files)
        }
        students_by_roll[roll.strip().lower()] = item
        students_by_name[name.strip().lower()] = item

    return students_by_roll, students_by_name

def capture_student(student_name: str, roll_no: str, age: str, on_progress=None):
    """
    Enforces identity locking, biometric verification, age validation,
    and captures face samples with histogram equalization.
    """
    student_name = student_name.strip()
    roll_no = str(roll_no).strip()
    age_str = str(age).strip()

    if not student_name or not roll_no:
        return False, "Name and Roll Number cannot be empty."

    # 1. Validate Age (16 to 25)
    try:
        age_int = int(age_str)
    except ValueError:
        return False, "Age must be a valid number (e.g. 18, 19, 20)."

    if age_int < config.MIN_STUDENT_AGE or age_int > config.MAX_STUDENT_AGE:
        return False, (
            f"AGE RESTRICTION VIOLATION!\n\n"
            f"Class attendance is strictly restricted to students between "
            f"{config.MIN_STUDENT_AGE} and {config.MAX_STUDENT_AGE} years of age.\n\n"
            f"Entered Age: {age_int} (Ineligible for attendance)."
        )

    # 2. Check Existing Records (ignoring empty folders)
    registered_rolls, registered_names = get_registered_students_info()
    roll_key = roll_no.lower()
    name_key = student_name.lower()

    is_re_registering = False
    existing_owner_name = None

    if roll_key in registered_rolls:
        existing_info = registered_rolls[roll_key]
        existing_owner_name = existing_info["name"]

        if name_key != existing_owner_name.lower():
            return False, (
                f"SECURITY VIOLATION - ROLL NUMBER CONFLICT!\n\n"
                f"Roll Number '{roll_no}' is already registered to:\n"
                f"Student: '{existing_owner_name}'\n\n"
                f"You cannot register a different student under this Roll Number."
            )
        else:
            is_re_registering = True

    elif name_key in registered_names:
        existing_info = registered_names[name_key]
        existing_roll = existing_info["roll_no"]
        return False, (
            f"SECURITY VIOLATION - NAME CONFLICT!\n\n"
            f"Student '{student_name}' is already registered with:\n"
            f"Roll Number: '{existing_roll}'\n\n"
            f"Please enter the correct Roll Number, or delete the old entry from 'Manage Students'."
        )

    # Load existing recognizer and labels for biometric check
    recognizer = None
    label_map = {}
    if os.path.exists(config.TRAINER_PATH) and os.path.exists(config.LABELS_PATH):
        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(config.TRAINER_PATH)
            with open(config.LABELS_PATH, "r") as f:
                raw_labels = json.load(f)
                label_map = {int(k): v for k, v in raw_labels.items()}
        except Exception:
            recognizer = None

    if not os.path.exists(config.CASCADE_PATH):
        return False, f"Haar Cascade model not found at {config.CASCADE_PATH}"

    face_cascade = cv2.CascadeClassifier(config.CASCADE_PATH)

    # Initialize Webcam
    cap = config.open_camera()
    if not cap.isOpened():
        return False, "Could not access webcam. Ensure no other application (Zoom, Teams, Camera) is using it."

    has_model = (recognizer is not None and len(label_map) > 0)

    if is_re_registering:
        if not has_model:
            cap.release()
            return False, (
                f"Student '{student_name}' is already registered.\n"
                "To replace this student's face, please delete them from 'Manage Students' first."
            )
        current_phase = "VERIFY_OWNER"
    elif has_model:
        current_phase = "CHECK_UNIQUENESS"
    else:
        current_phase = "CAPTURE"

    check_frames = 0
    max_check_frames = 15
    owner_match_count = 0
    other_match_count = 0
    matched_other_name = ""
    matched_other_roll = ""

    count = 0
    last_capture_time = 0
    capture_interval = 0.12

    folder_name = f"{roll_no}_{student_name.replace(' ', '_')}"
    student_dir = os.path.join(config.DATASET_DIR, folder_name)

    print(f"\n[INFO] Starting camera registration for {student_name} (Roll: {roll_no})...")
    print(f"[INFO] Initial Phase: {current_phase}")
    print("[INFO] Press 'q', 'ESC', or click 'X' to cancel.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h_frame, w_frame, _ = frame.shape

            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.15,
                minNeighbors=5,
                minSize=(80, 80)
            )

            current_time = time.time()

            for (x, y, w, h) in faces:
                face_crop = gray[y:y+h, x:x+w]
                face_resized = cv2.resize(face_crop, (config.FACE_WIDTH, config.FACE_HEIGHT))
                # Histogram Equalization for lighting normalization
                face_equalized = cv2.equalizeHist(face_resized)

                # ----------------- SECURITY PHASE 1: VERIFY OWNER -----------------
                if current_phase == "VERIFY_OWNER":
                    label_id, conf = recognizer.predict(face_equalized)
                    check_frames += 1

                    if label_id in label_map and conf < config.BIOMETRIC_VERIFY_THRESHOLD:
                        predicted_roll = str(label_map[label_id]["roll_no"]).strip().lower()
                        if predicted_roll == roll_key:
                            owner_match_count += 1

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 200, 0), 2)
                    cv2.putText(frame, f"Authenticating Identity... ({check_frames}/{max_check_frames})",
                                (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 200, 0), 2)

                    if check_frames >= max_check_frames:
                        if owner_match_count >= 5:
                            print(f"[AUTH] Identity confirmed as {student_name}! Capturing new samples.")
                            current_phase = "CAPTURE"
                        else:
                            try:
                                winsound.Beep(600, 500)
                            except Exception:
                                pass
                            error_msg = (
                                f"IDENTITY THEFT ATTEMPT BLOCKED!\n\n"
                                f"This Roll Number ({roll_no}) belongs to: '{existing_owner_name}'.\n\n"
                                f"The face in front of the camera DOES NOT match the registered biometric profile!\n"
                                f"Another person cannot re-register or overwrite your details."
                            )
                            print(f"[SECURITY ALERT] {error_msg}")
                            return False, error_msg
                    break

                # ----------------- SECURITY PHASE 2: CHECK UNIQUENESS -----------------
                elif current_phase == "CHECK_UNIQUENESS":
                    label_id, conf = recognizer.predict(face_equalized)
                    check_frames += 1

                    if label_id in label_map and conf < config.BIOMETRIC_DUPLICATE_THRESHOLD:
                        other_match_count += 1
                        matched_other_name = label_map[label_id]["name"]
                        matched_other_roll = label_map[label_id]["roll_no"]

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 200, 0), 2)
                    cv2.putText(frame, f"Checking Face Uniqueness... ({check_frames}/{max_check_frames})",
                                (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 200, 0), 2)

                    if other_match_count >= 5:
                        try:
                            winsound.Beep(600, 500)
                        except Exception:
                            pass
                        error_msg = (
                            f"DUPLICATE FACE REJECTED!\n\n"
                            f"This face is already registered in the system as:\n"
                            f"Name: {matched_other_name}\n"
                            f"Roll No: {matched_other_roll}\n\n"
                            f"A single face cannot be registered under multiple names or roll numbers!"
                        )
                        print(f"[SECURITY ALERT] {error_msg}")
                        return False, error_msg

                    if check_frames >= max_check_frames:
                        current_phase = "CAPTURE"
                    break

                # ----------------- PHASE 3: CAPTURING SAMPLES -----------------
                elif current_phase == "CAPTURE":
                    os.makedirs(student_dir, exist_ok=True)

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    if count < config.NUM_SAMPLES and (current_time - last_capture_time) >= capture_interval:
                        file_path = os.path.join(student_dir, f"sample_{count+1:02d}.jpg")
                        cv2.imwrite(file_path, face_equalized)

                        count += 1
                        last_capture_time = current_time

                        if on_progress:
                            on_progress(count, config.NUM_SAMPLES)

                    label = f"Capturing: {count}/{config.NUM_SAMPLES}"
                    cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    break

            # Top HUD Banner
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w_frame, 45), (20, 20, 20), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

            if current_phase == "VERIFY_OWNER":
                hud_text = f"Security Check: Verifying you are {student_name} ({roll_no})..."
            elif current_phase == "CHECK_UNIQUENESS":
                hud_text = f"Security Check: Verifying face is unique... Please look at camera"
            else:
                hud_text = f"Student: {student_name} | Age: {age_int} | Progress: {count}/{config.NUM_SAMPLES}"

            cv2.putText(frame, hud_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2)
            win_name = "Face Attendance System - Student Registration"
            cv2.imshow(win_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27 or (cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE) < 1):
                print("\n[INFO] Registration cancelled by user.")
                if os.path.exists(student_dir) and count < config.NUM_SAMPLES and not is_re_registering:
                    shutil.rmtree(student_dir, ignore_errors=True)
                return False, "Registration was cancelled by user."

            if count >= config.NUM_SAMPLES:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

    metadata = {
        "roll_no": roll_no,
        "name": student_name,
        "age": age_int
    }
    with open(os.path.join(student_dir, "info.json"), "w") as f:
        json.dump(metadata, f, indent=4)

    try:
        winsound.Beep(1200, 250)
    except Exception:
        pass

    msg = f"Successfully registered {student_name} (Roll: {roll_no} | Age: {age_int}) with {count} facial samples!"
    print(f"\n[SUCCESS] {msg}")
    print("[NEXT STEP] Please click 'Train Model' to update the recognition model.")
    return True, msg

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        name_input = sys.argv[1].strip()
        roll_input = sys.argv[2].strip()
        age_input = sys.argv[3].strip()
    else:
        print("=" * 60)
        print("      FACE RECOGNITION ATTENDANCE SYSTEM - REGISTRATION      ")
        print("=" * 60)
        name_input = input("Enter Student Full Name: ").strip()
        roll_input = input("Enter Student Roll Number / ID: ").strip()
        age_input = input(f"Enter Student Age ({config.MIN_STUDENT_AGE}-{config.MAX_STUDENT_AGE}): ").strip()

    success, message = capture_student(name_input, roll_input, age_input)
    if not success:
        print(f"\n[ERROR] {message}")
