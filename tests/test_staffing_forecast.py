import unittest

from app.staffing_forecast import forecast_staffing_demand


class StaffingForecastTests(unittest.TestCase):
    def test_repeats_weekday_hour_volume_and_calculates_staff(self):
        patients = [
            {"arrival_time": "2026-10-04T10:05:00Z", "department": "ER"},
            {"arrival_time": "2026-10-04T10:25:00Z", "department": "ER"},
            {"arrival_time": "2026-10-11T10:15:00Z", "department": "ER"},
        ]
        result = forecast_staffing_demand(
            patients, hours_ahead=1, patients_per_staff=2,
            department="ER", now="2026-10-11T09:00:00Z",
        )
        self.assertEqual(result["predicted_patient_arrivals"], [1.5])
        self.assertEqual(result["recommended_staff"], [1])

    def test_rejects_empty_arrival_history(self):
        with self.assertRaisesRegex(ValueError, "No valid arrivals"):
            forecast_staffing_demand([], now="2026-10-11T09:00:00Z")

    def test_department_filter_is_case_insensitive(self):
        patients = [
            {"arrival_time": "2026-10-04T10:15:00Z", "department": "ER"},
            *[{"arrival_time": "2026-10-04T10:20:00Z", "department": "ICU"} for _ in range(4)],
        ]
        result = forecast_staffing_demand(
            patients, hours_ahead=1, department="er", now="2026-10-04T09:00:00Z",
        )
        self.assertEqual(result["predicted_patient_arrivals"], [1.0])
        self.assertEqual(result["department"], "er")

    def test_department_without_history_is_rejected(self):
        patients = [{"arrival_time": "2026-10-04T10:15:00Z", "department": "ER"}]
        with self.assertRaisesRegex(ValueError, "No valid arrivals"):
            forecast_staffing_demand(patients, department="ICU", now="2026-10-04T09:00:00Z")

    def test_rejects_out_of_range_horizon_and_staff_ratio(self):
        patients = [{"arrival_time": "2026-10-04T10:15:00Z", "department": "ER"}]
        for options in ({"hours_ahead": 0}, {"hours_ahead": 73}, {"patients_per_staff": 0}):
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, "must be 1-72"):
                forecast_staffing_demand(patients, now="2026-10-04T09:00:00Z", **options)

    def test_ignores_invalid_arrival_timestamps(self):
        patients = [{"arrival_time": "not-a-date", "department": "ER"}]
        with self.assertRaisesRegex(ValueError, "No valid arrivals"):
            forecast_staffing_demand(patients, now="2026-10-04T09:00:00Z")

    def test_department_is_optional_for_unfiltered_history(self):
        patients = [{"arrival_time": "2026-10-04T10:15:00Z"}]
        result = forecast_staffing_demand(patients, hours_ahead=1, now="2026-10-04T09:00:00Z")
        self.assertEqual(result["predicted_patient_arrivals"], [1.0])
        self.assertIsNone(result["department"])

    def test_accepts_naive_arrival_and_forecast_timestamps(self):
        patients = [{"arrival_time": "2026-10-04 10:15:00", "department": "ER"}]
        result = forecast_staffing_demand(patients, hours_ahead=1, now="2026-10-04 09:00:00")
        self.assertEqual(result["predicted_patient_arrivals"], [1.0])
        self.assertTrue(result["timestamps"][0].endswith("+00:00"))

    def test_falls_back_to_hourly_average_when_weekday_is_unseen(self):
        patients = [
            {"arrival_time": "2026-10-04T09:15:00Z", "department": "ER"},
            {"arrival_time": "2026-10-05T10:15:00Z", "department": "ER"},
        ]
        result = forecast_staffing_demand(
            patients, hours_ahead=1, now="2026-10-06T09:00:00Z",
        )
        self.assertEqual(result["predicted_patient_arrivals"], [0.5])

    def test_forecast_has_one_staff_estimate_per_requested_hour(self):
        patients = [{"arrival_time": "2026-10-04T10:15:00Z", "department": "ER"} for _ in range(5)]
        result = forecast_staffing_demand(
            patients, hours_ahead=3, patients_per_staff=2, now="2026-10-04T09:00:00Z",
        )
        self.assertEqual(len(result["timestamps"]), 3)
        self.assertEqual(result["recommended_staff"], [3, 0, 0])


if __name__ == "__main__":
    unittest.main()