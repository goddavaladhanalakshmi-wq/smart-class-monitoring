import unittest
import sqlite3
import os
import sys

from database import get_db

class TestAnalyticsValidation(unittest.TestCase):
    def setUp(self):
        self.db = get_db()

    def test_01_attendance_percentage_within_bounds(self):
        """Requirement 1: Attendance percentage must never exceed 100%."""
        summary = self.db.get_student_reports_summary()
        self.assertIn("students_summary", summary)
        for s in summary["students_summary"]:
            pct = s["attendance_percentage"]
            self.assertGreaterEqual(pct, 0.0, f"Percentage for {s['name']} is negative: {pct}")
            self.assertLessEqual(pct, 100.0, f"Percentage for {s['name']} exceeded 100%: {pct}")

    def test_02_attended_classes_within_completed_sessions(self):
        """Requirement 2: Calculate attendance using unique completed class sessions."""
        summary = self.db.get_student_reports_summary()
        total_classes = summary["total_classes"]
        for s in summary["students_summary"]:
            attended = s["attended_classes"]
            self.assertLessEqual(attended, total_classes,
                f"Student {s['name']} attended {attended} classes but only {total_classes} completed sessions exist.")

    def test_03_only_valid_sessions_counted(self):
        """Requirement 3: Only count attendance records belonging to valid class sessions."""
        logs = self.db.get_attendance_logs(only_valid_sessions=True)
        for r in logs:
            self.assertIsNotNone(r.get("session_id"), f"Log record {r['id']} has NULL session_id.")

    def test_04_duration_not_exceeding_session(self):
        """Requirement 4 & 6: Duration calculated from join/exit and never exceeds session duration."""
        summary = self.db.get_student_reports_summary()
        for s in summary["students_summary"]:
            dur_sec = s["total_duration_seconds"]
            # 22 hours = 79,200 seconds; total duration must be reasonable class time (< 5 hours)
            self.assertLess(dur_sec, 18000,
                f"Student {s['name']} total duration {dur_sec}s indicates unconstrained test leakage.")

    def test_05_no_database_deletion(self):
        """Requirement 8: Database records are preserved (not automatically deleted)."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM attendance_records")
            row = cursor.fetchone()
            total_records = row[0] if isinstance(row, (tuple, list)) else row["COUNT(*)"]
            # We know the database had at least 16 records
            self.assertGreaterEqual(total_records, 16, "Database rows were unexpectedly deleted.")
        finally:
            conn.close()

if __name__ == "__main__":
    unittest.main()
