from pydantic import BaseModel
from datetime import datetime

class PatientBase(BaseModel):
    patient_id: int
    acuity_level: int
    department: str

class PatientOut(PatientBase):
    id: int
    arrival_time: datetime | None = None

    class Config:
        orm_mode = True