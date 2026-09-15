import csv
import os
from datetime import datetime


LOG_FILE = os.path.join("logs", "attendance.csv")


def create_log_file():
    os.makedirs("logs", exist_ok=True)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as file:
            writer = csv.writer(file)

            writer.writerow([
                "Date",
                "Time",
                "Faces Detected",
                "Status"
            ])


def record_attendance(face_count):

    create_log_file()

    now = datetime.now()

    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    if face_count > 0:
        status = "Present"
    else:
        status = "No Student Detected"

    with open(LOG_FILE, "a", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            date,
            time,
            face_count,
            status
        ])


if __name__ == "__main__":

    create_log_file()

    print("Attendance system ready.")
    print("Log file:", LOG_FILE)