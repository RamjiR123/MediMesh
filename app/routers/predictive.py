from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import pandas as pd

from app.database import get_db
from app import models
from app.ml_models import predictive_service

router = APIRouter(prefix="/predictive", tags=["Predictive"])

class PatientPredictionInput(BaseModel):
    patient_id: Optional[int] = Field(None, description="External patient identifier")
    arrival_time: Optional[str] = Field(None, description="Timestamp of patient arrival")
    acuity_level: int = Field(..., ge=1, le=5, description="Acuity level from 1 to 5")
    department: str = Field(..., description="ER, ICU, or General")

    class Config:
        schema_extra = {
            "example": {
                "patient_id": 42,
                "arrival_time": "2026-04-03T15:30:00Z",
                "acuity_level": 3,
                "department": "ER"
            }
        }

class PredictInitResponse(BaseModel):
    success: bool
    trained_models: List[str]
    message: str

class PredictERResponse(BaseModel):
    predicted_wait_time: float
    min_wait_time: float
    max_wait_time: float

class OccupancyForecastResponse(BaseModel):
    predicted_occupancy: List[float]
    timestamps: List[str]

@router.post("/init", response_model=PredictInitResponse)
def initialize_predictive_models(db: Session = Depends(get_db)):
    """Train predictive models using existing patient data"""
    patients = db.query(models.Patient).all()
    if not patients:
        raise HTTPException(status_code=404, detail="No patients available for model training")

    patient_rows = [
        {
            "patient_id": patient.patient_id,
            "arrival_time": patient.arrival_time,
            "acuity_level": patient.acuity_level,
            "department": patient.department,
        }
        for patient in patients
    ]

    df = pd.DataFrame(patient_rows)
    predictive_service.initialize_models(df)

    return PredictInitResponse(
        success=True,
        trained_models=["er_wait_time", "bed_occupancy"],
        message="Predictive models trained successfully using current patient history"
    )

@router.post("/er-wait", response_model=PredictERResponse)
def predict_er_wait_time(input: PatientPredictionInput):
    """Predict ER wait time for a single patient"""
    if not predictive_service.is_initialized:
        raise HTTPException(status_code=400, detail="Predictive models are not initialized")

    patient_data = pd.DataFrame([input.dict()])
    prediction = predictive_service.predict_er_wait_time(patient_data)
    return PredictERResponse(**prediction)

@router.get("/bed-occupancy", response_model=OccupancyForecastResponse)
def predict_bed_occupancy(hours_ahead: int = 24):
    """Predict future bed occupancy percentages"""
    if not predictive_service.is_initialized:
        raise HTTPException(status_code=400, detail="Predictive models are not initialized")
    if hours_ahead < 1 or hours_ahead > 72:
        raise HTTPException(status_code=422, detail="hours_ahead must be between 1 and 72")

    forecast = predictive_service.predict_bed_occupancy(hours_ahead)
    return OccupancyForecastResponse(**forecast)

@router.get("/status")
def predictive_status() -> Dict[str, object]:
    """Check whether predictive models are loaded"""
    return {
        "initialized": predictive_service.is_initialized,
        "available_models": ["er_wait_time", "bed_occupancy"]
    }
