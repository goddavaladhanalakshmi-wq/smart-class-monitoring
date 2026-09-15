import unittest
import json
from app import app
from database import get_db
from vision_engine import get_vision_engine

class TestSmartClassMonitoring(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.db = get_db()
        self.vision = get_vision_engine()
        self.vision.simulation_mode = True

    def tearDown(self):
        # Stop background camera capture thread to ensure clean process termination
        if self.vision.running:
            self.vision.stop_camera()

    def test_01_login_page_renders(self):
        """Verify Admin login page renders with status 200."""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SmartClass Monitor", response.data)
        self.assertIn(b"Admin Username", response.data)

    def test_02_unauthenticated_redirect(self):
        """Verify unauthenticated user cannot access /dashboard and is redirected to /login."""
        response = self.app.get('/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_03_admin_login_success(self):
        """Verify logging in with default credentials creates session."""
        response = self.app.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Live Classroom Camera Stream", response.data)

    def test_04_authenticated_pages_render(self):
        """Verify all pages render successfully when logged in."""
        with self.app.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_id'] = 1
            sess['admin_username'] = 'admin'
            sess['admin_name'] = 'Administrator'

        # Test Dashboard / Monitor
        resp = self.app.get('/dashboard')
        self.assertEqual(resp.status_code, 200)

        # Test Attendance Logs
        resp = self.app.get('/attendance')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Attendance Records & Timestamps", resp.data)

        # Test Students Roster
        resp = self.app.get('/students')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Enrolled Students Directory", resp.data)

        # Test Analytics
        resp = self.app.get('/analytics')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Classroom Attendance & Engagement Analytics", resp.data)

        # Test Settings
        resp = self.app.get('/settings')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"MySQL Database Connection", resp.data)

    def test_05_api_live_stats(self):
        """Verify /api/live_stats returns telemetry and database stats with server timestamp."""
        with self.app.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_id'] = 1
            sess['admin_username'] = 'admin'

        resp = self.app.get('/api/live_stats')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("server_time", data)
        self.assertIn("telemetry", data)
        self.assertIn("db_stats", data)
        print("\n[TEST] API Live Stats Response:", data["server_time"], data["db_stats"])

    def test_06_manual_attendance_and_csv_export(self):
        """Verify marking attendance and exporting timestamped CSV."""
        with self.app.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_id'] = 1
            sess['admin_username'] = 'admin'

        # Mark manual attendance for ESASAI
        students = self.db.get_all_students()
        self.assertGreater(len(students), 0)
        stu = students[0]

        resp = self.app.post('/api/attendance/mark_manual', json={
            'student_id': stu['student_id'],
            'status': 'Present',
            'remarks': 'Unit Test Verification'
        })
        self.assertEqual(resp.status_code, 200)
        res = json.loads(resp.data)
        self.assertTrue(res['success'])

        # Export CSV
        resp = self.app.get('/api/attendance/export_csv')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'text/csv')
        self.assertIn(b"Check-In Timestamp", resp.data)
        self.assertIn(b"Last Seen Timestamp", resp.data)
        self.assertIn(b"Join Timestamp", resp.data)
        self.assertIn(b"Exit Timestamp", resp.data)
        print("[TEST] CSV Export verified with Check-In, Join, and Exit timestamp columns.")

    def test_07_react_portal_renders(self):
        """Verify React UI Single Page Application renders at / and /react."""
        resp = self.app.get('/react')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"react_app.jsx", resp.data)
        self.assertIn(b"SmartClass Monitor", resp.data)

        resp2 = self.app.get('/')
        self.assertEqual(resp2.status_code, 200)
        self.assertIn(b"react_app.jsx", resp2.data)
        print("[TEST] React UI Single Page Application rendered successfully.")

    def test_08_admin_auth_api(self):
        """Verify JSON API authentication for the React UI."""
        # Bad login
        resp = self.app.post('/api/auth/login', json={'username': 'admin', 'password': 'wrongpassword'})
        self.assertEqual(resp.status_code, 401)

        # Good login
        resp = self.app.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['success'])
        self.assertIn('admin', data)

        # Auth check
        resp = self.app.get('/api/auth/check')
        self.assertEqual(resp.status_code, 200)
        chk = json.loads(resp.data)
        self.assertTrue(chk['authenticated'])

        # Logout
        resp = self.app.post('/api/auth/logout')
        self.assertEqual(resp.status_code, 200)
        print("[TEST] Admin JSON Auth API verified.")

    def test_09_class_session_lifecycle(self):
        """Verify Admin joining and ending class session with automated exit timing sealing."""
        with self.app.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_id'] = 1

        # Start session
        resp = self.app.post('/api/session/start', json={'title': 'Computer Vision Lecture'})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['session']['title'], 'Computer Vision Lecture')

        # Check active session
        resp = self.app.get('/api/session/active')
        self.assertEqual(resp.status_code, 200)
        act = json.loads(resp.data)
        self.assertIsNotNone(act['active_session'])

        # End session
        resp = self.app.post('/api/session/end', json={'session_id': act['active_session']['id']})
        self.assertEqual(resp.status_code, 200)
        end_data = json.loads(resp.data)
        self.assertTrue(end_data['success'])
        print("[TEST] Class session start and end lifecycle verified.")

    def test_10_attendance_join_and_exit_timings(self):
        """Verify storing and querying students' join and exit timings."""
        with self.app.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_id'] = 1

        students = self.db.get_all_students()
        stu = students[0]

        # Record presence (creates initial join_time)
        res = self.db.record_or_update_attendance(student_name=stu['name'], attentiveness=95.0, is_drowsy=False)
        self.assertIn('join_time', res)

        # Mark student exit
        resp = self.app.post('/api/attendance/mark_exit', json={'student_id': stu['student_id']})
        self.assertEqual(resp.status_code, 200)
        exit_res = json.loads(resp.data)
        self.assertTrue(exit_res['success'])

        # Query attendance logs via API
        resp = self.app.get('/api/attendance/list')
        self.assertEqual(resp.status_code, 200)
        logs_data = json.loads(resp.data)
        self.assertGreater(len(logs_data['records']), 0)
        record = logs_data['records'][0]
        self.assertIn('join_time', record)
        self.assertIn('exit_time', record)
        self.assertIn('duration_formatted', record)
        print(f"[TEST] Verified student join time: {record['join_time']}, exit time: {record['exit_time']}, duration: {record['duration_formatted']}")

if __name__ == '__main__':
    unittest.main()
