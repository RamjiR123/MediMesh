import unittest

from app.operational_alerts import build_operational_alerts


class OperationalAlertsTests(unittest.TestCase):
    def test_healthy_metrics_return_no_alerts(self):
        metrics = {"bed_occupancy_rate": 89.99, "total_doctors": 10, "doctor_availability_rate": 10.01}
        self.assertEqual(build_operational_alerts(metrics), [])

    def test_occupancy_threshold_is_inclusive(self):
        alerts = build_operational_alerts({"bed_occupancy_rate": 90})
        self.assertEqual([alert["metric"] for alert in alerts], ["bed_occupancy_rate"])
        self.assertEqual(alerts[0]["level"], "critical")

    def test_low_doctor_availability_threshold_is_inclusive(self):
        metrics = {"total_doctors": 10, "doctor_availability_rate": 10}
        alerts = build_operational_alerts(metrics)
        self.assertEqual([alert["metric"] for alert in alerts], ["doctor_availability_rate"])
        self.assertEqual(alerts[0]["level"], "warning")

    def test_both_conditions_return_both_alerts(self):
        metrics = {"bed_occupancy_rate": 95, "total_doctors": 5, "doctor_availability_rate": 0}
        alerts = build_operational_alerts(metrics)
        self.assertEqual(len(alerts), 2)

    def test_high_patient_volume_threshold_is_inclusive(self):
        alerts = build_operational_alerts({"recent_patients_24h": 50})
        self.assertEqual([alert["metric"] for alert in alerts], ["recent_patients_24h"])
        self.assertEqual(alerts[0]["level"], "warning")

    def test_patient_volume_below_threshold_does_not_alert(self):
        alerts = build_operational_alerts({"recent_patients_24h": 49})
        self.assertEqual(alerts, [])

    def test_volume_alert_reports_the_arrival_count(self):
        alert = build_operational_alerts({"recent_patients_24h": 64})[0]
        self.assertEqual(alert["value"], 64)
        self.assertIn("64 arrivals", alert["message"])

    def test_volume_warning_escalates_at_critical_threshold(self):
        warning = build_operational_alerts({"recent_patients_24h": 99})
        critical = build_operational_alerts({"recent_patients_24h": 100})
        self.assertEqual(warning[0]["level"], "warning")
        self.assertEqual(critical[0]["level"], "critical")

    def test_missing_patient_volume_does_not_alert(self):
        self.assertEqual(build_operational_alerts({}), [])

    def test_zero_patient_volume_does_not_alert(self):
        self.assertEqual(build_operational_alerts({"recent_patients_24h": 0}), [])

    def test_negative_patient_volume_does_not_alert(self):
        self.assertEqual(build_operational_alerts({"recent_patients_24h": -1}), [])

    def test_volume_and_occupancy_alerts_can_coexist(self):
        metrics = {"recent_patients_24h": 60, "bed_occupancy_rate": 95}
        alerts = build_operational_alerts(metrics)
        self.assertEqual(len(alerts), 2)
        self.assertEqual({alert["metric"] for alert in alerts}, {
            "recent_patients_24h", "bed_occupancy_rate",
        })

    def test_all_three_operational_alerts_can_coexist(self):
        metrics = {
            "recent_patients_24h": 120, "bed_occupancy_rate": 95,
            "total_doctors": 10, "doctor_availability_rate": 0,
        }
        alerts = build_operational_alerts(metrics)
        self.assertEqual(len(alerts), 3)
        self.assertEqual({alert["level"] for alert in alerts}, {"warning", "critical"})


if __name__ == "__main__":
    unittest.main()