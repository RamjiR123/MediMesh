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