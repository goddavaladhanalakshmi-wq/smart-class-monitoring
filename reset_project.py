import os
import sys
import shutil
import sqlite3
from datetime import datetime

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORKSPACE_DIR, "data")
STUDENTS_DIR = os.path.join(DATA_DIR, "students")
PHOTOS_DIR = os.path.join(DATA_DIR, "photos")
LOGS_DIR = os.path.join(WORKSPACE_DIR, "logs")
DB_PATH = os.path.join(DATA_DIR, "smart_classroom.db")
BACKUPS_DIR = os.path.join(WORKSPACE_DIR, "backups")

CSV_HEADER = (
    "ID,Student ID,Student Name,Date,Join Time,Check-In Time,"
    "Last Seen Time,Exit Time,Duration,Duration Seconds,Status,"
    "Attendance Status,Attentiveness Avg,Drowsiness Detected,Remarks\n"
)

PRESENCE_HEADER = "Timestamp,Student ID,Student Name,Status,Attention Score,Drowsy\n"

def backup_project_data():
    """Creates a timestamped backup of all current data before performing reset."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUPS_DIR, f"backup_{ts}")
    os.makedirs(backup_path, exist_ok=True)

    print(f"[*] Creating full data backup at: {backup_path}")

    # 1. Backup SQLite database
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, os.path.join(backup_path, "smart_classroom.db"))
        print("  -> Backed up smart_classroom.db")

    # 2. Backup data directory (students .npy, photos, etc.)
    if os.path.exists(DATA_DIR):
        dest_data = os.path.join(backup_path, "data")
        os.makedirs(dest_data, exist_ok=True)
        for item in os.listdir(DATA_DIR):
            src_item = os.path.join(DATA_DIR, item)
            if item.endswith(".db") or item.endswith(".db-journal"):
                continue
            if os.path.isdir(src_item):
                shutil.copytree(src_item, os.path.join(dest_data, item), dirs_exist_ok=True)
                print(f"  -> Backed up data/{item}/")

    # 3. Backup logs & root CSVs
    root_csv = os.path.join(WORKSPACE_DIR, "attendance.csv")
    if os.path.exists(root_csv):
        shutil.copy2(root_csv, os.path.join(backup_path, "attendance.csv"))
        print("  -> Backed up attendance.csv")

    if os.path.exists(LOGS_DIR):
        shutil.copytree(LOGS_DIR, os.path.join(backup_path, "logs"), dirs_exist_ok=True)
        print("  -> Backed up logs/")

    print("[*] Backup complete!\n")
    return backup_path

def reset_database():
    """Clears records while preserving table schema and admin user."""
    if not os.path.exists(DB_PATH):
        print("[!] No SQLite database found at data/smart_classroom.db. Nothing to clear.")
        return

    print("[*] Resetting database tables (preserving schema & admin account)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear attendance, sessions, and students tables
    cursor.execute("DELETE FROM attendance_records;")
    cursor.execute("DELETE FROM class_sessions;")
    cursor.execute("DELETE FROM students;")
    cursor.execute("DELETE FROM system_logs;")

    # Reset SQLite autoincrement sequences
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('attendance_records', 'class_sessions', 'students', 'system_logs');")
    except Exception:
        pass

    # Ensure admin user exists
    cursor.execute("SELECT COUNT(*) FROM admins;")
    admin_count = cursor.fetchone()[0]
    if admin_count == 0:
        from werkzeug.security import generate_password_hash
        pw = generate_password_hash("admin123")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO admins (username, password_hash, full_name, email, role, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", pw, "Administrator", "admin@smartclass.edu", "super_admin", now)
        )
        print("  -> Re-seeded default administrator (admin / admin123)")

    conn.commit()

    # Vacuum database to shrink file size
    cursor.execute("VACUUM;")
    conn.commit()
    conn.close()
    print("  -> Database tables cleared and vacuumed.")

def safe_remove_dir_or_contents(dir_path):
    """Safely removes directory or its contents handling Windows read-only flags."""
    import stat
    if not os.path.exists(dir_path):
        return
    for root, dirs, files in os.walk(dir_path, topdown=False):
        for f in files:
            fp = os.path.join(root, f)
            try:
                os.chmod(fp, stat.S_IWRITE)
                os.remove(fp)
            except Exception:
                pass
        for d in dirs:
            dp = os.path.join(root, d)
            try:
                os.chmod(dp, stat.S_IWRITE)
                os.rmdir(dp)
            except Exception:
                pass
    try:
        os.chmod(dir_path, stat.S_IWRITE)
        os.rmdir(dir_path)
    except Exception:
        pass

def reset_biometrics_and_files():
    """Removes all .npy files, old face photos, and resets CSV log files."""
    print("[*] Clearing active biometric .npy embeddings and student photos...")

    # Clear .npy embeddings in data/students
    if os.path.exists(STUDENTS_DIR):
        for f in os.listdir(STUDENTS_DIR):
            if f.endswith(".npy"):
                try:
                    os.remove(os.path.join(STUDENTS_DIR, f))
                    print(f"  -> Removed {f}")
                except Exception as e:
                    print(f"  -> Notice removing {f}: {e}")
    os.makedirs(STUDENTS_DIR, exist_ok=True)

    # Clear photo subdirectories in data/
    photo_folders = ["chaya", "esasai", "dhanalakshmi", "photos"]
    for pf in photo_folders:
        dir_path = os.path.join(DATA_DIR, pf)
        if os.path.exists(dir_path):
            safe_remove_dir_or_contents(dir_path)
            print(f"  -> Cleared data/{pf}/ folder")

    os.makedirs(PHOTOS_DIR, exist_ok=True)

    # Reset CSV logs to empty with proper headers
    os.makedirs(LOGS_DIR, exist_ok=True)

    root_csv = os.path.join(WORKSPACE_DIR, "attendance.csv")
    with open(root_csv, "w", encoding="utf-8") as f:
        f.write(CSV_HEADER)
    print("  -> Reset root attendance.csv")

    log_csv = os.path.join(LOGS_DIR, "attendance.csv")
    with open(log_csv, "w", encoding="utf-8") as f:
        f.write(CSV_HEADER)
    print("  -> Reset logs/attendance.csv")

    presence_csv = os.path.join(LOGS_DIR, "presence_log.csv")
    with open(presence_csv, "w", encoding="utf-8") as f:
        f.write(PRESENCE_HEADER)
    print("  -> Reset logs/presence_log.csv")

def verify_reset_state():
    """Prints verification of the clean system state."""
    print("\n" + "=" * 60)
    print("         SMART CLASSROOM - RESET VERIFICATION")
    print("=" * 60)

    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for t in ["students", "class_sessions", "attendance_records", "admins"]:
            c.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = c.fetchone()[0]
            print(f"  - Database Table [{t}]: {cnt} records")
        conn.close()

    npy_count = len([f for f in os.listdir(STUDENTS_DIR) if f.endswith(".npy")]) if os.path.exists(STUDENTS_DIR) else 0
    print(f"  - Registered Biometric Embeddings (.npy): {npy_count} files")
    print(f"  - Admin Login: Username 'admin' | Password 'admin123'")
    print("=" * 60)
    print("[SUCCESS] Project has been cleanly reset and is ready for live demonstration!\n")

def main():
    skip_confirm = "--yes" in sys.argv or "-y" in sys.argv

    print("=" * 60)
    print("    SMART CLASS MONITORING - SAFE DEMONSTRATION RESET")
    print("=" * 60)
    print("This will:")
    print("  1. Create a full backup in backups/backup_<timestamp>/")
    print("  2. Clear all student records and biometric .npy files")
    print("  3. Clear all old class sessions and attendance/timing records")
    print("  4. Reset CSV log files with fresh headers")
    print("  5. PRESERVE your admin account, source code, AI models, and schema")
    print("=" * 60)

    if not skip_confirm:
        resp = input("\nProceed with safe reset? (yes/no): ").strip().lower()
        if resp not in ["yes", "y"]:
            print("Reset aborted by user.")
            sys.exit(0)

    # Execute reset workflow
    backup_path = backup_project_data()
    reset_database()
    reset_biometrics_and_files()
    verify_reset_state()
    print(f"Notice: If you ever need to restore your old data, it is saved in:\n  {backup_path}\n")

if __name__ == "__main__":
    main()
