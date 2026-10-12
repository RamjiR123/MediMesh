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


if __name__ == "__main__":
    unittest.main()