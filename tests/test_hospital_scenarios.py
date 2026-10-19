import unittest

from app.staffing_forecast import forecast_staffing_demand


def weekly_history(er_arrivals, icu_arrivals):
    records = []
    for day in ("2026-10-04", "2026-10-11"):
        for department, count in (("ER", er_arrivals), ("ICU", icu_arrivals)):
            records.extend({
                "arrival_time": f"{day}T10:15:00Z",
                "department": department,
            } for _ in range(count))
    return records


def forecast(records, department=None):
    return forecast_staffing_demand(
        records, hours_ahead=1, patients_per_staff=4, department=department,
        now="2026-10-18T09:00:00Z",
    )


class HospitalScenarioTests(unittest.TestCase):
    def test_quiet_and_peak_sundays_scale_forecast_and_staffing(self):
        quiet = forecast(weekly_history(er_arrivals=1, icu_arrivals=1), "ER")
        peak = forecast(weekly_history(er_arrivals=8, icu_arrivals=1), "ER")

        self.assertEqual(quiet["predicted_patient_arrivals"], [1.0])
        self.assertEqual(quiet["recommended_staff"], [1])
        self.assertEqual(peak["predicted_patient_arrivals"], [8.0])
        self.assertEqual(peak["recommended_staff"], [2])

    def test_department_scenarios_use_their_own_arrival_history(self):
        records = weekly_history(er_arrivals=8, icu_arrivals=2)
        emergency = forecast(records, "ER")
        intensive_care = forecast(records, "ICU")

        self.assertEqual(emergency["predicted_patient_arrivals"], [8.0])
        self.assertEqual(intensive_care["predicted_patient_arrivals"], [2.0])
        self.assertGreater(emergency["recommended_staff"][0], intensive_care["recommended_staff"][0])

    def test_hospital_wide_forecast_matches_combined_departments(self):
        result = forecast(weekly_history(er_arrivals=8, icu_arrivals=2))
        self.assertEqual(result["predicted_patient_arrivals"], [10.0])
        self.assertIsNone(result["department"])


if __name__ == "__main__":
    unittest.main()