from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PatientBase(BaseModel):
    patient_id: int
    acuity_level: int
    department: str

class Patient(PatientBase):
    id: int
    arrival_time: Optional[datetime] = None

    class Config:
        from_attributes = True # This allows Pydantic to read SQLAlchemy models
