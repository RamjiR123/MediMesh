import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.routers.health import database_health_check, readiness_check, system_metrics


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

    def test_database_health_reports_existing_tables(self):
        result = database_health_check(self.session)
        self.assertEqual(result["status"], "healthy")
        self.assertTrue(result["tables_exist"])
        self.assertTrue(all(result["table_status"].values()))

    def test_database_health_reports_missing_tables(self):
        models.Base.metadata.drop_all(bind=self.engine)
        result = database_health_check(self.session)
        self.assertEqual(result["status"], "unhealthy")
        self.assertFalse(result["tables_exist"])
        self.assertFalse(any(result["table_status"].values()))

    def test_database_health_identifies_each_missing_table(self):
        required_tables = ("patients", "doctors", "beds", "appointments", "staff")
        for table in required_tables:
            with self.subTest(table=table):
                models.Base.metadata.drop_all(bind=self.engine)
                models.Base.metadata.create_all(bind=self.engine)
                models.Base.metadata.tables[table].drop(bind=self.engine)
                result = database_health_check(self.session)
                self.assertFalse(result["table_status"][table])

    def test_readiness_reports_required_table_state(self):
        self.assertEqual(readiness_check(self.session)["status"], "ready")
        models.Base.metadata.tables["beds"].drop(bind=self.engine)
        result = readiness_check(self.session)
        self.assertEqual(result["status"], "not ready")
        self.assertIn("beds", result["reason"])

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

    def test_metrics_handle_missing_values_without_crashing(self):
        result = system_metrics(self.session)
        self.assertEqual(result["metrics"]["bed_occupancy_rate"], 0)
        self.assertEqual(result["metrics"]["doctor_availability_rate"], 0)
        self.assertEqual(result["metrics"]["recent_patients_24h"], 0)
        self.assertEqual(result["metrics"]["upcoming_appointments_24h"], 0)
        self.assertEqual(result["metrics"]["bed_occupancy_by_department"], [])
        self.assertEqual(result["metrics"]["doctor_availability_by_department"], [])
        self.assertEqual(result["alerts"], [])

    def test_metrics_include_department_bed_occupancy(self):
        self.session.add_all([
            models.Bed(
                bed_number="C-1",
                department="Cardiology",
                is_occupied=True,
            ),
            models.Bed(
                bed_number="C-2",
                department="Cardiology",
                is_occupied=False,
            ),
            models.Bed(
                bed_number="I-1",
                department="ICU",
                is_occupied=True,
            ),
        ])
        self.session.commit()

        result = system_metrics(self.session)

        self.assertEqual(
            result["metrics"]["bed_occupancy_by_department"],
            [
                {
                    "department": "Cardiology",
                    "total_beds": 2,
                    "occupied_beds": 1,
                    "occupancy_rate": 50.0,
                },
                {
                    "department": "ICU",
                    "total_beds": 1,
                    "occupied_beds": 1,
                    "occupancy_rate": 100.0,
                },
            ],
        )

    def test_metrics_include_department_doctor_availability(self):
        self.session.add_all([
            models.Doctor(doctor_id="D-1", name="A", department="Cardiology", is_available=True),
            models.Doctor(doctor_id="D-2", name="B", department="Cardiology", is_available=False),
            models.Doctor(doctor_id="D-3", name="C", department="ICU", is_available=False),
        ])
        self.session.commit()

        result = system_metrics(self.session)

        departments = result["metrics"]["doctor_availability_by_department"]
        self.assertEqual([row["department"] for row in departments], ["Cardiology", "ICU"])
        self.assertEqual([row["total_doctors"] for row in departments], [2, 1])
        self.assertEqual([row["available_doctors"] for row in departments], [1, 0])
        self.assertEqual([row["availability_rate"] for row in departments], [50.0, 0.0])

    def test_alert_builder_rejects_invalid_numeric_inputs(self):
        from app.operational_alerts import build_operational_alerts

        alerts = build_operational_alerts({
            "bed_occupancy_rate": None,
            "total_doctors": 0,
            "doctor_availability_rate": "not-a-number",
            "recent_patients_24h": "bad",
            "upcoming_appointments_24h": float("nan"),
        })
        self.assertEqual(alerts, [])


if __name__ == "__main__":
    unittest.main()