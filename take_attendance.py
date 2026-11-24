"""
Module: Real-Time Attendance Recording
Captures webcam stream, recognizes faces, and writes attendance to a CSV file.
Features:
- Histogram Equalization & Calibrated Distance Threshold (57) for reliable recognition.
- Voice Audio Warning ("Warning! Person not recognized.") on confirmed unknown faces.
- Real-time live distance metrics displayed on HUD for transparency.
- Simultaneous multi-face recognition.
- Resilient against Excel file-locking (PermissionError protection).
- Consecutive frame verification & duplicate prevention.
"""

import os
import cv2
import json
import time
from datetime import datetime
import pandas as pd
import winsound
import config

def get_today_csv_path():
    """Returns the CSV file path for today's date."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(config.ATTENDANCE_DIR, f"attendance_{today_str}.csv")

def ensure_attendance_file():
    """Creates today's CSV file with headers if it doesn't already exist."""
    csv_path = get_today_csv_path()
    if not os.path.exists(csv_path):
        df = pd.DataFrame(columns=["Roll_Number", "Name", "Age", "Date", "Time", "Status"])
        try:
            df.to_csv(csv_path, index=False)
        except Exception:
            pass
    return csv_path

def get_already_marked_roll_numbers():
    """Reads today's CSV and returns set of roll numbers already marked."""
    csv_path = get_today_csv_path()
    if not os.path.exists(csv_path):
        return set()
    try:
        df = pd.read_csv(csv_path)
        if "Roll_Number" in df.columns:
            return set(df["Roll_Number"].astype(str).str.strip().tolist())
    except Exception:
        pass
    return set()

def record_attendance(roll_no: str, name: str, age: int):
    """
    Appends a new attendance record if not already recorded today.
    Catches PermissionError if the CSV is currently open in Microsoft Excel.
    """
    csv_path = ensure_attendance_file()
    marked_rolls = get_already_marked_roll_numbers()

    roll_no = str(roll_no).strip()
    if roll_no in marked_rolls:
        return False, f"{name} ({roll_no}) is already marked Present today."

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    new_row = pd.DataFrame([{
        "Roll_Number": roll_no,
        "Name": name,
        "Age": age,
        "Date": date_str,
        "Time": time_str,
        "Status": "Present"
    }])

    try:
        new_row.to_csv(csv_path, mode="a", header=False, index=False)
    except PermissionError:
        print(f"[WARN] Could not write to {csv_path} because the file is open in Excel!")
        return False, f"Please close Excel! File is locked."
    except Exception as e:
        print(f"[ERROR] Could not save record: {e}")
        return False, "Error writing to attendance file."

    try:
        winsound.Beep(1500, 250)
    except Exception:
        pass

    return True, f"Attendance Marked: {name} (Roll: {roll_no} | Age: {age}) at {time_str}"

def start_attendance_system():
    """
    Launches the live video recognition and attendance loop.
    Rejects other faces with audio voice warning and alarm.
    """
    if not os.path.exists(config.TRAINER_PATH) or not os.path.exists(config.LABELS_PATH):
        print("\n[ERROR] Model or labels not found!")
        print("Please register a student and click 'Train Model' first.")
        return False, "Model not trained yet."

    if not os.path.exists(config.CASCADE_PATH):
        return False, f"Cascade file missing at {config.CASCADE_PATH}"

    with open(config.LABELS_PATH, "r") as f:
        labels_raw = json.load(f)
        label_map = {int(k): v for k, v in labels_raw.items()}

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(config.TRAINER_PATH)
    face_cascade = cv2.CascadeClassifier(config.CASCADE_PATH)

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        return False, "Could not open webcam."

    ensure_attendance_file()
    marked_today = get_already_marked_roll_numbers()

    banner_text = f"System Ready - Stand in front of camera"
    banner_color = (180, 180, 180)
    banner_expire_time = time.time() + 3.0

    student_streaks = {}
    recent_marks = {}

    unknown_streak = 0
    last_unknown_alert_time = 0

    print("\n" + "=" * 60)
    print("      AUTOMATED FACE RECOGNITION ATTENDANCE IS RUNNING      ")
    print(f"      CALIBRATED MATCH THRESHOLD: Distance < {config.CONFIDENCE_THRESHOLD}       ")
    print("=" * 60)
    print("[INFO] Press 'q', 'ESC', or click 'X' to Stop.")
    print(f"[INFO] Current attendance file: {get_today_csv_path()}\n")

    win_title = "Face Recognition Attendance System"

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h_frame, w_frame, _ = frame.shape
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.15,
            minNeighbors=5,
            minSize=(80, 80)
        )

        current_time = time.time()
        detected_in_frame = set()
        has_unknown_in_frame = False

        for (x, y, w, h) in faces:
            face_crop = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_crop, (config.FACE_WIDTH, config.FACE_HEIGHT))
            face_equalized = cv2.equalizeHist(face_resized)

            label_id, confidence = recognizer.predict(face_equalized)

            # Match % based on LBPH distance:
            match_percentage = max(0, min(100, int((1.0 - (confidence / 70.0)) * 100)))

            # Strict threshold check
            is_match = (confidence < config.CONFIDENCE_THRESHOLD) and (label_id in label_map)

            if is_match:
                student = label_map[label_id]
                roll_no = str(student["roll_no"])
                name = student["name"]
                age = student.get("age", 19)
                detected_in_frame.add(label_id)

                student_streaks[label_id] = student_streaks.get(label_id, 0) + 1

                if roll_no in marked_today:
                    box_color = (255, 190, 0)  # Yellow/Cyan
                    status_display = f"{name} (Marked) [Dist: {int(confidence)}]"
                else:
                    last_marked_time = recent_marks.get(roll_no, 0)
                    if (current_time - last_marked_time) < config.SESSION_LOCK_SECONDS:
                        box_color = (0, 255, 0)
                        status_display = f"{name} (Marked) [Dist: {int(confidence)}]"
                    elif student_streaks[label_id] >= config.CONSECUTIVE_FRAMES_REQUIRED:
                        is_new, msg = record_attendance(roll_no, name, age)
                        if is_new:
                            marked_today.add(roll_no)
                            recent_marks[roll_no] = current_time
                            banner_text = f"SUCCESS: {name} (Roll {roll_no} | Age {age}) Marked Present!"
                            banner_color = (0, 255, 0)
                            banner_expire_time = current_time + 4.0
                            print(f"[LOG] {msg}")
                        elif "close Excel" in msg:
                            banner_text = "WARNING: Close Excel file to record attendance!"
                            banner_color = (0, 140, 255)
                            banner_expire_time = current_time + 4.0

                        box_color = (0, 255, 0)
                        status_display = f"{name} [Age: {age}] ({match_percentage}%) [Dist: {int(confidence)}]"
                    else:
                        box_color = (255, 255, 0)
                        status_display = f"Detecting: {name} ({student_streaks[label_id]}/{config.CONSECUTIVE_FRAMES_REQUIRED})"
            else:
                has_unknown_in_frame = True
                box_color = (0, 0, 255)  # Bright Red
                status_display = f"Unknown / Not Recognized [Dist: {int(confidence)}]"

            # Draw bounding box and label tag
            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
            cv2.rectangle(frame, (x, y - 28), (x + w, y), box_color, -1)
            cv2.putText(frame, status_display, (x + 6, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 0) if is_match else (255, 255, 255), 2)

        # ----------------- UNKNOWN PERSON VOICE & ALARM SOUND -----------------
        if has_unknown_in_frame:
            unknown_streak += 1
            # Require at least UNKNOWN_STREAK_REQUIRED frames (~0.8s) so momentary entries don't trigger false alarms
            if unknown_streak >= config.UNKNOWN_STREAK_REQUIRED:
                if (current_time - last_unknown_alert_time) >= config.UNKNOWN_ALERT_COOLDOWN:
                    last_unknown_alert_time = current_time
                    banner_text = "ALERT: Person Not Recognized! Access Denied!"
                    banner_color = (0, 0, 255)
                    banner_expire_time = current_time + 3.5
                    print(f"[SECURITY ALERT] Confirmed unknown face detected! Playing voice alert: 'Person not recognized.'")

                    if os.path.exists(config.ALERT_AUDIO_PATH):
                        try:
                            winsound.PlaySound(config.ALERT_AUDIO_PATH, winsound.SND_FILENAME | winsound.SND_ASYNC)
                        except Exception as e:
                            print(f"[AUDIO ERROR] {e}")
                    else:
                        try:
                            winsound.Beep(900, 300)
                        except Exception:
                            pass
        else:
            unknown_streak = 0

        # Reset streak for any student not visible in this frame
        for s_id in list(student_streaks.keys()):
            if s_id not in detected_in_frame:
                student_streaks[s_id] = 0

        # Top Bar
        cv2.rectangle(frame, (0, 0), (w_frame, 50), (25, 25, 25), -1)
        now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        title_text = f"ATTENDANCE SYSTEM  |  {now_str}  |  Total Marked Today: {len(marked_today)}"
        cv2.putText(frame, title_text, (15, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        # Bottom Bar
        if current_time < banner_expire_time:
            cv2.rectangle(frame, (0, h_frame - 45), (w_frame, h_frame), (30, 30, 30), -1)
            cv2.putText(frame, banner_text, (20, h_frame - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.62, banner_color, 2)
        else:
            cv2.rectangle(frame, (0, h_frame - 30), (w_frame, h_frame), (20, 20, 20), -1)
            cv2.putText(frame, f"Align face in camera | Match Threshold: Dist < {config.CONFIDENCE_THRESHOLD} | Press 'q', 'ESC', or 'X' to Exit",
                        (20, h_frame - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1)

        cv2.imshow(win_title, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27 or (cv2.getWindowProperty(win_title, cv2.WND_PROP_VISIBLE) < 1):
            print("\n[INFO] Attendance session stopped by user.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return True, f"Attendance session completed. Total students marked today: {len(marked_today)}"

if __name__ == "__main__":
    start_attendance_system()
