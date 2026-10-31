import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.routers.health import system_metrics


class HealthAppointmentMetricsTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        models.Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def add_appointments(self, rows):
        now = datetime.utcnow()
        self.session.add_all([
            models.Appointment(
                appointment_id=appointment_id,
                status=status,
                scheduled_time=now + timedelta(hours=offset),
            )
            for appointment_id, status, offset in rows
        ])
        self.session.commit()

    def test_metrics_only_count_scheduled_appointments_in_next_day(self):
        self.add_appointments([
            ("in-window", "scheduled", 12),
            ("cancelled", "cancelled", 12),
            ("completed", "completed", 12),
            ("too-late", "scheduled", 25),
            ("past", "scheduled", -1),
        ])
        result = system_metrics(self.session)
        metrics = result["metrics"]
        self.assertEqual(metrics["total_appointments"], 5)
        self.assertEqual(metrics["upcoming_appointments_24h"], 1)
        self.assertFalse(any(alert["metric"] == "upcoming_appointments_24h" for alert in result["alerts"]))

    def test_metrics_emit_volume_alert_at_threshold(self):
        self.add_appointments([
            (f"appointment-{index}", "scheduled", 12) for index in range(30)
        ])
        result = system_metrics(self.session)
        alert = next(alert for alert in result["alerts"]
                     if alert["metric"] == "upcoming_appointments_24h")
        self.assertEqual(result["metrics"]["upcoming_appointments_24h"], 30)
        self.assertEqual(alert["level"], "warning")

    def test_empty_database_returns_zero_upcoming_appointments(self):
        result = system_metrics(self.session)
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["metrics"]["upcoming_appointments_24h"], 0)
        self.assertEqual(result["alerts"], [])


if __name__ == "__main__":
    unittest.main()