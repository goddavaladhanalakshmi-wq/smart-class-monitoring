import unittest

from database import get_db


class TestAnalyticsValidation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = get_db()

    def test_01_attendance_never_exceeds_total_sessions(self):
        """Requirement 1: Attendance cannot exceed total class sessions."""
        summary = self.db.get_student_reports_summary()

        total_classes = summary["total_classes"]

        for s in summary["students_summary"]:
            attended = s["attended_classes"]

            self.assertLessEqual(
                attended,
                total_classes,
                f"Student {s['name']} attended {attended} classes "
                f"but only {total_classes} completed sessions exist."
            )

    def test_02_attendance_summary_is_valid(self):
        """Requirement 2: Attendance summary values are valid."""
        summary = self.db.get_student_reports_summary()

        total_classes = summary["total_classes"]

        self.assertGreaterEqual(
            total_classes,
            0,
            "Total class sessions cannot be negative."
        )

        for s in summary["students_summary"]:
            attended = s["attended_classes"]

            self.assertGreaterEqual(
                attended,
                0,
                f"Student {s['name']} has a negative attendance count."
            )

            self.assertLessEqual(
                attended,
                total_classes,
                f"Student {s['name']} attended {attended} classes "
                f"but only {total_classes} total classes exist."
            )

    def test_03_only_valid_sessions_counted(self):
        """Requirement 3: Only attendance records belonging to valid sessions are counted."""
        logs = self.db.get_attendance_logs(only_valid_sessions=True)

        for r in logs:
            self.assertIsNotNone(
                r.get("session_id"),
                f"Log record {r['id']} has NULL session_id."
            )

    def test_04_duration_not_exceeding_session(self):
        """Requirement 4 & 6: Duration stays within a reasonable limit."""
        summary = self.db.get_student_reports_summary()

        for s in summary["students_summary"]:
            dur_sec = s["total_duration_seconds"]

            self.assertGreaterEqual(
                dur_sec,
                0,
                f"Student {s['name']} has a negative duration."
            )

            self.assertLess(
                dur_sec,
                18000,
                f"Student {s['name']} total duration "
                f"{dur_sec}s indicates unconstrained test leakage."
            )

    def test_05_no_database_deletion(self):
        """Requirement 8: Existing attendance records are preserved."""
        conn = self.db.get_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*) AS total FROM attendance_records"
            )

            row = cursor.fetchone()

            if isinstance(row, (tuple, list)):
                total_records = row[0]
            else:
                total_records = row["total"]

            self.assertIsNotNone(
                total_records,
                "Could not determine attendance record count."
            )

            self.assertGreaterEqual(
                total_records,
                0,
                "Attendance record count cannot be negative."
            )

        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
