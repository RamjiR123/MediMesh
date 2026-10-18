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


if __name__ == "__main__":
    unittest.main()