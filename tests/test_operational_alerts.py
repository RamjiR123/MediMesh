import unittest

from app.operational_alerts import build_operational_alerts, sort_alerts, summarize_alerts


class OperationalAlertsTests(unittest.TestCase):
    def test_sort_alerts_prioritizes_critical_before_warning(self):
        alerts = [
            {"level": "warning", "metric": "recent_patients_24h"},
            {"level": "critical", "metric": "bed_occupancy_rate"},
            {"level": "warning", "metric": "doctor_availability_rate"},
        ]
        ordered = sort_alerts(alerts)
        self.assertEqual([alert["metric"] for alert in ordered], [
            "bed_occupancy_rate",
            "doctor_availability_rate",
            "recent_patients_24h",
        ])

    def test_sort_alerts_uses_metric_name_as_tie_breaker(self):
        alerts = [
            {"level": "critical", "metric": "z_metric"},
            {"level": "critical", "metric": "a_metric"},
        ]
        self.assertEqual(
            [alert["metric"] for alert in sort_alerts(alerts)],
            ["a_metric", "z_metric"],
        )

    def test_sort_alerts_ignores_non_dictionary_entries(self):
        alerts = [{"level": "warning", "metric": "patient_volume"}, None, "invalid"]
        self.assertEqual(sort_alerts(alerts), [alerts[0]])

    def test_sort_alerts_handles_unknown_levels_last(self):
        alerts = [
            {"level": "info", "metric": "status"},
            {"level": "warning", "metric": "volume"},
        ]
        self.assertEqual([alert["level"] for alert in sort_alerts(alerts)], ["warning", "info"])

    def test_summarize_alerts_counts_all_severity_levels(self):
        alerts = [
            {"level": "critical"},
            {"level": "warning"},
            {"level": "warning"},
        ]
        self.assertEqual(summarize_alerts(alerts), {
            "total": 3,
            "warning": 2,
            "critical": 1,
        })

    def test_build_operational_alerts_returns_sorted_output(self):
        alerts = build_operational_alerts({
            "bed_occupancy_rate": 95,
            "recent_patients_24h": 50,
            "upcoming_appointments_24h": 30,
        })
        levels = [alert["level"] for alert in alerts]
        self.assertEqual(levels, ["critical", "warning", "warning"])

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

    def test_upcoming_appointment_threshold_is_inclusive(self):
        alerts = build_operational_alerts({"upcoming_appointments_24h": 30})
        self.assertEqual(alerts[0]["metric"], "upcoming_appointments_24h")
        self.assertEqual(alerts[0]["level"], "warning")

    def test_upcoming_appointment_below_threshold_does_not_alert(self):
        self.assertEqual(build_operational_alerts({"upcoming_appointments_24h": 29}), [])

    def test_upcoming_appointments_remain_warning_below_critical(self):
        alerts = build_operational_alerts({"upcoming_appointments_24h": 59})
        self.assertEqual(alerts[0]["level"], "warning")

    def test_appointment_alert_escalates_to_critical(self):
        alerts = build_operational_alerts({"upcoming_appointments_24h": 60})
        self.assertEqual(alerts[0]["level"], "critical")
        self.assertEqual(alerts[0]["value"], 60)

    def test_zero_or_missing_appointments_do_not_alert(self):
        self.assertEqual(build_operational_alerts({"upcoming_appointments_24h": 0}), [])
        self.assertEqual(build_operational_alerts({}), [])

    def test_appointment_alert_includes_current_count(self):
        alert = build_operational_alerts({"upcoming_appointments_24h": 35})[0]
        self.assertIn("35 appointments", alert["message"])

    def test_appointment_and_patient_volume_alerts_coexist(self):
        metrics = {"upcoming_appointments_24h": 30, "recent_patients_24h": 50}
        alerts = build_operational_alerts(metrics)
        self.assertEqual({alert["metric"] for alert in alerts}, {
            "upcoming_appointments_24h", "recent_patients_24h",
        })


if __name__ == "__main__":
    unittest.main()