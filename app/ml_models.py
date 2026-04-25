import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import logging

logger = logging.getLogger(__name__)

class ERWaitTimePredictor:
    """Predict ER wait times using Random Forest regression"""

    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.train_metrics = {}

    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess patient data for modeling"""
        df_processed = df.copy()

        # Extract time features
        if 'arrival_time' in df_processed.columns:
            df_processed['arrival_time'] = pd.to_datetime(df_processed['arrival_time'])
            df_processed['hour'] = df_processed['arrival_time'].dt.hour
            df_processed['day_of_week'] = df_processed['arrival_time'].dt.dayofweek
            df_processed['is_weekend'] = df_processed['day_of_week'].isin([5, 6]).astype(int)

        # Encode department
        dept_mapping = {'ER': 0, 'ICU': 1, 'General': 2}
        df_processed['department_encoded'] = df_processed['department'].map(dept_mapping).fillna(-1)

        return df_processed

    def train(self, df: pd.DataFrame):
        """Train the ER wait time prediction model"""
        try:
            logger.info("Training ER wait time prediction model...")

            # Preprocess data
            df_processed = self.preprocess_data(df)

            # Create synthetic target (wait time in minutes)
            np.random.seed(42)
            df_processed['wait_time'] = (
                np.random.exponential(scale=20, size=len(df_processed)) +
                df_processed['acuity_level'] * 15 +
                df_processed['hour'].apply(lambda x: 10 if 18 <= x <= 22 else 0)  # Peak hours
            )

            # Features for prediction
            feature_cols = ['acuity_level', 'hour', 'day_of_week', 'is_weekend', 'department_encoded']
            X = df_processed[feature_cols]
            y = df_processed['wait_time']

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train model
            self.model.fit(X_train_scaled, y_train)
            self.is_trained = True

            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            self.train_metrics = {
                "trained_samples": len(df_processed),
                "mae": float(mae),
                "rmse": float(rmse)
            }

            logger.info(f"Model trained successfully - MAE: {mae:.2f} min, RMSE: {rmse:.2f} min")

        except Exception as e:
            logger.error(f"Failed to train ER wait time model: {e}")
            raise

    def predict(self, patient_data: pd.DataFrame) -> Dict[str, float]:
        """Predict wait time for new patient data"""
        if not self.is_trained:
            raise ValueError("Model not trained yet")

        try:
            # Preprocess input data
            df_processed = self.preprocess_data(patient_data)

            # Prepare features
            feature_cols = ['acuity_level', 'hour', 'day_of_week', 'is_weekend', 'department_encoded']
            X = df_processed[feature_cols]
            X_scaled = self.scaler.transform(X)

            # Make predictions
            predictions = self.model.predict(X_scaled)

            return {
                'predicted_wait_time': float(np.mean(predictions)),
                'min_wait_time': float(np.min(predictions)),
                'max_wait_time': float(np.max(predictions)),
                'confidence_range': float(np.std(predictions) * 1.96)  # 95% confidence interval
            }

        except Exception as e:
            logger.error(f"Failed to predict wait time: {e}")
            raise

class BedOccupancyPredictor:
    """Simple bed occupancy prediction using historical averages"""

    def __init__(self):
        self.hourly_patterns = {}
        self.is_trained = False
        self.train_samples = 0

    def train(self, df: pd.DataFrame):
        """Train bed occupancy patterns"""
        try:
            logger.info("Training bed occupancy prediction model...")

            df_processed = df.copy()
            df_processed['arrival_time'] = pd.to_datetime(df_processed['arrival_time'])
            df_processed['hour'] = df_processed['arrival_time'].dt.hour

            # Calculate average occupancy by hour
            hourly_stats = df_processed.groupby('hour').agg({
                'patient_id': 'count'
            }).reset_index()

            # Assume max capacity of 50 beds
            hourly_stats['occupancy_rate'] = (hourly_stats['patient_id'] / 50) * 100
            hourly_stats['occupancy_rate'] = hourly_stats['occupancy_rate'].clip(0, 100)

            self.hourly_patterns = dict(zip(hourly_stats['hour'], hourly_stats['occupancy_rate']))
            self.is_trained = True
            self.train_samples = len(df_processed)

            logger.info("Bed occupancy model trained successfully")

        except Exception as e:
            logger.error(f"Failed to train bed occupancy model: {e}")
            raise

    def predict(self, hours_ahead: int = 24) -> Dict[str, List[float]]:
        """Predict bed occupancy for next hours"""
        if not self.is_trained:
            raise ValueError("Model not trained yet")

        try:
            current_hour = datetime.now().hour
            predictions = []

            for i in range(hours_ahead):
                hour = (current_hour + i) % 24
                occupancy = self.hourly_patterns.get(hour, 50.0)  # Default to 50% if no data
                predictions.append(occupancy)

            return {
                'predicted_occupancy': predictions,
                'timestamps': [(datetime.now() + timedelta(hours=i)).isoformat()
                             for i in range(hours_ahead)]
            }

        except Exception as e:
            logger.error(f"Failed to predict bed occupancy: {e}")
            raise

class PredictiveAnalyticsService:
    """Service for hospital predictive analytics"""

    def __init__(self):
        self.er_predictor = ERWaitTimePredictor()
        self.bed_predictor = BedOccupancyPredictor()
        self.is_initialized = False
        self.training_summary = {}

    def initialize_models(self, patient_data: pd.DataFrame):
        """Initialize and train prediction models"""
        try:
            logger.info("Initializing predictive analytics models...")

            self.er_predictor.train(patient_data)
            self.bed_predictor.train(patient_data)
            self.training_summary = {
                "er_wait_time": self.er_predictor.train_metrics,
                "bed_occupancy": {
                    "trained_samples": self.bed_predictor.train_samples
                }
            }

            self.is_initialized = True
            logger.info("Predictive models initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
            raise

    def retrain_models(self, patient_data: pd.DataFrame):
        """Retrain prediction models with fresh patient history"""
        self.is_initialized = False
        self.initialize_models(patient_data)
        return self.training_summary

    def get_training_summary(self) -> Dict[str, object]:
        if not self.is_initialized:
            raise ValueError("Models not initialized")
        return self.training_summary

    def predict_er_wait_time(self, patient_data: pd.DataFrame) -> Dict[str, float]:
        """Predict ER wait time"""
        if not self.is_initialized:
            raise ValueError("Models not initialized")
        return self.er_predictor.predict(patient_data)

    def predict_bed_occupancy(self, hours_ahead: int = 24) -> Dict[str, List[float]]:
        """Predict bed occupancy"""
        if not self.is_initialized:
            raise ValueError("Models not initialized")
        return self.bed_predictor.predict(hours_ahead)

# Global service instance
predictive_service = PredictiveAnalyticsService()