"""
Face Recognition Attendance System - Desktop Application (GUI)
A unified GUI interface for registering students, training models,
marking attendance, viewing attendance records, and managing registered students.
Features Student Age Verification (16 - 25 years).
"""

import os
import sys
import shutil
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import pandas as pd

import config
from register_student import capture_student
from train_model import train_model
from take_attendance import start_attendance_system, get_today_csv_path, ensure_attendance_file

class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Attendance System - Face Recognition (Age Verified)")
        self.root.geometry("880x660")
        self.root.minsize(800, 600)
        self.root.configure(bg="#1E1E2E")

        self.setup_styles()
        self.create_widgets()
        self.refresh_stats()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background="#1E1E2E", foreground="#CDD6F4", font=("Segoe UI", 10))
        style.configure("TLabel", background="#1E1E2E", foreground="#CDD6F4", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#89B4FA")
        style.configure("SubHeader.TLabel", font=("Segoe UI", 10), foreground="#A6ADC8")
        style.configure("Card.TFrame", background="#26283D", relief="flat")
        style.configure("Stat.TLabel", font=("Segoe UI", 12, "bold"), foreground="#A6E3A1", background="#26283D")

        style.configure("Treeview",
                        background="#181825",
                        foreground="#CDD6F4",
                        fieldbackground="#181825",
                        rowheight=26,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background="#313244",
                        foreground="#89B4FA",
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#45475A")])

    def create_widgets(self):
        # 1. Title Header
        header_frame = tk.Frame(self.root, bg="#1E1E2E")
        header_frame.pack(fill="x", padx=25, pady=(15, 10))

        title = ttk.Label(header_frame, text="Smart Attendance System", style="Header.TLabel")
        title.pack(anchor="w")

        subtitle = ttk.Label(header_frame,
                             text=f"Anti-Proxy Face Recognition | Eligible Age: {config.MIN_STUDENT_AGE}–{config.MAX_STUDENT_AGE} Years | ECE Micro Project",
                             style="SubHeader.TLabel")
        subtitle.pack(anchor="w")

        # 2. Stats Bar
        stats_frame = tk.Frame(self.root, bg="#26283D", bd=0, highlightthickness=1, highlightbackground="#313244")
        stats_frame.pack(fill="x", padx=25, pady=8)

        self.lbl_registered = tk.Label(stats_frame, text="Registered Students: 0",
                                       font=("Segoe UI", 10, "bold"), bg="#26283D", fg="#89B4FA")
        self.lbl_registered.pack(side="left", padx=20, pady=10)

        self.lbl_model_status = tk.Label(stats_frame, text="Model: Not Trained",
                                         font=("Segoe UI", 10, "bold"), bg="#26283D", fg="#F38BA8")
        self.lbl_model_status.pack(side="left", padx=20, pady=10)

        self.lbl_marked_today = tk.Label(stats_frame, text="Marked Today: 0",
                                         font=("Segoe UI", 10, "bold"), bg="#26283D", fg="#A6E3A1")
        self.lbl_marked_today.pack(side="right", padx=20, pady=10)

        # 3. Main Content Split
        main_frame = tk.Frame(self.root, bg="#1E1E2E")
        main_frame.pack(fill="both", expand=True, padx=25, pady=10)

        # Left Column - Buttons
        left_col = tk.Frame(main_frame, bg="#1E1E2E", width=260)
        left_col.pack(side="left", fill="y", padx=(0, 15))

        btn_style = {
            "font": ("Segoe UI", 10, "bold"),
            "bd": 0,
            "cursor": "hand2",
            "activeforeground": "#FFFFFF",
            "height": 2,
            "width": 24
        }

        btn_register = tk.Button(left_col, text="1. Register Student", bg="#89B4FA", fg="#11111B",
                                 activebackground="#74C7EC", command=self.on_register_clicked, **btn_style)
        btn_register.pack(pady=5, fill="x")

        btn_train = tk.Button(left_col, text="2. Train Model", bg="#CBA6F7", fg="#11111B",
                              activebackground="#B4BEFE", command=self.on_train_clicked, **btn_style)
        btn_train.pack(pady=5, fill="x")

        btn_attendance = tk.Button(left_col, text="3. Start Attendance", bg="#A6E3A1", fg="#11111B",
                                   activebackground="#94E2D5", command=self.on_attendance_clicked, **btn_style)
        btn_attendance.pack(pady=5, fill="x")

        btn_manage = tk.Button(left_col, text="👥 Manage / Delete Students", bg="#F9E2AF", fg="#11111B",
                               activebackground="#F38BA8", command=self.on_manage_students_clicked, **btn_style)
        btn_manage.pack(pady=5, fill="x")

        btn_open_csv = tk.Button(left_col, text="📊 Open Excel / CSV", bg="#FAB387", fg="#11111B",
                                 activebackground="#F9E2AF", command=self.on_open_csv_clicked, **btn_style)
        btn_open_csv.pack(pady=5, fill="x")

        btn_refresh = tk.Button(left_col, text="🔄 Refresh Table", bg="#45475A", fg="#CDD6F4",
                                activebackground="#585B70", command=self.refresh_stats, **btn_style)
        btn_refresh.pack(pady=5, fill="x")

        btn_git = tk.Button(left_col, text="🚀 Commit & Update GitHub", bg="#B4BEFE", fg="#11111B",
                            activebackground="#CBA6F7", command=self.on_commit_and_update_clicked, **btn_style)
        btn_git.pack(pady=5, fill="x")

        # Right Column - Table of Today's Attendance
        right_col = tk.Frame(main_frame, bg="#181825")
        right_col.pack(side="right", fill="both", expand=True)

        table_header = tk.Label(right_col, text="Today's Attendance Log (With Verified Age)", font=("Segoe UI", 11, "bold"),
                                bg="#181825", fg="#89B4FA")
        table_header.pack(anchor="w", padx=10, pady=(8, 4))

        # Include Age column in Treeview
        columns = ("Roll_Number", "Name", "Age", "Time", "Status")
        self.tree = ttk.Treeview(right_col, columns=columns, show="headings", height=12)
        self.tree.heading("Roll_Number", text="Roll No")
        self.tree.heading("Name", text="Student Name")
        self.tree.heading("Age", text="Age")
        self.tree.heading("Time", text="Time")
        self.tree.heading("Status", text="Status")

        self.tree.column("Roll_Number", width=85, anchor="center")
        self.tree.column("Name", width=170, anchor="w")
        self.tree.column("Age", width=55, anchor="center")
        self.tree.column("Time", width=85, anchor="center")
        self.tree.column("Status", width=75, anchor="center")

        scrollbar = ttk.Scrollbar(right_col, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

        # 4. Status Bar
        self.status_bar = tk.Label(self.root, text="System Ready", font=("Segoe UI", 9),
                                   bg="#11111B", fg="#A6ADC8", anchor="w", padx=15, pady=4)
        self.status_bar.pack(side="bottom", fill="x")

    def update_status(self, text, color="#A6ADC8"):
        self.status_bar.config(text=text, fg=color)
        self.root.update_idletasks()

    def refresh_stats(self):
        if os.path.exists(config.DATASET_DIR):
            students = [f for f in os.listdir(config.DATASET_DIR) if os.path.isdir(os.path.join(config.DATASET_DIR, f))]
            num_students = len(students)
        else:
            num_students = 0
        self.lbl_registered.config(text=f"Registered Students: {num_students}")

        if os.path.exists(config.TRAINER_PATH) and os.path.exists(config.LABELS_PATH) and num_students > 0:
            self.lbl_model_status.config(text="Model: Ready", fg="#A6E3A1")
        else:
            self.lbl_model_status.config(text="Model: Not Trained", fg="#F38BA8")

        csv_path = ensure_attendance_file()
        for item in self.tree.get_children():
            self.tree.delete(item)

        count_marked = 0
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                for _, row in df.iterrows():
                    self.tree.insert("", "end", values=(
                        str(row.get("Roll_Number", "")),
                        str(row.get("Name", "")),
                        str(row.get("Age", "-")),
                        str(row.get("Time", "")),
                        str(row.get("Status", "Present"))
                    ))
                    count_marked += 1
            except Exception as e:
                print(f"Error reading CSV: {e}")

        self.lbl_marked_today.config(text=f"Marked Today: {count_marked}")

    def on_register_clicked(self):
        name = simpledialog.askstring("Register Student", "Enter Student Full Name:", parent=self.root)
        if not name:
            return

        roll = simpledialog.askstring("Register Student", "Enter Student Roll Number / ID:", parent=self.root)
        if not roll:
            return

        age = simpledialog.askstring("Register Student",
                                    f"Enter Student Age ({config.MIN_STUDENT_AGE} to {config.MAX_STUDENT_AGE}):",
                                    initialvalue="19", parent=self.root)
        if not age:
            return

        try:
            age_val = int(age.strip())
            if age_val < config.MIN_STUDENT_AGE or age_val > config.MAX_STUDENT_AGE:
                messagebox.showerror(
                    "Age Restriction Error",
                    f"Student Age must be between {config.MIN_STUDENT_AGE} and {config.MAX_STUDENT_AGE} years.\n\n"
                    f"Entered: {age_val}\n"
                    "Proxy or ineligible age registration is blocked.",
                    parent=self.root
                )
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Age must be a valid number.", parent=self.root)
            return

        self.update_status(f"Starting camera for {name} (Age: {age})... Please face the camera.", "#89B4FA")
        messagebox.showinfo("Instructions",
                            f"Camera will now open to capture face samples for {name} (Age: {age}).\n\n"
                            "1. Look directly at camera\n"
                            "2. Move head slightly (tilt, smile, left, right)\n"
                            f"3. System will capture {config.NUM_SAMPLES} face samples.\n"
                            "4. Press 'q' or 'ESC' on the camera window if you need to cancel.")

        def run_capture():
            success, msg = capture_student(name, roll, age)
            if success:
                self.root.after(0, lambda: messagebox.showinfo("Success", msg + "\n\nRemember to click 'Train Model' next!"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Registration Blocked", msg))
            self.root.after(0, self.refresh_stats)
            self.root.after(0, lambda: self.update_status("System Ready"))

        threading.Thread(target=run_capture, daemon=True).start()

    def on_train_clicked(self):
        self.update_status("Training Face Recognition model, please wait...", "#CBA6F7")

        def run_train():
            success, msg = train_model()
            if success:
                self.root.after(0, lambda: messagebox.showinfo("Training Complete", msg))
            else:
                self.root.after(0, lambda: messagebox.showerror("Training Error", msg))
            self.root.after(0, self.refresh_stats)
            self.root.after(0, lambda: self.update_status("System Ready"))

        threading.Thread(target=run_train, daemon=True).start()

    def on_attendance_clicked(self):
        if not os.path.exists(config.TRAINER_PATH):
            messagebox.showwarning("Model Required", "Please register a student and click 'Train Model' before starting attendance.")
            return

        self.update_status("Attendance camera running... Press 'q' on camera window to stop.", "#A6E3A1")

        def run_att():
            success, msg = start_attendance_system()
            self.root.after(0, self.refresh_stats)
            self.root.after(0, lambda: self.update_status("System Ready"))
            if success:
                self.root.after(0, lambda: messagebox.showinfo("Session Finished", msg))

        threading.Thread(target=run_att, daemon=True).start()

    def on_manage_students_clicked(self):
        """Window to view registered students with their age and delete duplicates."""
        manage_win = tk.Toplevel(self.root)
        manage_win.title("Manage Registered Students (Age Verified)")
        manage_win.geometry("560x430")
        manage_win.configure(bg="#1E1E2E")
        manage_win.transient(self.root)
        manage_win.grab_set()

        lbl = tk.Label(manage_win, text="Registered Students Database", font=("Segoe UI", 12, "bold"),
                       bg="#1E1E2E", fg="#89B4FA")
        lbl.pack(pady=10)

        info = tk.Label(manage_win, text=f"All students must be within eligible age bracket: {config.MIN_STUDENT_AGE}–{config.MAX_STUDENT_AGE} years.",
                        font=("Segoe UI", 9), bg="#1E1E2E", fg="#A6ADC8", justify="center")
        info.pack(pady=(0, 10))

        list_frame = tk.Frame(manage_win, bg="#181825")
        list_frame.pack(fill="both", expand=True, padx=20, pady=5)

        cols = ("Roll", "Name", "Age", "Samples")
        tree_st = ttk.Treeview(list_frame, columns=cols, show="headings", height=8)
        tree_st.heading("Roll", text="Roll No")
        tree_st.heading("Name", text="Student Name")
        tree_st.heading("Age", text="Age")
        tree_st.heading("Samples", text="Images")
        tree_st.column("Roll", width=85, anchor="center")
        tree_st.column("Name", width=200, anchor="w")
        tree_st.column("Age", width=60, anchor="center")
        tree_st.column("Samples", width=70, anchor="center")
        tree_st.pack(side="left", fill="both", expand=True)

        sc = ttk.Scrollbar(list_frame, orient="vertical", command=tree_st.yview)
        tree_st.configure(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")

        def populate_students():
            for it in tree_st.get_children():
                tree_st.delete(it)
            if os.path.exists(config.DATASET_DIR):
                for folder in sorted(os.listdir(config.DATASET_DIR)):
                    fp = os.path.join(config.DATASET_DIR, folder)
                    if os.path.isdir(fp):
                        parts = folder.split("_", 1)
                        roll = parts[0]
                        name = parts[1].replace("_", " ") if len(parts) > 1 else folder
                        age_disp = "19"

                        info_path = os.path.join(fp, "info.json")
                        if os.path.exists(info_path):
                            try:
                                import json
                                with open(info_path, "r") as ifile:
                                    idata = json.load(ifile)
                                    age_disp = str(idata.get("age", 19))
                            except Exception:
                                pass

                        img_count = len([f for f in os.listdir(fp) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
                        tree_st.insert("", "end", iid=folder, values=(roll, name, f"{age_disp} yrs", f"{img_count} imgs"))

        populate_students()

        def delete_selected():
            selected = tree_st.selection()
            if not selected:
                messagebox.showinfo("Select Student", "Please select a student from the list first.", parent=manage_win)
                return

            folder_to_delete = selected[0]
            confirm = messagebox.askyesno("Confirm Deletion",
                                          f"Are you sure you want to delete student:\n'{folder_to_delete}'?\n\nThis will remove their face images.",
                                          parent=manage_win)
            if confirm:
                fp = os.path.join(config.DATASET_DIR, folder_to_delete)
                shutil.rmtree(fp, ignore_errors=True)
                messagebox.showinfo("Deleted", f"Deleted student: {folder_to_delete}.\nPlease click 'Train Model' to update recognition!", parent=manage_win)
                populate_students()
                self.refresh_stats()

        btn_box = tk.Frame(manage_win, bg="#1E1E2E")
        btn_box.pack(fill="x", padx=20, pady=12)

        btn_del = tk.Button(btn_box, text="🗑️ Delete Selected Student", bg="#F38BA8", fg="#11111B",
                            font=("Segoe UI", 10, "bold"), bd=0, height=2, cursor="hand2", command=delete_selected)
        btn_del.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_close = tk.Button(btn_box, text="Close", bg="#45475A", fg="#CDD6F4",
                              font=("Segoe UI", 10), bd=0, height=2, cursor="hand2", command=manage_win.destroy)
        btn_close.pack(side="right", padx=(5, 0))

    def on_open_csv_clicked(self):
        csv_path = get_today_csv_path()
        ensure_attendance_file()
        if os.path.exists(csv_path):
            os.startfile(csv_path)
            self.update_status(f"Opened {os.path.basename(csv_path)}", "#A6E3A1")
        else:
            messagebox.showinfo("Not Found", "No attendance file created yet.")

    def on_commit_and_update_clicked(self):
        bat_path = os.path.join(config.BASE_DIR, "COMMIT_AND_UPDATE.bat")
        if os.path.exists(bat_path):
            os.startfile(bat_path)
            self.update_status("Launched Git Commit & Update console...", "#B4BEFE")
        else:
            messagebox.showerror("Not Found", "COMMIT_AND_UPDATE.bat not found in project folder.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceApp(root)
    root.mainloop()
