from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import uuid4
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.database import get_db
from app import models
from app.schemas import AppointmentCreate, AppointmentUpdate, AppointmentOut, AppointmentTypeEnum

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.post("/", response_model=AppointmentOut)
def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    # Validate patient and doctor exist
    patient = db.query(models.Patient).filter(models.Patient.id == appointment.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    doctor = db.query(models.Doctor).filter(models.Doctor.id == appointment.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    db_appointment = models.Appointment(**appointment.dict(), created_at=datetime.utcnow())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

@router.get("/", response_model=List[AppointmentOut])
def list_appointments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    appointments = db.query(models.Appointment).offset(skip).limit(limit).all()
    return appointments

@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: str, db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(models.Appointment.appointment_id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.put("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(appointment_id: str, appointment_update: AppointmentUpdate, db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(models.Appointment.appointment_id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    update_data = appointment_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    for key, value in update_data.items():
        setattr(appointment, key, value)
    db.commit()
    db.refresh(appointment)
    return appointment

@router.delete("/{appointment_id}")
def delete_appointment(appointment_id: str, db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(models.Appointment.appointment_id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    db.delete(appointment)
    db.commit()
    return {"message": "Appointment deleted successfully"}

@router.get("/patient/{patient_id}", response_model=List[AppointmentOut])
def get_patient_appointments(patient_id: int, db: Session = Depends(get_db)):
    appointments = db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id).all()
    return appointments

@router.get("/doctor/{doctor_id}", response_model=List[AppointmentOut])
def get_doctor_appointments(doctor_id: int, db: Session = Depends(get_db)):
    appointments = db.query(models.Appointment).filter(models.Appointment.doctor_id == doctor_id).all()
    return appointments

@router.get("/status/{status}", response_model=List[AppointmentOut])
def get_appointments_by_status(status: str, db: Session = Depends(get_db)):
    valid_statuses = ["scheduled", "completed", "cancelled", "no-show"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
    appointments = db.query(models.Appointment).filter(models.Appointment.status == status).all()
    return appointments

@router.get("/upcoming/count", response_model=dict)
def get_upcoming_appointment_count(hours: int = 24, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    cutoff = datetime.utcfromtimestamp(now.timestamp() + hours * 3600)
    count = db.query(models.Appointment).filter(
        models.Appointment.scheduled_time.between(now, cutoff),
        models.Appointment.status == "scheduled"
    ).count()
    return {"upcoming_appointments": count, "time_window_hours": hours}

@router.get("/date-range/search", response_model=List[AppointmentOut])
def search_appointments_by_date_range(start_date: str, end_date: str, db: Session = Depends(get_db)):
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")
    appointments = db.query(models.Appointment).filter(
        models.Appointment.scheduled_time.between(start, end)
    ).all()
    return appointments

@router.post("/conflict-check", response_model=dict)
def check_appointment_conflicts(doctor_id: int, appointment_time: str, duration_minutes: int = 30, db: Session = Depends(get_db)):
    try:
        apt_time = datetime.fromisoformat(appointment_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid appointment_time format. Use ISO format.")
    end_time = datetime.utcfromtimestamp(apt_time.timestamp() + duration_minutes * 60)
    conflicts = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.status == "scheduled",
        models.Appointment.scheduled_time < end_time,
        models.Appointment.scheduled_time >= apt_time
    ).count()
    return {"has_conflicts": conflicts > 0, "conflicting_appointments": conflicts}

@router.get("/analytics/summary", response_model=dict)
def get_appointment_analytics(db: Session = Depends(get_db)):
    total = db.query(models.Appointment).count()
    scheduled = db.query(models.Appointment).filter(models.Appointment.status == "scheduled").count()
    completed = db.query(models.Appointment).filter(models.Appointment.status == "completed").count()
    cancelled = db.query(models.Appointment).filter(models.Appointment.status == "cancelled").count()
    no_show = db.query(models.Appointment).filter(models.Appointment.status == "no-show").count()
    return {
        "total_appointments": total,
        "scheduled": scheduled,
        "completed": completed,
        "cancelled": cancelled,
        "no_show": no_show,
        "completion_rate": round(completed / total * 100, 2) if total > 0 else 0
    }

@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(appointment_id: str, reason: str = None, db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(models.Appointment.appointment_id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.status == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel a completed appointment")
    appointment.status = "cancelled"
    appointment.cancellation_reason = reason
    appointment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(appointment)
    return appointment

@router.post("/bulk-status-update", response_model=dict)
def bulk_update_appointment_status(appointment_ids: List[int], new_status: str, db: Session = Depends(get_db)):
    valid_statuses = ["scheduled", "completed", "cancelled", "no-show"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
    updated_count = db.query(models.Appointment).filter(
        models.Appointment.id.in_(appointment_ids)
    ).update({"status": new_status, "updated_at": datetime.utcnow()})
    db.commit()
    return {"updated_appointments": updated_count, "new_status": new_status}

@router.get("/doctor/{doctor_id}/available-slots", response_model=dict)
def get_available_slots(doctor_id: int, date: str, slot_duration: int = 30, db: Session = Depends(get_db)):
    try:
        query_date = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format: YYYY-MM-DD")
    day_start = datetime(query_date.year, query_date.month, query_date.day, 9, 0)
    day_end = datetime(query_date.year, query_date.month, query_date.day, 17, 0)
    booked = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.scheduled_time.between(day_start, day_end),
        models.Appointment.status == "scheduled"
    ).all()
    booked_times = {apt.scheduled_time for apt in booked}
    available_slots = []
    current_time = day_start
    while current_time < day_end:
        if current_time not in booked_times:
            available_slots.append(current_time.isoformat())
        current_time = datetime.utcfromtimestamp(current_time.timestamp() + slot_duration * 60)
    return {"doctor_id": doctor_id, "date": date, "available_slots": available_slots}


def parse_iso_datetime(value: str, field_name: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name} format. Use ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")


@router.post("/bulk-import", response_model=dict)
def bulk_import_appointments(appointments: List[AppointmentCreate], db: Session = Depends(get_db)):
    imported_ids = []
    for appointment in appointments:
        patient = db.query(models.Patient).filter(models.Patient.id == appointment.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {appointment.patient_id} not found")
        doctor = db.query(models.Doctor).filter(models.Doctor.id == appointment.doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail=f"Doctor {appointment.doctor_id} not found")

        db_appointment = models.Appointment(**appointment.dict(), created_at=datetime.utcnow())
        db.add(db_appointment)
        imported_ids.append(appointment.appointment_id)

    db.commit()
    return {"imported_appointments": len(imported_ids), "appointment_ids": imported_ids}


class RecurringAppointmentRequest(BaseModel):
    patient_id: int
    doctor_id: int
    start_time: datetime
    appointment_type: AppointmentTypeEnum
    interval_days: int = 7
    occurrences: int = 4
    duration_minutes: int = 30
    notes: Optional[str] = None


@router.post("/recurring", response_model=List[AppointmentOut])
def create_recurring_appointments(request: RecurringAppointmentRequest, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    doctor = db.query(models.Doctor).filter(models.Doctor.id == request.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    appointments = []
    for index in range(request.occurrences):
        scheduled_time = request.start_time + timedelta(days=index * request.interval_days)
        conflict_count = db.query(models.Appointment).filter(
            models.Appointment.doctor_id == request.doctor_id,
            models.Appointment.status == "scheduled",
            models.Appointment.scheduled_time == scheduled_time
        ).count()
        if conflict_count:
            continue

        appointment_id = f"rec-{request.patient_id}-{request.doctor_id}-{uuid4().hex[:8]}-{index}"
        new_appointment = models.Appointment(
            appointment_id=appointment_id,
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            scheduled_time=scheduled_time,
            duration_minutes=request.duration_minutes,
            status="scheduled",
            appointment_type=request.appointment_type,
            notes=request.notes,
            created_at=datetime.utcnow()
        )
        db.add(new_appointment)
        appointments.append(new_appointment)

    if not appointments:
        raise HTTPException(status_code=400, detail="No recurring appointments could be scheduled due to conflicts")

    db.commit()
    for appointment in appointments:
        db.refresh(appointment)
    return appointments


@router.get("/report/doctor/{doctor_id}", response_model=dict)
def get_doctor_report(doctor_id: int, date: Optional[str] = None, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if date:
        target_date = parse_iso_datetime(date, "date").date()
    else:
        target_date = datetime.utcnow().date()

    start = datetime(target_date.year, target_date.month, target_date.day, 0, 0)
    end = start + timedelta(days=1)

    appointments = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.scheduled_time.between(start, end)
    ).all()

    status_breakdown = {
        "scheduled": 0,
        "completed": 0,
        "cancelled": 0,
        "no-show": 0
    }
    next_slot = None
    now = datetime.utcnow()
    for apt in appointments:
        status_breakdown[apt.status] = status_breakdown.get(apt.status, 0) + 1
        if apt.status == "scheduled" and apt.scheduled_time >= now:
            if next_slot is None or apt.scheduled_time < next_slot:
                next_slot = apt.scheduled_time

    return {
        "doctor_id": doctor_id,
        "date": target_date.isoformat(),
        "total_appointments": len(appointments),
        "status_breakdown": status_breakdown,
        "next_available_slot": next_slot.isoformat() if next_slot else None
    }


@router.get("/report/patient/{patient_id}", response_model=dict)
def get_patient_report(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    upcoming = db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient.id,
        models.Appointment.scheduled_time >= datetime.utcnow(),
        models.Appointment.status == "scheduled"
    ).order_by(models.Appointment.scheduled_time).all()

    return {
        "patient_id": patient_id,
        "upcoming_appointments": len(upcoming),
        "next_appointment": upcoming[0].scheduled_time.isoformat() if upcoming else None
    }


@router.get("/report/date/{date}", response_model=dict)
def get_daily_appointment_report(date: str, db: Session = Depends(get_db)):
    target_date = parse_iso_datetime(date, "date").date()
    start = datetime(target_date.year, target_date.month, target_date.day, 0, 0)
    end = start + timedelta(days=1)

    appointments = db.query(models.Appointment).filter(
        models.Appointment.scheduled_time.between(start, end)
    ).all()

    by_status = {}
    by_doctor = {}
    for apt in appointments:
        by_status[apt.status] = by_status.get(apt.status, 0) + 1
        by_doctor[apt.doctor_id] = by_doctor.get(apt.doctor_id, 0) + 1

    busiest_doctor = None
    if by_doctor:
        busiest_doctor = max(by_doctor, key=by_doctor.get)

    return {
        "date": target_date.isoformat(),
        "total_appointments": len(appointments),
        "by_status": by_status,
        "busiest_doctor_id": busiest_doctor,
        "appointments_per_doctor": by_doctor
    }