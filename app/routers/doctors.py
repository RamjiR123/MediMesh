from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app import models
from app.schemas import DoctorCreate, DoctorUpdate, DoctorOut

router = APIRouter(prefix="/doctors", tags=["Doctors"])

@router.post("/", response_model=DoctorOut)
def create_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    db_doctor = models.Doctor(**doctor.dict())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

@router.get("/", response_model=List[DoctorOut])
def list_doctors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    doctors = db.query(models.Doctor).offset(skip).limit(limit).all()
    return doctors

@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: str, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.doctor_id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@router.put("/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id: str, doctor_update: DoctorUpdate, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.doctor_id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    for key, value in doctor_update.dict(exclude_unset=True).items():
        setattr(doctor, key, value)
    db.commit()
    db.refresh(doctor)
    return doctor

@router.delete("/{doctor_id}")
def delete_doctor(doctor_id: str, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.doctor_id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    db.delete(doctor)
    db.commit()
    return {"message": "Doctor deleted successfully"}

@router.get("/search", response_model=List[DoctorOut])
def search_doctors(
    department: Optional[str] = None,
    specialty: Optional[str] = None,
    is_available: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Doctor)
    if department:
        query = query.filter(models.Doctor.department == department)
    if specialty:
        query = query.filter(models.Doctor.specialty == specialty)
    if is_available is not None:
        query = query.filter(models.Doctor.is_available == is_available)
    return query.all()

@router.get("/on-shift/", response_model=List[DoctorOut])
def list_on_shift_doctors(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    doctors = db.query(models.Doctor).filter(
        models.Doctor.shift_start <= now,
        models.Doctor.shift_end >= now,
        models.Doctor.is_available == True
    ).all()
    return doctors

@router.get("/summary", response_model=dict)
def doctor_summary(db: Session = Depends(get_db)):
    total = db.query(models.Doctor).count()
    available = db.query(models.Doctor).filter(models.Doctor.is_available == True).count()
    by_department = {
        row.department: db.query(models.Doctor).filter(models.Doctor.department == row.department).count()
        for row in db.query(models.Doctor.department).distinct().all()
    }
    by_specialty = {
        row.specialty: db.query(models.Doctor).filter(models.Doctor.specialty == row.specialty).count()
        for row in db.query(models.Doctor.specialty).distinct().all()
    }
    return {
        "total_doctors": total,
        "available_doctors": available,
        "by_department": by_department,
        "by_specialty": by_specialty
    }

@router.get("/available/", response_model=List[DoctorOut])
def list_available_doctors(db: Session = Depends(get_db)):
    doctors = db.query(models.Doctor).filter(models.Doctor.is_available == True).all()
    return doctors