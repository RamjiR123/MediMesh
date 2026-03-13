from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, validator


class DepartmentEnum(str, Enum):
    ER = "ER"
    ICU = "ICU"
    GENERAL = "General"


class AcuityLevelEnum(int, Enum):
    LOW = 1
    MODERATE = 2
    ELEVATED = 3
    HIGH = 4
    CRITICAL = 5


class PatientBase(BaseModel):
    patient_id: int = Field(..., description="External patient identifier")
    acuity_level: int = Field(..., ge=1, le=5, description="Acuity level from 1 (low) to 5 (critical)")
    department: DepartmentEnum = Field(..., description="Current department assignment")


class PatientCreate(PatientBase):
    arrival_time: Optional[datetime] = Field(
        default=None,
        description="Time the patient arrived at the hospital"
    )


class PatientUpdate(BaseModel):
    acuity_level: Optional[int] = Field(None, ge=1, le=5)
    department: Optional[DepartmentEnum] = None

    class Config:
        extra = "forbid"


class PatientOut(PatientBase):
    id: int
    arrival_time: Optional[datetime] = None

    class Config:
        orm_mode = True


class PatientListResponse(BaseModel):
    total: int
    items: List[PatientOut]


class MetricsSummary(BaseModel):
    total_patients: int
    er_count: int
    icu_count: int
    general_count: int
    average_acuity: Optional[float] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class TimeWindow(BaseModel):
    start: datetime
    end: datetime

    @validator("end")
    def validate_window(cls, v: datetime, values: dict) -> datetime:
        start = values.get("start")
        if start and v <= start:
            raise ValueError("end must be after start")
        return v

    @classmethod
    def last_hours(cls, hours: int = 24) -> "TimeWindow":
        now = datetime.utcnow()
        return cls(start=now - timedelta(hours=hours), end=now)


class DoctorBase(BaseModel):
    doctor_id: str = Field(..., description="Unique doctor identifier")
    name: str = Field(..., description="Doctor's full name")
    specialty: Optional[str] = Field(None, description="Medical specialty")
    department: DepartmentEnum = Field(..., description="Department assignment")


class DoctorCreate(DoctorBase):
    shift_start: Optional[datetime] = Field(None, description="Shift start time")
    shift_end: Optional[datetime] = Field(None, description="Shift end time")


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    department: Optional[DepartmentEnum] = None
    is_available: Optional[bool] = None
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None

    class Config:
        extra = "forbid"


class DoctorOut(DoctorBase):
    id: int
    is_available: bool
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None

    class Config:
        orm_mode = True


class BedBase(BaseModel):
    bed_number: str = Field(..., description="Unique bed identifier")
    department: DepartmentEnum = Field(..., description="Department location")
    room_type: str = Field(..., description="Type of room (ICU, General, etc.)")


class BedCreate(BedBase):
    last_cleaned: Optional[datetime] = Field(None, description="Last cleaning timestamp")


class BedUpdate(BaseModel):
    department: Optional[DepartmentEnum] = None
    is_occupied: Optional[bool] = None
    room_type: Optional[str] = None
    last_cleaned: Optional[datetime] = None

    class Config:
        extra = "forbid"


class BedOut(BedBase):
    id: int
    is_occupied: bool
    last_cleaned: Optional[datetime] = None

    class Config:
        orm_mode = True


class AppointmentStatusEnum(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no-show"


class AppointmentTypeEnum(str, Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow-up"
    PROCEDURE = "procedure"
    EMERGENCY = "emergency"


class AppointmentBase(BaseModel):
    appointment_id: str = Field(..., description="Unique appointment identifier")
    patient_id: int = Field(..., description="Patient ID")
    doctor_id: int = Field(..., description="Doctor ID")
    scheduled_time: datetime = Field(..., description="Scheduled appointment time")
    duration_minutes: int = Field(30, ge=1, description="Duration in minutes")
    appointment_type: AppointmentTypeEnum = Field(..., description="Type of appointment")


class AppointmentCreate(AppointmentBase):
    notes: Optional[str] = Field(None, description="Additional notes")


class AppointmentUpdate(BaseModel):
    scheduled_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=1)
    status: Optional[AppointmentStatusEnum] = None
    appointment_type: Optional[AppointmentTypeEnum] = None
    notes: Optional[str] = None

    class Config:
        extra = "forbid"


class AppointmentOut(AppointmentBase):
    id: int
    status: AppointmentStatusEnum
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class StaffRoleEnum(str, Enum):
    NURSE = "nurse"
    TECHNICIAN = "technician"
    ADMINISTRATOR = "administrator"
    MANAGER = "manager"
    SUPPORT = "support"


class StaffBase(BaseModel):
    staff_id: str = Field(..., description="Unique staff identifier")
    name: str = Field(..., description="Staff member's full name")
    role: StaffRoleEnum = Field(..., description="Staff role")
    department: DepartmentEnum = Field(..., description="Department assignment")


class StaffCreate(StaffBase):
    shift_start: Optional[datetime] = Field(None, description="Shift start time")
    shift_end: Optional[datetime] = Field(None, description="Shift end time")
    hire_date: Optional[datetime] = Field(None, description="Hire date")
    contact_info: Optional[str] = Field(None, description="Contact information")
    certifications: Optional[str] = Field(None, description="Certifications (comma-separated)")


class StaffUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[StaffRoleEnum] = None
    department: Optional[DepartmentEnum] = None
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    is_active: Optional[bool] = None
    contact_info: Optional[str] = None
    certifications: Optional[str] = None
    supervisor_id: Optional[int] = None

    class Config:
        extra = "forbid"


class StaffOut(StaffBase):
    id: int
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    is_active: bool
    hire_date: Optional[datetime] = None
    contact_info: Optional[str] = None
    certifications: Optional[str] = None
    supervisor_id: Optional[int] = None

    class Config:
        orm_mode = True
