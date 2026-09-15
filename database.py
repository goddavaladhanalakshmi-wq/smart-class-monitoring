import os
import time
import sqlite3
import pymysql
from pymysql.constants import CLIENT
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import load_config, save_config

class DatabaseManager:
    def __init__(self):
        self.config = load_config()
        self.active_db = self.config.get("DB_TYPE", "mysql")
        self.mysql_error = None
        self._init_db()

    def _get_mysql_conn(self, create_db_if_missing=True):
        m_cfg = self.config.get("MYSQL", {})
        host = m_cfg.get("host", "localhost")
        port = int(m_cfg.get("port", 3306))
        user = m_cfg.get("user", "root")
        password = m_cfg.get("password", "")
        database = m_cfg.get("database", "smart_class_db")

        if create_db_if_missing:
            # First connect without database to create it if it doesn't exist
            temp_conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                charset='utf8mb4',
                connect_timeout=3
            )
            try:
                with temp_conn.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                temp_conn.commit()
            finally:
                temp_conn.close()

        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=3,
            autocommit=True
        )
        return conn

    def _get_sqlite_conn(self):
        db_path = self.config.get("SQLITE_PATH", "data/smart_classroom.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def get_connection(self):
        pref_type = self.config.get("DB_TYPE", "mysql")
        if pref_type == "mysql":
            now_t = time.time()
            if self.mysql_error and (now_t - getattr(self, "_last_mysql_fail_time", 0) < 10):
                self.active_db = "sqlite"
                return self._get_sqlite_conn()

            try:
                conn = self._get_mysql_conn()
                self.active_db = "mysql"
                self.mysql_error = None
                return conn
            except Exception as e:
                self.mysql_error = str(e)
                self._last_mysql_fail_time = now_t
                self.active_db = "sqlite"
                return self._get_sqlite_conn()
        else:
            self.active_db = "sqlite"
            return self._get_sqlite_conn()

    def _init_db(self):
        """Creates tables in current active database and seeds default admin & existing students."""
        try:
            conn = self.get_connection()
            is_mysql = (self.active_db == "mysql")
            
            auto_inc = "AUTO_INCREMENT" if is_mysql else "AUTOINCREMENT"
            primary_key_id = f"id INTEGER PRIMARY KEY {auto_inc}" if not is_mysql else f"id INT AUTO_INCREMENT PRIMARY KEY"
            text_type = "TEXT" if not is_mysql else "VARCHAR(255)"

            queries = [
                # Admins table
                f"""CREATE TABLE IF NOT EXISTS admins (
                    {primary_key_id},
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100),
                    email VARCHAR(100),
                    role VARCHAR(20) DEFAULT 'admin',
                    created_at VARCHAR(30),
                    last_login VARCHAR(30)
                );""",
                # Online Class Sessions table
                f"""CREATE TABLE IF NOT EXISTS class_sessions (
                    {primary_key_id},
                    session_code VARCHAR(50) UNIQUE NOT NULL,
                    title VARCHAR(150) NOT NULL,
                    admin_id INT DEFAULT 1,
                    start_time VARCHAR(30) NOT NULL,
                    end_time VARCHAR(30),
                    duration_minutes INT DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'ACTIVE',
                    created_at VARCHAR(30)
                );""",
                # Students table
                f"""CREATE TABLE IF NOT EXISTS students (
                    {primary_key_id},
                    student_id VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    department VARCHAR(100),
                    email VARCHAR(100),
                    embedding_file VARCHAR(255),
                    photo_path VARCHAR(255),
                    is_active INT DEFAULT 1,
                    created_at VARCHAR(30)
                );""",
                # Attendance records table
                f"""CREATE TABLE IF NOT EXISTS attendance_records (
                    {primary_key_id},
                    session_id INT DEFAULT NULL,
                    student_id VARCHAR(50) NOT NULL,
                    student_name VARCHAR(100) NOT NULL,
                    log_date VARCHAR(20) NOT NULL,
                    join_time VARCHAR(20),
                    check_in_time VARCHAR(20) NOT NULL,
                    last_seen_time VARCHAR(20) NOT NULL,
                    exit_time VARCHAR(20),
                    duration_seconds INT DEFAULT 0,
                    status VARCHAR(50) DEFAULT 'Present',
                    attendance_status VARCHAR(50) DEFAULT 'Present',
                    attentiveness_avg FLOAT DEFAULT 100.0,
                    drowsiness_detected INT DEFAULT 0,
                    remarks VARCHAR(255),
                    created_at VARCHAR(30),
                    updated_at VARCHAR(30)
                );""",
                # System logs table
                f"""CREATE TABLE IF NOT EXISTS system_logs (
                    {primary_key_id},
                    event_type VARCHAR(50),
                    message {text_type},
                    timestamp VARCHAR(30)
                );"""
            ]

            cursor = conn.cursor()
            for q in queries:
                cursor.execute(q)

            # Auto-migration: Ensure new columns exist in attendance_records if table was created previously
            try:
                if not is_mysql:
                    cursor.execute("PRAGMA table_info(attendance_records);")
                    existing_cols = [r[1] for r in cursor.fetchall()]
                    col_defs = {
                        "session_id": "INTEGER DEFAULT NULL",
                        "join_time": "VARCHAR(20)",
                        "exit_time": "VARCHAR(20)",
                        "attendance_status": "VARCHAR(50) DEFAULT 'Present'"
                    }
                    for c_name, c_type in col_defs.items():
                        if c_name not in existing_cols:
                            cursor.execute(f"ALTER TABLE attendance_records ADD COLUMN {c_name} {c_type};")
                    # Backfill join_time & attendance_status if empty
                    cursor.execute("UPDATE attendance_records SET join_time = check_in_time WHERE join_time IS NULL OR join_time = '';")
                    cursor.execute("UPDATE attendance_records SET attendance_status = status WHERE attendance_status IS NULL OR attendance_status = '';")
                else:
                    db_name = self.config.get("MYSQL", {}).get("database", "smart_class_db")
                    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'attendance_records'", (db_name,))
                    existing_cols = [r["COLUMN_NAME"] if isinstance(r, dict) else r[0] for r in cursor.fetchall()]
                    col_defs = {
                        "session_id": "INT DEFAULT NULL",
                        "join_time": "VARCHAR(20)",
                        "exit_time": "VARCHAR(20)",
                        "attendance_status": "VARCHAR(50) DEFAULT 'Present'"
                    }
                    for c_name, c_type in col_defs.items():
                        if c_name not in existing_cols:
                            cursor.execute(f"ALTER TABLE attendance_records ADD COLUMN {c_name} {c_type};")
                    cursor.execute("UPDATE attendance_records SET join_time = check_in_time WHERE join_time IS NULL OR join_time = '';")
                    cursor.execute("UPDATE attendance_records SET attendance_status = status WHERE attendance_status IS NULL OR attendance_status = '';")
            except Exception as mig_err:
                print(f"[DB MIGRATION WARNING] {mig_err}")

            # Safely migrate and preserve existing student, session, and attendance data from SQLite to MySQL
            if is_mysql:
                self._migrate_data_from_sqlite(conn)

            # Seed default admin if not exists
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            check_admin_q = "SELECT id FROM admins WHERE username = %s" if is_mysql else "SELECT id FROM admins WHERE username = ?"
            cursor.execute(check_admin_q, ("admin",))
            admin_row = cursor.fetchone()
            
            if not admin_row:
                pw_hash = generate_password_hash("admin123")
                insert_admin_q = """
                    INSERT INTO admins (username, password_hash, full_name, email, role, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """ if is_mysql else """
                    INSERT INTO admins (username, password_hash, full_name, email, role, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_admin_q, ("admin", pw_hash, "Administrator", "admin@smartclass.edu", "super_admin", now_str))

            # Auto-seed existing .npy students in data/students if not in database
            student_dir = self.config.get("STUDENT_DATA_DIR", "data/students")
            if os.path.exists(student_dir):
                for fname in os.listdir(student_dir):
                    if fname.endswith(".npy"):
                        s_name = os.path.splitext(fname)[0]
                        check_s_q = "SELECT id FROM students WHERE name = %s" if is_mysql else "SELECT id FROM students WHERE name = ?"
                        cursor.execute(check_s_q, (s_name,))
                        if not cursor.fetchone():
                            s_id = f"STU-{s_name.upper()[:4]}-{abs(hash(s_name)) % 1000:03d}"
                            ins_s_q = """
                                INSERT INTO students (student_id, name, department, email, embedding_file, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """ if is_mysql else """
                                INSERT INTO students (student_id, name, department, email, embedding_file, created_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """
                            cursor.execute(ins_s_q, (s_id, s_name, "Computer Science", f"{s_name.lower()}@smartclass.edu", fname, now_str))

            if not is_mysql:
                conn.commit()
            conn.close()
            print(f"[DB] Initialized successfully. Active Backend: {self.active_db.upper()}")
        except Exception as e:
            print(f"[DB ERROR] Failed to initialize database: {e}")

    def _migrate_data_from_sqlite(self, mysql_conn):
        """Safely migrates existing students, class sessions, and attendance records from SQLite to MySQL."""
        sqlite_path = self.config.get("SQLITE_PATH", "data/smart_classroom.db")
        if not os.path.exists(sqlite_path):
            return

        try:
            s_conn = sqlite3.connect(sqlite_path)
            s_conn.row_factory = sqlite3.Row
            s_cur = s_conn.cursor()
            m_cur = mysql_conn.cursor()

            # 1. Migrate Students (preserving custom student IDs, photo paths, and active status)
            m_cur.execute("SELECT COUNT(*) AS cnt FROM students")
            m_row = m_cur.fetchone()
            m_stu_count = m_row["cnt"] if isinstance(m_row, dict) else m_row[0]
            if m_stu_count == 0:
                s_cur.execute("SELECT * FROM students")
                s_students = s_cur.fetchall()
                for stu in s_students:
                    m_cur.execute("""
                        INSERT IGNORE INTO students (id, student_id, name, department, email, embedding_file, photo_path, is_active, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        stu["id"], stu["student_id"], stu["name"],
                        stu["department"] if "department" in stu.keys() else "Computer Science",
                        stu["email"] if "email" in stu.keys() else None,
                        stu["embedding_file"] if "embedding_file" in stu.keys() else None,
                        stu["photo_path"] if "photo_path" in stu.keys() else None,
                        stu["is_active"] if "is_active" in stu.keys() else 1,
                        stu["created_at"] if "created_at" in stu.keys() else None
                    ))
                if s_students:
                    print(f"[DB MIGRATION] Preserved and migrated {len(s_students)} student profile(s) from SQLite to MySQL.")

            # 2. Migrate Class Sessions
            m_cur.execute("SELECT COUNT(*) AS cnt FROM class_sessions")
            m_row = m_cur.fetchone()
            m_sess_count = m_row["cnt"] if isinstance(m_row, dict) else m_row[0]
            if m_sess_count == 0:
                s_cur.execute("SELECT * FROM class_sessions")
                s_sessions = s_cur.fetchall()
                for sess in s_sessions:
                    m_cur.execute("""
                        INSERT IGNORE INTO class_sessions (id, session_code, title, admin_id, start_time, end_time, duration_minutes, status, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        sess["id"], sess["session_code"], sess["title"],
                        sess["admin_id"] if "admin_id" in sess.keys() else 1,
                        sess["start_time"],
                        sess["end_time"] if "end_time" in sess.keys() else None,
                        sess["duration_minutes"] if "duration_minutes" in sess.keys() else 0,
                        sess["status"] if "status" in sess.keys() else "ACTIVE",
                        sess["created_at"] if "created_at" in sess.keys() else None
                    ))
                if s_sessions:
                    print(f"[DB MIGRATION] Preserved and migrated {len(s_sessions)} class session(s) from SQLite to MySQL.")

            # 3. Migrate Attendance Records with exact Join & Exit Timings
            m_cur.execute("SELECT COUNT(*) AS cnt FROM attendance_records")
            m_row = m_cur.fetchone()
            m_att_count = m_row["cnt"] if isinstance(m_row, dict) else m_row[0]
            if m_att_count == 0:
                s_cur.execute("SELECT * FROM attendance_records")
                s_records = s_cur.fetchall()
                for r in s_records:
                    m_cur.execute("""
                        INSERT IGNORE INTO attendance_records (
                            id, session_id, student_id, student_name, log_date,
                            join_time, check_in_time, last_seen_time, exit_time,
                            duration_seconds, status, attendance_status,
                            attentiveness_avg, drowsiness_detected, remarks,
                            created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        r["id"],
                        r["session_id"] if "session_id" in r.keys() else None,
                        r["student_id"],
                        r["student_name"],
                        r["log_date"],
                        r["join_time"] if "join_time" in r.keys() else r.get("check_in_time"),
                        r["check_in_time"],
                        r["last_seen_time"],
                        r["exit_time"] if "exit_time" in r.keys() else r.get("last_seen_time"),
                        r["duration_seconds"] if "duration_seconds" in r.keys() else 0,
                        r["status"] if "status" in r.keys() else "Present",
                        r["attendance_status"] if "attendance_status" in r.keys() else (r.get("status") or "Present"),
                        r["attentiveness_avg"] if "attentiveness_avg" in r.keys() else 100.0,
                        r["drowsiness_detected"] if "drowsiness_detected" in r.keys() else 0,
                        r["remarks"] if "remarks" in r.keys() else None,
                        r["created_at"] if "created_at" in r.keys() else None,
                        r["updated_at"] if "updated_at" in r.keys() else None
                    ))
                if s_records:
                    print(f"[DB MIGRATION] Preserved and migrated {len(s_records)} attendance record(s) from SQLite to MySQL.")

            # 4. Migrate Admin credentials if needed
            m_cur.execute("SELECT COUNT(*) AS cnt FROM admins")
            m_row = m_cur.fetchone()
            m_adm_count = m_row["cnt"] if isinstance(m_row, dict) else m_row[0]
            if m_adm_count == 0:
                s_cur.execute("SELECT * FROM admins")
                s_admins = s_cur.fetchall()
                for a in s_admins:
                    m_cur.execute("""
                        INSERT IGNORE INTO admins (id, username, password_hash, full_name, email, role, created_at, last_login)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        a["id"], a["username"], a["password_hash"],
                        a["full_name"] if "full_name" in a.keys() else "Administrator",
                        a["email"] if "email" in a.keys() else None,
                        a["role"] if "role" in a.keys() else "admin",
                        a["created_at"] if "created_at" in a.keys() else None,
                        a["last_login"] if "last_login" in a.keys() else None
                    ))

            s_conn.close()
        except Exception as e:
            print(f"[DB MIGRATION WARNING] Could not auto-migrate from SQLite to MySQL: {e}")

    # ==========================================
    # AUTHENTICATION
    # ==========================================
    def authenticate_admin(self, username, password):
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        try:
            cursor = conn.cursor()
            q = "SELECT * FROM admins WHERE username = %s" if is_mysql else "SELECT * FROM admins WHERE username = ?"
            cursor.execute(q, (username,))
            user = cursor.fetchone()
            if user:
                # Format to dict if sqlite Row
                user_dict = dict(user) if not is_mysql else user
                if check_password_hash(user_dict["password_hash"], password):
                    # Update last login timestamp
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    upd_q = "UPDATE admins SET last_login = %s WHERE id = %s" if is_mysql else "UPDATE admins SET last_login = ? WHERE id = ?"
                    cursor.execute(upd_q, (now_str, user_dict["id"]))
                    if not is_mysql:
                        conn.commit()
                    return user_dict
            return None
        finally:
            conn.close()

    def get_admin_by_id(self, admin_id):
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        try:
            cursor = conn.cursor()
            q = "SELECT id, username, full_name, email, role, created_at, last_login FROM admins WHERE id = %s" if is_mysql else "SELECT id, username, full_name, email, role, created_at, last_login FROM admins WHERE id = ?"
            cursor.execute(q, (admin_id,))
            user = cursor.fetchone()
            return dict(user) if user and not is_mysql else user
        finally:
            conn.close()

    def update_admin_profile(self, admin_id, full_name, email, new_password=None):
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        try:
            cursor = conn.cursor()
            if new_password:
                pw_hash = generate_password_hash(new_password)
                q = "UPDATE admins SET full_name=%s, email=%s, password_hash=%s WHERE id=%s" if is_mysql else "UPDATE admins SET full_name=?, email=?, password_hash=? WHERE id=?"
                cursor.execute(q, (full_name, email, pw_hash, admin_id))
            else:
                q = "UPDATE admins SET full_name=%s, email=%s WHERE id=%s" if is_mysql else "UPDATE admins SET full_name=?, email=? WHERE id=?"
                cursor.execute(q, (full_name, email, admin_id))
            if not is_mysql:
                conn.commit()
            return True
        finally:
            conn.close()

    # ==========================================
    # STUDENTS MANAGEMENT
    # ==========================================
    def get_all_students(self):
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        try:
            cursor = conn.cursor()
            q = "SELECT * FROM students WHERE is_active = 1 ORDER BY name ASC"
            cursor.execute(q)
            rows = cursor.fetchall()
            return [dict(r) if not is_mysql else r for r in rows]
        finally:
            conn.close()

    def get_student_by_name(self, name):
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        try:
            cursor = conn.cursor()
            q = "SELECT * FROM students WHERE LOWER(name) = LOWER(%s) AND is_active = 1" if is_mysql else "SELECT * FROM students WHERE LOWER(name) = LOWER(?) AND is_active = 1"
            cursor.execute(q, (name,))
            row = cursor.fetchone()
            return dict(row) if row and not is_mysql else row
        finally:
            conn.close()

    def add_student(self, student_id, name, department="Computer Science", email=None, embedding_file=None, photo_path=None):
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor = conn.cursor()
            q = """
                INSERT INTO students (student_id, name, department, email, embedding_file, photo_path, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """ if is_mysql else """
                INSERT INTO students (student_id, name, department, email, embedding_file, photo_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(q, (student_id, name, department, email, embedding_file, photo_path, now_str))
            if not is_mysql:
                conn.commit()
            return True
        finally:
            conn.close()

    def delete_student(self, student_id):
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        try:
            cursor = conn.cursor()
            q = "UPDATE students SET is_active = 0 WHERE id = %s" if is_mysql else "UPDATE students SET is_active = 0 WHERE id = ?"
            cursor.execute(q, (student_id,))
            if not is_mysql:
                conn.commit()
            return True
        finally:
            conn.close()

    # ==========================================
    # ATTENDANCE WITH TIMESTAMP LOGGING
    # ==========================================
    # ==========================================
    # ONLINE CLASS SESSIONS MANAGEMENT
    # ==========================================
    def start_class_session(self, title="Online Class Lecture", admin_id=1):
        """Starts a new online class session. If an active session exists, returns it."""
        active = self.get_active_class_session()
        if active:
            return active

        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        now = datetime.now()
        start_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        code = f"CLS-{now.strftime('%Y%m%d')}-{int(time.time()) % 10000:04d}"

        try:
            cursor = conn.cursor()
            ins_q = """
                INSERT INTO class_sessions (session_code, title, admin_id, start_time, duration_minutes, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """ if is_mysql else """
                INSERT INTO class_sessions (session_code, title, admin_id, start_time, duration_minutes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(ins_q, (code, title, admin_id, start_time_str, 0, "ACTIVE", start_time_str))
            if not is_mysql:
                conn.commit()
                sess_id = cursor.lastrowid
            else:
                cursor.execute("SELECT LAST_INSERT_ID() as id;")
                row = cursor.fetchone()
                sess_id = row["id"] if isinstance(row, dict) else row[0]

            return {
                "id": sess_id,
                "session_code": code,
                "title": title,
                "start_time": start_time_str,
                "status": "ACTIVE"
            }
        finally:
            conn.close()

    def get_active_class_session(self):
        """Returns current active online class session, or None."""
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        try:
            cursor = conn.cursor()
            q = "SELECT * FROM class_sessions WHERE status = 'ACTIVE' ORDER BY id DESC LIMIT 1"
            cursor.execute(q)
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row) if not is_mysql else row
            
            # Calculate live elapsed minutes
            try:
                st = datetime.strptime(data["start_time"], "%Y-%m-%d %H:%M:%S")
                elapsed_sec = max(0, int((datetime.now() - st).total_seconds()))
                data["elapsed_seconds"] = elapsed_sec
                data["elapsed_formatted"] = self.format_duration(elapsed_sec)
            except Exception:
                data["elapsed_seconds"] = 0
                data["elapsed_formatted"] = "00:00"
            return data
        finally:
            conn.close()

    def end_class_session(self, session_id=None):
        """Ends the active class session, sealing all students' exit_time, duration, and attendance_status."""
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        now = datetime.now()
        end_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        time_clock_str = now.strftime("%I:%M:%S %p")

        try:
            cursor = conn.cursor()
            if not session_id:
                active = self.get_active_class_session()
                if not active:
                    return None
                session_id = active["id"]

            # Lookup session
            q_s = "SELECT * FROM class_sessions WHERE id = %s" if is_mysql else "SELECT * FROM class_sessions WHERE id = ?"
            cursor.execute(q_s, (session_id,))
            s_row = cursor.fetchone()
            if not s_row:
                return None
            sess_dict = dict(s_row) if not is_mysql else s_row

            # Compute duration minutes
            duration_mins = 0
            try:
                st = datetime.strptime(sess_dict["start_time"], "%Y-%m-%d %H:%M:%S")
                duration_mins = max(1, int((now - st).total_seconds() // 60))
            except Exception:
                pass

            # Update session status
            upd_sess = "UPDATE class_sessions SET status = 'COMPLETED', end_time = %s, duration_minutes = %s WHERE id = %s" if is_mysql else "UPDATE class_sessions SET status = 'COMPLETED', end_time = ?, duration_minutes = ? WHERE id = ?"
            cursor.execute(upd_sess, (end_time_str, duration_mins, session_id))

            # Seal attendance records ONLY for this specific session (Requirement 3 & 6)
            sess_duration_sec = max(60, duration_mins * 60)
            
            # Fetch records in this session to accurately seal their exit_time and duration
            q_get = "SELECT id, log_date, join_time, check_in_time, duration_seconds FROM attendance_records WHERE session_id = %s" if is_mysql else "SELECT id, log_date, join_time, check_in_time, duration_seconds FROM attendance_records WHERE session_id = ?"
            cursor.execute(q_get, (session_id,))
            session_recs = cursor.fetchall()
            
            for srec in session_recs:
                srec_dict = dict(srec) if not is_mysql else srec
                rid = srec_dict["id"]
                jt = srec_dict.get("join_time") or srec_dict.get("check_in_time")
                calc_dur = self._calculate_record_duration({
                    "log_date": srec_dict.get("log_date"),
                    "join_time": jt,
                    "exit_time": time_clock_str,
                    "duration_seconds": srec_dict.get("duration_seconds", 0)
                }, session_duration=sess_duration_sec)
                
                status = "Left Early" if calc_dur < (sess_duration_sec * 0.5) else "Present"
                
                upd_att = """
                    UPDATE attendance_records SET
                        exit_time = %s,
                        last_seen_time = %s,
                        duration_seconds = %s,
                        attendance_status = %s,
                        updated_at = %s
                    WHERE id = %s
                """ if is_mysql else """
                    UPDATE attendance_records SET
                        exit_time = ?,
                        last_seen_time = ?,
                        duration_seconds = ?,
                        attendance_status = ?,
                        updated_at = ?
                    WHERE id = ?
                """
                cursor.execute(upd_att, (time_clock_str, time_clock_str, calc_dur, status, end_time_str, rid))

            if not is_mysql:
                conn.commit()
            return {"session_id": session_id, "duration_minutes": duration_mins, "end_time": end_time_str}
        finally:
            conn.close()

    def get_all_sessions(self, limit=30):
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        try:
            cursor = conn.cursor()
            q = f"SELECT * FROM class_sessions ORDER BY id DESC LIMIT {limit}"
            cursor.execute(q)
            rows = cursor.fetchall()
            return [dict(r) if not is_mysql else r for r in rows]
        finally:
            conn.close()

    # ==========================================
    # ATTENDANCE WITH TIMESTAMP LOGGING
    # ==========================================
    @staticmethod
    def format_duration(seconds):
        """Helper to format duration seconds to human-readable format."""
        if not seconds or seconds < 0:
            return "0s"
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours}h {mins}m {secs}s"
        elif mins > 0:
            return f"{mins}m {secs}s"
        else:
            return f"{secs}s"

    @staticmethod
    def _parse_time_string(date_str, time_str):
        """Parses various date and time strings into a datetime object."""
        if not time_str:
            return None
        time_str = str(time_str).strip()
        # Direct format attempts if string already contains full date
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %I:%M:%S %p"):
            try:
                return datetime.strptime(time_str, fmt)
            except Exception:
                pass

        # Combine date_str and time_str
        if date_str:
            date_str = str(date_str).strip()
            for fmt in ("%Y-%m-%d %I:%M:%S %p", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %I:%M %p"):
                try:
                    return datetime.strptime(f"{date_str} {time_str}", fmt)
                except Exception:
                    pass
        return None

    @staticmethod
    def _get_session_duration_seconds(session_dict):
        """Calculates actual session duration in seconds, clamped safely."""
        if not session_dict:
            return 0
        st = session_dict.get("start_time")
        et = session_dict.get("end_time")
        dur_sec = 0
        if st and et:
            try:
                t1 = datetime.strptime(str(st).strip(), "%Y-%m-%d %H:%M:%S")
                t2 = datetime.strptime(str(et).strip(), "%Y-%m-%d %H:%M:%S")
                dur_sec = max(0, int((t2 - t1).total_seconds()))
            except Exception:
                pass
        if dur_sec <= 0 and session_dict.get("duration_minutes", 0):
            try:
                dur_sec = int(session_dict["duration_minutes"]) * 60
            except Exception:
                pass
        if dur_sec <= 0 and session_dict.get("status") == "ACTIVE" and st:
            try:
                t1 = datetime.strptime(str(st).strip(), "%Y-%m-%d %H:%M:%S")
                dur_sec = max(0, int((datetime.now() - t1).total_seconds()))
            except Exception:
                pass
        return max(60, dur_sec) if dur_sec > 0 else 60

    def _calculate_record_duration(self, record, session_duration=None):
        """
        Calculates valid time in class from join_time and exit_time,
        strictly capping it so it cannot exceed the session duration (Requirement 4 & 6).
        """
        if not record:
            return 0
        log_date = record.get("log_date", "")
        join_str = record.get("join_time") or record.get("check_in_time")
        exit_str = record.get("exit_time") or record.get("last_seen_time")

        dur = 0
        t_in = self._parse_time_string(log_date, join_str)
        t_out = self._parse_time_string(log_date, exit_str)

        if t_in and t_out:
            if t_out >= t_in:
                dur = int((t_out - t_in).total_seconds())
            else:
                dur = 0
        else:
            dur = record.get("duration_seconds", 0) or 0

        # Cap at session duration if provided (Requirement 6)
        if session_duration and session_duration > 0:
            dur = min(dur, session_duration)
        else:
            dur = min(dur, 86400)

        return max(0, int(dur))


    def record_or_update_attendance(self, student_name, attentiveness=100.0, is_drowsy=False, session_id=None):
        """
        Records or updates attendance with exact timestamps:
        - join_time / check_in_time
        - last_seen_time
        - exit_time
        - duration_seconds
        - attendance_status
        """
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%I:%M:%S %p")
        datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # Auto-detect active session if not passed
        if session_id is None:
            active = self.get_active_class_session()
            if active:
                session_id = active["id"]

        try:
            cursor = conn.cursor()

            # Find student roll number if registered
            student = self.get_student_by_name(student_name)
            student_id = student["student_id"] if student else f"STU-{student_name.upper()[:4]}"

            # Check if record exists for today (and current session if active)
            if session_id:
                check_q = """
                    SELECT * FROM attendance_records 
                    WHERE student_name = %s AND log_date = %s AND session_id = %s
                """ if is_mysql else """
                    SELECT * FROM attendance_records 
                    WHERE student_name = ? AND log_date = ? AND session_id = ?
                """
                cursor.execute(check_q, (student_name, date_str, session_id))
            else:
                check_q = """
                    SELECT * FROM attendance_records 
                    WHERE student_name = %s AND log_date = %s
                """ if is_mysql else """
                    SELECT * FROM attendance_records 
                    WHERE student_name = ? AND log_date = ?
                """
                cursor.execute(check_q, (student_name, date_str))

            record = cursor.fetchone()
            record_dict = dict(record) if record and not is_mysql else record

            if not record_dict:
                # First detection -> Create new attendance check-in / join record
                remarks = "On-time arrival"
                status = "Present"
                attendance_status = "Present"

                # Check late arrival if arrived after 09:30 AM
                if now.hour > 9 or (now.hour == 9 and now.minute > 30):
                    remarks = "Late arrival"
                    status = "Late"
                    attendance_status = "Late"

                ins_q = """
                    INSERT INTO attendance_records (
                        session_id, student_id, student_name, log_date,
                        join_time, check_in_time, last_seen_time, exit_time,
                        duration_seconds, status, attendance_status,
                        attentiveness_avg, drowsiness_detected, remarks,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """ if is_mysql else """
                    INSERT INTO attendance_records (
                        session_id, student_id, student_name, log_date,
                        join_time, check_in_time, last_seen_time, exit_time,
                        duration_seconds, status, attendance_status,
                        attentiveness_avg, drowsiness_detected, remarks,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(ins_q, (
                    session_id, student_id, student_name, date_str,
                    time_str, time_str, time_str, time_str,
                    0, status, attendance_status,
                    float(attentiveness), 1 if is_drowsy else 0, remarks,
                    datetime_str, datetime_str
                ))
                if not is_mysql:
                    conn.commit()
                return {
                    "is_new": True,
                    "student_name": student_name,
                    "student_id": student_id,
                    "join_time": time_str,
                    "last_seen_time": time_str,
                    "exit_time": time_str,
                    "duration": 0,
                    "duration_formatted": "0s",
                    "attendance_status": attendance_status,
                    "date": date_str
                }
            else:
                # Existing record -> update last_seen_time, exit_time, and duration
                rec_id = record_dict["id"]
                join_time_str = record_dict.get("join_time") or record_dict.get("check_in_time")
                
                # Calculate duration in seconds
                duration = record_dict["duration_seconds"]
                try:
                    t_in = datetime.strptime(f"{date_str} {join_time_str}", "%Y-%m-%d %I:%M:%S %p")
                    duration = max(0, int((now - t_in).total_seconds()))
                except Exception:
                    duration += 5  # incremental fallback

                prev_att = float(record_dict.get("attentiveness_avg", 100.0) or 100.0)
                new_att = round((prev_att * 0.9) + (attentiveness * 0.1), 1)  # Exponential moving avg
                drowsy_flag = record_dict.get("drowsiness_detected", 0) or (1 if is_drowsy else 0)

                # Keep status updated
                att_status = record_dict.get("attendance_status") or record_dict.get("status") or "Present"

                upd_q = """
                    UPDATE attendance_records SET
                        last_seen_time = %s,
                        exit_time = %s,
                        duration_seconds = %s,
                        attentiveness_avg = %s,
                        drowsiness_detected = %s,
                        attendance_status = %s,
                        updated_at = %s
                    WHERE id = %s
                """ if is_mysql else """
                    UPDATE attendance_records SET
                        last_seen_time = ?,
                        exit_time = ?,
                        duration_seconds = ?,
                        attentiveness_avg = ?,
                        drowsiness_detected = ?,
                        attendance_status = ?,
                        updated_at = ?
                    WHERE id = ?
                """
                cursor.execute(upd_q, (time_str, time_str, duration, new_att, drowsy_flag, att_status, datetime_str, rec_id))
                if not is_mysql:
                    conn.commit()
                return {
                    "is_new": False,
                    "student_name": student_name,
                    "student_id": student_id,
                    "join_time": join_time_str,
                    "last_seen_time": time_str,
                    "exit_time": time_str,
                    "duration": duration,
                    "duration_formatted": self.format_duration(duration),
                    "attendance_status": att_status
                }
        finally:
            conn.close()

    def get_attendance_logs(self, date=None, student_query=None, session_id=None, status=None, only_valid_sessions=True):
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        try:
            cursor = conn.cursor()
            conditions = []
            params = []

            if date:
                conditions.append("log_date = %s" if is_mysql else "log_date = ?")
                params.append(date)

            if session_id:
                conditions.append("session_id = %s" if is_mysql else "session_id = ?")
                params.append(session_id)
            elif only_valid_sessions:
                # Requirement 3 & 5: Only include records belonging to valid class sessions
                conditions.append("session_id IS NOT NULL AND session_id IN (SELECT id FROM class_sessions)")

            if status and status != "All":
                conditions.append("(attendance_status = %s OR status = %s)" if is_mysql else "(attendance_status = ? OR status = ?)")
                params.append(status)
                params.append(status)

            if student_query:
                conditions.append("(student_name LIKE %s OR student_id LIKE %s)" if is_mysql else "(student_name LIKE ? OR student_id LIKE ?)")
                params.append(f"%{student_query}%")
                params.append(f"%{student_query}%")

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            q = f"SELECT * FROM attendance_records {where_clause} ORDER BY id DESC"
            cursor.execute(q, params)
            rows = cursor.fetchall()

            # Pre-fetch class sessions to compute accurate session duration caps
            cursor.execute("SELECT * FROM class_sessions")
            sessions_dict = {}
            for s in cursor.fetchall():
                s_dict = dict(s) if not is_mysql else s
                sessions_dict[s_dict["id"]] = s_dict

            results = []
            for r in rows:
                item = dict(r) if not is_mysql else r
                # Normalize join_time, exit_time, attendance_status
                if not item.get("join_time"):
                    item["join_time"] = item.get("check_in_time", "")
                if not item.get("exit_time"):
                    item["exit_time"] = item.get("last_seen_time", "")
                if not item.get("attendance_status"):
                    item["attendance_status"] = item.get("status", "Present")

                # Look up session duration cap (Requirement 6)
                s_obj = sessions_dict.get(item.get("session_id"))
                sess_dur = self._get_session_duration_seconds(s_obj) if s_obj else None

                # Calculate duration from valid join_time and exit_time (Requirement 4 & 6)
                valid_dur = self._calculate_record_duration(item, session_duration=sess_dur)
                item["duration_seconds"] = valid_dur
                item["duration_formatted"] = self.format_duration(valid_dur)
                results.append(item)
            return results
        finally:
            conn.close()

    def mark_manual_attendance(self, student_id, status="Present", remarks="Manual entry by Admin"):
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%I:%M:%S %p")
        datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")

        active = self.get_active_class_session()
        sess_id = active["id"] if active else None
        if not sess_id:
            # Fallback to the most recent class session so record belongs to a valid session
            try:
                cursor_s = conn.cursor()
                cursor_s.execute("SELECT id FROM class_sessions ORDER BY id DESC LIMIT 1")
                last_s = cursor_s.fetchone()
                if last_s:
                    sess_id = (dict(last_s)["id"] if not is_mysql else last_s["id"])
            except Exception:
                pass

        try:
            cursor = conn.cursor()
            # Lookup student
            q_s = "SELECT * FROM students WHERE student_id = %s OR id = %s" if is_mysql else "SELECT * FROM students WHERE student_id = ? OR id = ?"
            cursor.execute(q_s, (student_id, student_id))
            student = cursor.fetchone()
            s_dict = dict(student) if student and not is_mysql else student

            if not s_dict:
                return False, "Student not found"

            s_name = s_dict["name"]
            sid = s_dict["student_id"]

            ins_q = """
                INSERT INTO attendance_records (
                    session_id, student_id, student_name, log_date,
                    join_time, check_in_time, last_seen_time, exit_time,
                    duration_seconds, status, attendance_status,
                    attentiveness_avg, drowsiness_detected, remarks,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """ if is_mysql else """
                INSERT INTO attendance_records (
                    session_id, student_id, student_name, log_date,
                    join_time, check_in_time, last_seen_time, exit_time,
                    duration_seconds, status, attendance_status,
                    attentiveness_avg, drowsiness_detected, remarks,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(ins_q, (
                sess_id, sid, s_name, date_str,
                time_str, time_str, time_str, time_str,
                0, status, status, 100.0, 0, remarks,
                datetime_str, datetime_str
            ))
            if not is_mysql:
                conn.commit()
            return True, "Marked successfully"
        finally:
            conn.close()

    def mark_student_exit(self, student_id, session_id=None):
        """Records student exit timestamp, calculates duration, and updates attendance status."""
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%I:%M:%S %p")
        datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")

        try:
            cursor = conn.cursor()
            # Lookup latest attendance record for this student today
            if session_id:
                q = """
                    SELECT * FROM attendance_records
                    WHERE (student_id = %s OR student_name = %s) AND log_date = %s AND session_id = %s
                    ORDER BY id DESC LIMIT 1
                """ if is_mysql else """
                    SELECT * FROM attendance_records
                    WHERE (student_id = ? OR student_name = ?) AND log_date = ? AND session_id = ?
                    ORDER BY id DESC LIMIT 1
                """
                cursor.execute(q, (student_id, student_id, date_str, session_id))
            else:
                q = """
                    SELECT * FROM attendance_records
                    WHERE (student_id = %s OR student_name = %s) AND log_date = %s
                    ORDER BY id DESC LIMIT 1
                """ if is_mysql else """
                    SELECT * FROM attendance_records
                    WHERE (student_id = ? OR student_name = ?) AND log_date = ?
                    ORDER BY id DESC LIMIT 1
                """
                cursor.execute(q, (student_id, student_id, date_str))

            row = cursor.fetchone()
            if not row:
                return False, "No active attendance record found for this student today."

            record = dict(row) if not is_mysql else row
            rec_id = record["id"]
            join_time_str = record.get("join_time") or record.get("check_in_time")

            # Calculate duration
            duration = record.get("duration_seconds", 0) or 0
            try:
                t_in = datetime.strptime(f"{date_str} {join_time_str}", "%Y-%m-%d %I:%M:%S %p")
                duration = max(0, int((now - t_in).total_seconds()))
            except Exception:
                pass

            upd_q = """
                UPDATE attendance_records SET
                    exit_time = %s,
                    last_seen_time = %s,
                    duration_seconds = %s,
                    attendance_status = %s,
                    updated_at = %s
                WHERE id = %s
            """ if is_mysql else """
                UPDATE attendance_records SET
                    exit_time = ?,
                    last_seen_time = ?,
                    duration_seconds = ?,
                    attendance_status = ?,
                    updated_at = ?
                WHERE id = ?
            """
            status = "Left Early" if duration < 1800 else "Present"
            cursor.execute(upd_q, (time_str, time_str, duration, status, datetime_str, rec_id))
            if not is_mysql:
                conn.commit()

            return True, f"Exit time recorded at {time_str} (Duration: {self.format_duration(duration)})"
        finally:
            conn.close()

    def get_dashboard_stats(self):
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            cursor = conn.cursor()
            # Total enrolled students
            cursor.execute("SELECT COUNT(*) as cnt FROM students WHERE is_active = 1")
            row = cursor.fetchone()
            total_students = (dict(row)["cnt"] if not is_mysql else row["cnt"]) if row else 0

            # Present today: only count distinct students with attendance in valid class sessions
            q_pres = """
                SELECT COUNT(DISTINCT student_id) as cnt 
                FROM attendance_records 
                WHERE log_date = %s AND session_id IS NOT NULL AND session_id IN (SELECT id FROM class_sessions)
            """ if is_mysql else """
                SELECT COUNT(DISTINCT student_id) as cnt 
                FROM attendance_records 
                WHERE log_date = ? AND session_id IS NOT NULL AND session_id IN (SELECT id FROM class_sessions)
            """
            cursor.execute(q_pres, (today,))
            row = cursor.fetchone()
            present_today = (dict(row)["cnt"] if not is_mysql else row["cnt"]) if row else 0

            # Average attentiveness today for valid session records
            q_att = """
                SELECT AVG(attentiveness_avg) as avg_att 
                FROM attendance_records 
                WHERE log_date = %s AND session_id IS NOT NULL AND session_id IN (SELECT id FROM class_sessions)
            """ if is_mysql else """
                SELECT AVG(attentiveness_avg) as avg_att 
                FROM attendance_records 
                WHERE log_date = ? AND session_id IS NOT NULL AND session_id IN (SELECT id FROM class_sessions)
            """
            cursor.execute(q_att, (today,))
            row = cursor.fetchone()
            avg_att = (dict(row)["avg_att"] if not is_mysql else row["avg_att"]) if row else None
            avg_att_val = round(float(avg_att), 1) if avg_att is not None else 100.0

            # Drowsiness count today for valid session records
            q_drowsy = """
                SELECT COUNT(*) as cnt 
                FROM attendance_records 
                WHERE log_date = %s AND session_id IS NOT NULL AND session_id IN (SELECT id FROM class_sessions) AND drowsiness_detected = 1
            """ if is_mysql else """
                SELECT COUNT(*) as cnt 
                FROM attendance_records 
                WHERE log_date = ? AND session_id IS NOT NULL AND session_id IN (SELECT id FROM class_sessions) AND drowsiness_detected = 1
            """
            cursor.execute(q_drowsy, (today,))
            row = cursor.fetchone()
            drowsy_count = (dict(row)["cnt"] if not is_mysql else row["cnt"]) if row else 0

            # Total sessions held
            cursor.execute("SELECT COUNT(*) as cnt FROM class_sessions")
            row = cursor.fetchone()
            total_sessions = (dict(row)["cnt"] if not is_mysql else row["cnt"]) if row else 0

            # Active session
            active_session = self.get_active_class_session()

            # Strict 100% cap on attendance rate (Requirement 1)
            attendance_rate = round((present_today / total_students * 100), 1) if total_students > 0 else 0.0
            attendance_rate = min(100.0, max(0.0, attendance_rate))

            return {
                "total_students": total_students,
                "present_today": present_today,
                "attendance_rate": attendance_rate,
                "avg_attentiveness": min(100.0, max(0.0, avg_att_val)),
                "drowsy_count": drowsy_count,
                "total_sessions": total_sessions,
                "active_session": active_session,
                "today_date": today,
                "active_db": self.active_db,
                "mysql_error": self.mysql_error
            }
        finally:
            conn.close()

    def get_student_reports_summary(self):
        """
        Generates comprehensive student-by-student reports for analytics and reports page.
        - Calculates attendance percentage using unique completed class sessions (never exceeds 100%).
        - Only counts attendance records belonging to valid completed class sessions.
        - Ignores future/invalid/duplicate records.
        - Calculates total time in class strictly from valid join_time and exit_time, capped at session duration.
        """
        students = self.get_all_students()

        # 1. Fetch all completed class sessions (Requirement 2 & 3)
        conn = self.get_connection()
        is_mysql = (self.active_db == "mysql")
        try:
            cursor = conn.cursor()
            q_sess = "SELECT * FROM class_sessions WHERE status = 'COMPLETED' ORDER BY id ASC"
            cursor.execute(q_sess)
            completed_sessions = [dict(r) if not is_mysql else r for r in cursor.fetchall()]
        finally:
            conn.close()

        total_completed_classes = len(completed_sessions)
        session_map = {s["id"]: s for s in completed_sessions}
        session_durations = {s["id"]: self._get_session_duration_seconds(s) for s in completed_sessions}

        # 2. Fetch attendance records belonging to valid completed class sessions (Requirement 3)
        all_records = self.get_attendance_logs(only_valid_sessions=True) if completed_sessions else []
        valid_records = [r for r in all_records if r.get("session_id") in session_map]

        # 3. Filter out invalid or future records (Requirement 5)
        today_str = datetime.now().strftime("%Y-%m-%d")
        clean_records = []
        for r in valid_records:
            log_date = r.get("log_date", "")
            if log_date > today_str:
                continue
            if not r.get("student_id") and not r.get("student_name"):
                continue
            clean_records.append(r)

        reports = []
        for s in students:
            sid = s["student_id"]
            sname = s["name"]

            # Filter records for this student
            s_records = [
                r for r in clean_records
                if (r.get("student_id") and r["student_id"] == sid) or
                   (r.get("student_name") and r["student_name"].lower() == sname.lower())
            ]

            # Group student records by session_id (Requirement 2 & 5: deduplicate multiple records in same session)
            session_to_records = {}
            for r in s_records:
                sess_id = r.get("session_id")
                if sess_id not in session_to_records:
                    session_to_records[sess_id] = []
                session_to_records[sess_id].append(r)

            # Unique completed sessions attended (Requirement 2)
            attended_session_ids = set(session_to_records.keys())
            attended_count = len(attended_session_ids)

            # Strict cap: attended_classes cannot exceed total_completed_classes (Requirement 1 & 2)
            if total_completed_classes > 0:
                attended_count = min(attended_count, total_completed_classes)
                pct = round((attended_count / total_completed_classes) * 100, 1)
                pct = min(100.0, max(0.0, pct))
            else:
                attended_count = 0
                pct = 0.0

            # Calculate total time in class and attentiveness from valid records
            total_duration_sec = 0
            attention_scores = []
            drowsy_incidents = 0
            last_seen_val = "Never"

            for sess_id, rec_list in session_to_records.items():
                sess_dur = session_durations.get(sess_id, 3600)
                sess_student_dur = 0
                for r in rec_list:
                    rec_dur = self._calculate_record_duration(r, session_duration=sess_dur)
                    sess_student_dur += rec_dur
                    if r.get("attentiveness_avg") is not None:
                        try:
                            attention_scores.append(float(r["attentiveness_avg"]))
                        except Exception:
                            pass
                    if r.get("drowsiness_detected"):
                        drowsy_incidents += 1
                    if r.get("last_seen_time") and last_seen_val == "Never":
                        last_seen_val = r["last_seen_time"]

                # Student duration in a session cannot exceed the actual class session duration (Requirement 6)
                sess_student_dur = min(sess_student_dur, sess_dur)
                total_duration_sec += sess_student_dur

            avg_att = round(sum(attention_scores) / len(attention_scores), 1) if attention_scores else 100.0
            avg_att = min(100.0, max(0.0, avg_att))

            # Performance Grade
            if pct >= 85:
                grade = "Excellent"
                badge_class = "success"
            elif pct >= 70:
                grade = "Good"
                badge_class = "info"
            elif pct >= 50:
                grade = "Average"
                badge_class = "warning"
            else:
                grade = "Low Attendance"
                badge_class = "danger"

            reports.append({
                "student_id": sid,
                "name": sname,
                "department": s.get("department", "Computer Science"),
                "email": s.get("email", ""),
                "photo_path": s.get("photo_path", ""),
                "total_classes": total_completed_classes,
                "attended_classes": attended_count,
                "attendance_percentage": pct,
                "total_duration_seconds": total_duration_sec,
                "total_duration_formatted": self.format_duration(total_duration_sec),
                "avg_attentiveness": avg_att,
                "drowsy_incidents": drowsy_incidents,
                "grade": grade,
                "badge_class": badge_class,
                "last_seen": last_seen_val
            })

        return {
            "total_classes": total_completed_classes,
            "students_summary": reports,
            "total_students": len(students)
        }

    def get_reports_analytics(self):
        """Returns visual trend data for graphs: turnout per day, attentiveness, and status breakdown."""
        logs = self.get_attendance_logs(only_valid_sessions=True)
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Turnout by date
        date_counts = {}
        status_counts = {"Present": 0, "Late": 0, "Left Early": 0, "Absent": 0}
        attention_breakdown = {"Attentive (>80%)": 0, "Distracted (50-80%)": 0, "Drowsy (<50%)": 0}

        for r in logs:
            d = r.get("log_date", "Unknown")
            # Ignore future records (Requirement 5)
            if d > today_str:
                continue

            date_counts[d] = date_counts.get(d, 0) + 1

            st = r.get("attendance_status") or r.get("status") or "Present"
            if st in status_counts:
                status_counts[st] += 1
            else:
                status_counts["Present"] += 1

            att = float(r.get("attentiveness_avg", 100) or 100)
            if r.get("drowsiness_detected") or att < 50:
                attention_breakdown["Drowsy (<50%)"] += 1
            elif att < 80:
                attention_breakdown["Distracted (50-80%)"] += 1
            else:
                attention_breakdown["Attentive (>80%)"] += 1

        # Sort dates
        sorted_dates = sorted(list(date_counts.keys()))[-7:]
        trend_dates = sorted_dates
        trend_counts = [date_counts[d] for d in sorted_dates]

        return {
            "dates": trend_dates,
            "counts": trend_counts,
            "status_breakdown": status_counts,
            "attention_breakdown": attention_breakdown
        }

    def test_mysql_connection(self, host, port, user, password, database):
        try:
            conn = pymysql.connect(
                host=host,
                port=int(port),
                user=user,
                password=password,
                charset='utf8mb4',
                connect_timeout=3
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.close()
            return True, "Successfully connected to MySQL database!"
        except Exception as e:
            return False, f"MySQL connection error: {str(e)}"

# Singleton database manager instance
_db_manager = None

def get_db():
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
