from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models
from app.schemas import AppointmentCreate, AppointmentUpdate, AppointmentOut
from datetime import datetime

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
        models.Appointment.appointment_time.between(now, cutoff),
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
        models.Appointment.appointment_time.between(start, end)
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
        models.Appointment.appointment_time < end_time,
        models.Appointment.appointment_time >= apt_time
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
        models.Appointment.appointment_time.between(day_start, day_end),
        models.Appointment.status == "scheduled"
    ).all()
    booked_times = {apt.appointment_time for apt in booked}
    available_slots = []
    current_time = day_start
    while current_time < day_end:
        if current_time not in booked_times:
            available_slots.append(current_time.isoformat())
        current_time = datetime.utcfromtimestamp(current_time.timestamp() + slot_duration * 60)
    return {"doctor_id": doctor_id, "date": date, "available_slots": available_slots}