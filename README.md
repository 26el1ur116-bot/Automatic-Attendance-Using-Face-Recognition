# Automated Attendance Recording Using Face Recognition
> **Micro Project** | Semester 1 – Electronics Engineering

An automated, contactless attendance recording system built in Python using **OpenCV** and the **LBPH (Local Binary Patterns Histograms)** Face Recognizer. The system uses a laptop webcam to detect student faces in real-time, recognize them, and automatically log attendance into a daily CSV/Excel sheet with advanced anti-proxy, age restriction, and voice alert security.

---

## 📌 Features Overview

1. **Illumination Normalization & High Accuracy**:
   - Integrated **Histogram Equalization (`cv2.equalizeHist`)** across registration, training, and real-time attendance to eliminate lighting variations.
   - Strict Chi-Square distance thresholding (`CONFIDENCE_THRESHOLD = 48`) to prevent false positives and block strangers.
2. **Audio Voice Alert (Anti-Intrusion)**:
   - Built-in spoken voice alarm: **`"Warning! Person not recognized."`** plays automatically through laptop speakers whenever an unknown or unregistered face attempts to mark attendance.
3. **Student Age Verification (Anti-Proxy Protection)**:
   - Registration strictly verifies that student age is within the eligible college bracket (**16 to 25 years**).
   - Ineligible ages (<16 or >25) are immediately blocked from registration.
   - Verified age is embedded into the biometric profile and logged into the daily CSV sheet.
4. **Biometric Ownership & Identity Locking**:
   - Roll Number and Name are permanently bound to prevent identity hijacking.
   - Biometric ownership challenge verifies existing students before allowing photo updates.
   - Prevents duplicate registrations of the same face under different identities.
5. **Real-time Live Attendance**:
   - Simultaneous recognition of multiple faces in the same frame.
   - Stylized HUD with bounding box:
     - 🟩 **Green**: Recognized & Age Verified (`Name [Age: X] (88%)`)
     - 🟨 **Yellow/Cyan**: Already Marked Today
     - 🟥 **Red**: Unknown / Person Not Recognized (with Voice Warning)
6. **Smart Attendance Storage**:
   - Automatically creates daily records with columns: `Roll_Number, Name, Age, Date, Time, Status`.
   - Prevents duplicate entries so the same student is not logged multiple times in the same session.
   - Resilient against Microsoft Excel file-locking (`PermissionError` protected).
7. **Modern Desktop GUI**:
   - Built-in Dark Mode Dashboard (`app.py`) using Tkinter.
   - Real-time attendance log viewer with age display and 1-click open in Excel.
   - Student management window (`👥 Manage / Delete Students`) to view and delete student records.

---

## 🛠️ Project Directory Structure

```
c:\Users\singh\Downloads\Face\
│
├── data/
│   ├── dataset/             # Captured student face photos & info.json (Roll, Name, Age)
│   └── attendance/          # Daily CSV attendance logs (Excel compatible)
│
├── models/
│   ├── haarcascade_frontalface_default.xml  # Haar cascade face detector
│   ├── trainer.yml                          # Trained LBPH model weights
│   ├── labels.json                          # ID-to-student mapping with age profiles
│   └── person_not_recognized.wav            # Audio voice alert for unknown faces
│
├── config.py                # System settings (thresholds, age limits, sample count, paths)
├── register_student.py      # Module 1: Enrolls student with age validation & ownership check
├── train_model.py           # Module 2: Trains LBPH recognizer with histogram equalization
├── take_attendance.py       # Module 3: Real-time recognition, anti-proxy check & voice alert
├── app.py                   # Unified Desktop GUI Dashboard
│
├── RUN_APP.bat              # 1-Click launcher for GUI App
├── 1_REGISTER_STUDENT.bat   # 1-Click launcher for registration
├── 2_TRAIN_MODEL.bat        # 1-Click launcher for training
├── 3_START_ATTENDANCE.bat   # 1-Click launcher for attendance
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation & viva guide
```

---

## 🚀 How to Run

Double-click [**`RUN_APP.bat`**](file:///c:/Users/singh/Downloads/Face/RUN_APP.bat) (or run `py app.py` in your terminal).
1. Click **`1. Register Student`** ➔ Enter Name, Roll Number, and Age (16–25) ➔ Face camera for 40 samples.
2. Click **`2. Train Model`** ➔ Takes 1 second.
3. Click **`3. Start Attendance`** ➔ Stand in front of camera to mark attendance!
4. Click **`4. Open Excel / CSV`** ➔ View attendance records in Microsoft Excel.

*(Camera window can be closed by pressing `q`, `ESC`, or clicking the top-right `X` button).*
