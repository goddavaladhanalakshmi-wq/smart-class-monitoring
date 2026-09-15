import os
import csv
import io
import time
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, Response, send_file, flash
)
from config import load_config, save_config, BASE_DIR
from database import get_db
from vision_engine import get_vision_engine

app = Flask(__name__)
config = load_config()
app.secret_key = config.get("SECRET_KEY", "smart-class-2026-secret-key")

# Database & Vision Engine instances
db = get_db()
vision_engine = get_vision_engine()

# ==========================================
# AUTHENTICATION GUARD
# ==========================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please sign in as Admin to access the Classroom Monitor.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# WEB VIEW ROUTES
# ==========================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        user = db.authenticate_admin(username, password)
        if user:
            session["admin_logged_in"] = True
            session["admin_id"] = user["id"]
            session["admin_username"] = user["username"]
            session["admin_name"] = user.get("full_name") or user["username"]
            session["admin_role"] = user.get("role", "admin")
            flash(f"Welcome back, {session['admin_name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password. Please try again."

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))

@app.route("/")
def index():
    if request.args.get("view") == "classic":
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))
        return redirect(url_for("dashboard"))
    # Default to modern React UI Single-Page Application
    return render_template("react_app.html")

@app.route("/react")
@app.route("/app")
def react_portal():
    """Serves the modern React UI Single-Page Application."""
    return render_template("react_app.html")

@app.route("/dashboard")
@admin_required
def dashboard():
    # Ensure camera is running for monitoring
    if not vision_engine.running:
        vision_engine.start_camera()

    stats = db.get_dashboard_stats()
    students = db.get_all_students()
    return render_template("monitor.html", stats=stats, students=students)

@app.route("/attendance")
@admin_required
def attendance():
    date_filter = request.args.get("date", "")
    query = request.args.get("q", "")
    records = db.get_attendance_logs(date=date_filter if date_filter else None, student_query=query if query else None)
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("attendance.html", records=records, date_filter=date_filter, query=query, today=today)

@app.route("/students")
@admin_required
def students():
    student_list = db.get_all_students()
    return render_template("students.html", students=student_list)

@app.route("/analytics")
@admin_required
def analytics():
    stats = db.get_dashboard_stats()
    records = db.get_attendance_logs()
    return render_template("analytics.html", stats=stats, total_records=len(records))

@app.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    cfg = load_config()
    db_stats = db.get_dashboard_stats()
    msg = None
    msg_type = "info"

    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_mysql":
            host = request.form.get("host", "localhost").strip()
            port = int(request.form.get("port", 3306))
            user = request.form.get("user", "root").strip()
            password = request.form.get("password", "").strip()
            database = request.form.get("database", "smart_class_db").strip()

            success, test_msg = db.test_mysql_connection(host, port, user, password, database)
            if success:
                cfg["DB_TYPE"] = "mysql"
                cfg["MYSQL"]["host"] = host
                cfg["MYSQL"]["port"] = port
                cfg["MYSQL"]["user"] = user
                cfg["MYSQL"]["password"] = password
                cfg["MYSQL"]["database"] = database
                save_config(cfg)
                # Reconnect
                db.config = cfg
                db._init_db()
                msg = f"MySQL connected and configured successfully! Database: {database}"
                msg_type = "success"
            else:
                msg = f"Failed to connect to MySQL: {test_msg}"
                msg_type = "danger"

        elif action == "update_thresholds":
            cos_th = float(request.form.get("cosine_threshold", 0.363))
            conf_th = float(request.form.get("detection_confidence", 0.6))
            cfg["COSINE_THRESHOLD"] = cos_th
            cfg["DETECTION_CONFIDENCE"] = conf_th
            save_config(cfg)
            vision_engine.config = cfg
            msg = "Detection thresholds updated successfully!"
            msg_type = "success"

        elif action == "update_admin":
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip()
            new_pw = request.form.get("new_password", "").strip()
            admin_id = session.get("admin_id")
            if db.update_admin_profile(admin_id, full_name, email, new_password=new_pw if new_pw else None):
                session["admin_name"] = full_name
                msg = "Admin profile updated successfully!"
                msg_type = "success"
            else:
                msg = "Failed to update profile."
                msg_type = "danger"

    return render_template("settings.html", config=cfg, db_stats=db_stats, msg=msg, msg_type=msg_type)

# ==========================================
# MJPEG VIDEO STREAM ROUTE
# ==========================================
def generate_stream_frames():
    """Video streaming generator function."""
    while True:
        frame_bytes = vision_engine.get_frame_bytes()
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            time.sleep(0.04)

@app.route("/video_feed")
@admin_required
def video_feed():
    if not vision_engine.running:
        vision_engine.start_camera()
    return Response(
        generate_stream_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

# ==========================================
# REST API ENDPOINTS
# ==========================================
@app.route("/api/live_stats")
@admin_required
def api_live_stats():
    telemetry = vision_engine.get_telemetry()
    db_stats = db.get_dashboard_stats()
    now_dt = datetime.now()

    response = {
        "telemetry": telemetry,
        "db_stats": db_stats,
        "server_time": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "server_time_display": now_dt.strftime("%I:%M:%S %p"),
        "server_date": now_dt.strftime("%A, %B %d, %Y"),
        "camera_active": vision_engine.running
    }
    return jsonify(response)

# ==========================================
# REST API - AUTHENTICATION & ACCESS CONTROL
# ==========================================
@app.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    data = request.json or request.form
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    user = db.authenticate_admin(username, password)
    if user:
        session["admin_logged_in"] = True
        session["admin_id"] = user["id"]
        session["admin_username"] = user["username"]
        session["admin_name"] = user.get("full_name") or user["username"]
        session["admin_role"] = user.get("role", "admin")
        return jsonify({
            "success": True,
            "message": f"Welcome back, {session['admin_name']}!",
            "admin": {
                "id": user["id"],
                "username": user["username"],
                "name": session["admin_name"],
                "role": session["admin_role"]
            }
        })
    return jsonify({"success": False, "message": "Invalid admin credentials. Access restricted to Admin only."}), 401

@app.route("/api/auth/logout", methods=["POST", "GET"])
def api_auth_logout():
    session.clear()
    return jsonify({"success": True, "message": "Admin signed out successfully."})

@app.route("/api/auth/check", methods=["GET"])
def api_auth_check():
    is_auth = bool(session.get("admin_logged_in"))
    return jsonify({
        "authenticated": is_auth,
        "admin": {
            "id": session.get("admin_id"),
            "username": session.get("admin_username"),
            "name": session.get("admin_name"),
            "role": session.get("admin_role")
        } if is_auth else None
    })

# ==========================================
# REST API - ONLINE CLASS SESSIONS (ADMIN JOIN & MONITOR)
# ==========================================
@app.route("/api/session/start", methods=["POST"])
@admin_required
def api_session_start():
    data = request.json or request.form
    title = data.get("title", "Smart Classroom Live Session").strip()
    admin_id = session.get("admin_id", 1)

    sess = db.start_class_session(title=title, admin_id=admin_id)
    if not vision_engine.running:
        vision_engine.start_camera()

    return jsonify({
        "success": True,
        "message": f"Class session '{title}' started successfully. Live monitoring active.",
        "session": sess
    })

@app.route("/api/session/end", methods=["POST"])
@admin_required
def api_session_end():
    data = request.json or {}
    session_id = data.get("session_id")
    result = db.end_class_session(session_id=session_id)
    if result:
        return jsonify({
            "success": True,
            "message": f"Session concluded. All students' exit timings and durations have been stored.",
            "result": result
        })
    return jsonify({"success": False, "message": "No active session found to end."}), 400

@app.route("/api/session/active", methods=["GET"])
@admin_required
def api_session_active():
    sess = db.get_active_class_session()
    return jsonify({"active_session": sess})

@app.route("/api/session/list", methods=["GET"])
@admin_required
def api_session_list():
    sessions = db.get_all_sessions(limit=50)
    return jsonify({"sessions": sessions, "total": len(sessions)})

# ==========================================
# REST API - ATTENDANCE WITH JOIN & EXIT TIMINGS
# ==========================================
@app.route("/api/attendance/list", methods=["GET"])
@admin_required
def api_attendance_list():
    date_filter = request.args.get("date", None)
    session_id = request.args.get("session_id", None)
    status_filter = request.args.get("status", None)
    query = request.args.get("q", None)

    records = db.get_attendance_logs(
        date=date_filter if date_filter else None,
        student_query=query if query else None,
        session_id=session_id if session_id else None,
        status=status_filter if status_filter else None
    )
    return jsonify({
        "records": records,
        "total": len(records),
        "query_date": date_filter or datetime.now().strftime("%Y-%m-%d")
    })

@app.route("/api/attendance/mark_exit", methods=["POST"])
@admin_required
def api_attendance_mark_exit():
    data = request.json or {}
    student_id = data.get("student_id")
    session_id = data.get("session_id")

    if not student_id:
        return jsonify({"success": False, "message": "Student ID is required."}), 400

    success, msg = db.mark_student_exit(student_id, session_id=session_id)
    return jsonify({"success": success, "message": msg})

# ==========================================
# REST API - STUDENTS & ENROLLMENT
# ==========================================
@app.route("/api/students", methods=["GET"])
@admin_required
def api_get_students():
    students = db.get_all_students()
    return jsonify({"students": students, "total": len(students)})

# ==========================================
# REST API - ANALYTICS & REPORTS
# ==========================================
@app.route("/api/reports/summary", methods=["GET"])
@admin_required
def api_reports_summary():
    data = db.get_student_reports_summary()
    return jsonify(data)

@app.route("/api/reports/analytics", methods=["GET"])
@admin_required
def api_reports_analytics():
    data = db.get_reports_analytics()
    return jsonify(data)

# ==========================================
# REST API - SETTINGS
# ==========================================
@app.route("/api/settings/update_mysql", methods=["POST"])
@admin_required
def api_settings_update_mysql():
    data = request.json or {}
    host = data.get("host", "localhost").strip()
    port = int(data.get("port", 3306))
    user = data.get("user", "root").strip()
    password = data.get("password", "").strip()
    database = data.get("database", "smart_class_db").strip()

    success, test_msg = db.test_mysql_connection(host, port, user, password, database)
    if success:
        cfg = load_config()
        cfg["DB_TYPE"] = "mysql"
        cfg["MYSQL"]["host"] = host
        cfg["MYSQL"]["port"] = port
        cfg["MYSQL"]["user"] = user
        cfg["MYSQL"]["password"] = password
        cfg["MYSQL"]["database"] = database
        save_config(cfg)
        db.config = cfg
        db._init_db()
        return jsonify({"success": True, "message": f"Connected to MySQL ({database}) successfully!"})
    return jsonify({"success": False, "message": test_msg}), 400

@app.route("/api/settings/update_thresholds", methods=["POST"])
@admin_required
def api_settings_update_thresholds():
    data = request.json or {}
    cos_th = float(data.get("cosine_threshold", 0.363))
    conf_th = float(data.get("detection_confidence", 0.6))

    cfg = load_config()
    cfg["COSINE_THRESHOLD"] = cos_th
    cfg["DETECTION_CONFIDENCE"] = conf_th
    save_config(cfg)
    vision_engine.config = cfg
    return jsonify({"success": True, "message": "Detection thresholds updated successfully."})

@app.route("/api/settings/update_admin", methods=["POST"])
@admin_required
def api_settings_update_admin():
    data = request.json or {}
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip()
    new_pw = data.get("new_password", "").strip()
    admin_id = session.get("admin_id")

    if db.update_admin_profile(admin_id, full_name, email, new_password=new_pw if new_pw else None):
        if full_name:
            session["admin_name"] = full_name
        return jsonify({"success": True, "message": "Admin profile updated successfully."})
    return jsonify({"success": False, "message": "Failed to update profile."}), 400

@app.route("/api/camera/toggle", methods=["POST"])
@admin_required
def api_camera_toggle():
    if vision_engine.running:
        vision_engine.stop_camera()
        status = "stopped"
    else:
        vision_engine.start_camera()
        status = "started"
    return jsonify({"success": True, "status": status})

@app.route("/api/students/register", methods=["POST"])
@admin_required
def api_register_student():
    data = request.json or request.form
    name = data.get("name", "").strip()
    student_id = data.get("student_id", "").strip()
    department = data.get("department", "Computer Science").strip()
    email = data.get("email", "").strip()

    if not name or not student_id:
        return jsonify({"success": False, "message": "Student Name and Student ID are required."}), 400

    success, msg = vision_engine.capture_and_register_face(
        student_name=name,
        student_id=student_id,
        department=department,
        email=email
    )
    return jsonify({"success": success, "message": msg})

@app.route("/api/students/<int:stu_id>", methods=["DELETE"])
@admin_required
def api_delete_student(stu_id):
    success = db.delete_student(stu_id)
    if success:
        return jsonify({"success": True, "message": "Student removed successfully."})
    return jsonify({"success": False, "message": "Could not delete student."}), 400

@app.route("/api/attendance/mark_manual", methods=["POST"])
@admin_required
def api_mark_manual():
    data = request.json or request.form
    student_id = data.get("student_id")
    status = data.get("status", "Present")
    remarks = data.get("remarks", "Manual entry by Admin")

    if not student_id:
        return jsonify({"success": False, "message": "Student ID required."}), 400

    success, msg = db.mark_manual_attendance(student_id, status=status, remarks=remarks)
    return jsonify({"success": success, "message": msg})

@app.route("/api/attendance/export_csv")
@admin_required
def api_export_csv():
    date_filter = request.args.get("date", None)
    records = db.get_attendance_logs(date=date_filter)

    output = io.StringIO()
    writer = csv.writer(output)

    # Timestamped Header row with complete Join & Exit Timings
    writer.writerow([
        "Record ID",
        "Student ID",
        "Student Name",
        "Date",
        "Join Timestamp",
        "Check-In Timestamp",
        "Last Seen Timestamp",
        "Exit Timestamp",
        "Session Duration",
        "Session Duration (Seconds)",
        "Status",
        "Attentiveness Average (%)",
        "Drowsiness Detected",
        "Remarks",
        "Created At"
    ])

    for r in records:
        writer.writerow([
            r.get("id", ""),
            r.get("student_id", ""),
            r.get("student_name", ""),
            r.get("log_date", ""),
            r.get("join_time", "") or r.get("check_in_time", ""),
            r.get("check_in_time", ""),
            r.get("last_seen_time", ""),
            r.get("exit_time", "") or r.get("last_seen_time", ""),
            r.get("duration_formatted", "") or f"{r.get('duration_seconds', 0)}s",
            r.get("duration_seconds", 0),
            r.get("attendance_status", "") or r.get("status", "Present"),
            r.get("attentiveness_avg", 100.0),
            "YES" if r.get("drowsiness_detected") else "NO",
            r.get("remarks", ""),
            r.get("created_at", "")
        ])

    output.seek(0)
    filename = f"Classroom_Attendance_{date_filter or datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.route("/api/settings/mysql_test", methods=["POST"])
@admin_required
def api_mysql_test():
    data = request.json or {}
    host = data.get("host", "localhost")
    port = int(data.get("port", 3306))
    user = data.get("user", "root")
    password = data.get("password", "")
    database = data.get("database", "smart_class_db")

    success, msg = db.test_mysql_connection(host, port, user, password, database)
    return jsonify({"success": success, "message": msg})

@app.route("/data/photos/<path:filename>")
@admin_required
def serve_photo(filename):
    photos_dir = config.get("STUDENT_PHOTOS_DIR", os.path.join(BASE_DIR, "data", "photos"))
    return send_file(os.path.join(photos_dir, filename))

if __name__ == "__main__":
    port = 5000
    print("=" * 60)
    print("SMART CLASSROOM MONITORING SYSTEM")
    print(f"Backend Server starting on http://127.0.0.1:{port}")
    print("=" * 60)
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
