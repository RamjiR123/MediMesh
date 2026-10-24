import unittest

import pandas as pd

from app.ml_models import ERWaitTimePredictor


def sample_patients(count=12, observed=False):
    rows = []
    for index in range(count):
        row = {
            "arrival_time": f"2026-10-{index + 1:02d}T{index % 24:02d}:30:00Z",
            "acuity_level": index % 5 + 1,
            "department": ["ER", "ICU", "General"][index % 3],
        }
        if observed:
            row["wait_time_minutes"] = 12 + index * 3
        rows.append(row)
    return pd.DataFrame(rows)


class ERWaitPredictorTests(unittest.TestCase):
    def test_hour_features_are_continuous_across_midnight(self):
        patients = pd.DataFrame({
            "arrival_time": ["2026-10-18T23:45:00Z", "2026-10-19T00:15:00Z"],
            "acuity_level": [2, 2],
            "department": ["ER", "ER"],
        })
        features = ERWaitTimePredictor().preprocess_data(patients)
        difference = abs(features.loc[0, "hour_sin"] - features.loc[1, "hour_sin"])
        self.assertLess(difference, 0.2)
        self.assertEqual(features.loc[0, "department_er"], 1)

    def test_training_prefers_observed_wait_times_and_predicts(self):
        predictor = ERWaitTimePredictor()
        predictor.train(sample_patients(observed=True))
        prediction = predictor.predict(sample_patients(1))
        self.assertEqual(predictor.train_metrics["target_source"], "observed")
        self.assertEqual(predictor.train_metrics["trained_samples"], 12)
        self.assertGreater(prediction["predicted_wait_time"], 0)

    def test_fallback_labels_are_reported_as_synthetic(self):
        predictor = ERWaitTimePredictor()
        predictor.train(sample_patients())
        self.assertEqual(predictor.train_metrics["target_source"], "synthetic")

    def test_training_summary_ranks_feature_importance(self):
        predictor = ERWaitTimePredictor()
        predictor.train(sample_patients(observed=True))
        importance = predictor.train_metrics["feature_importance"]
        scores = [item["importance"] for item in importance]
        self.assertEqual(len(importance), len(predictor.feature_columns))
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertAlmostEqual(sum(scores), 1.0)

    def test_invalid_observed_labels_are_excluded(self):
        patients = sample_patients(observed=True)
        patients.loc[0, "wait_time_minutes"] = 0
        patients.loc[1, "wait_time_minutes"] = None
        predictor = ERWaitTimePredictor()
        predictor.train(patients)
        self.assertEqual(predictor.train_metrics["trained_samples"], 10)

    def test_training_rejects_fewer_than_two_valid_observations(self):
        predictor = ERWaitTimePredictor()
        with self.assertRaisesRegex(ValueError, "At least two valid"):
            predictor.train(sample_patients(1, observed=True))


if __name__ == "__main__":
    unittest.main()