from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app import models
from app.schemas import BedCreate, BedUpdate, BedOut

router = APIRouter(prefix="/beds", tags=["Beds"])

@router.post("/", response_model=BedOut)
def create_bed(bed: BedCreate, db: Session = Depends(get_db)):
    db_bed = models.Bed(**bed.dict())
    db.add(db_bed)
    db.commit()
    db.refresh(db_bed)
    return db_bed

@router.get("/", response_model=List[BedOut])
def list_beds(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    beds = db.query(models.Bed).offset(skip).limit(limit).all()
    return beds

@router.get("/{bed_number}", response_model=BedOut)
def get_bed(bed_number: str, db: Session = Depends(get_db)):
    bed = db.query(models.Bed).filter(models.Bed.bed_number == bed_number).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    return bed

@router.put("/{bed_number}", response_model=BedOut)
def update_bed(bed_number: str, bed_update: BedUpdate, db: Session = Depends(get_db)):
    bed = db.query(models.Bed).filter(models.Bed.bed_number == bed_number).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    for key, value in bed_update.dict(exclude_unset=True).items():
        setattr(bed, key, value)
    db.commit()
    db.refresh(bed)
    return bed

@router.delete("/{bed_number}")
def delete_bed(bed_number: str, db: Session = Depends(get_db)):
    bed = db.query(models.Bed).filter(models.Bed.bed_number == bed_number).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    db.delete(bed)
    db.commit()
    return {"message": "Bed deleted successfully"}

@router.get("/available/", response_model=List[BedOut])
def list_available_beds(db: Session = Depends(get_db)):
    beds = db.query(models.Bed).filter(models.Bed.is_occupied == False).all()
    return beds

@router.get("/search", response_model=List[BedOut])
def search_beds(department: Optional[str] = None, room_type: Optional[str] = None, is_occupied: Optional[bool] = None, db: Session = Depends(get_db)):
    query = db.query(models.Bed)
    if department:
        query = query.filter(models.Bed.department == department)
    if room_type:
        query = query.filter(models.Bed.room_type == room_type)
    if is_occupied is not None:
        query = query.filter(models.Bed.is_occupied == is_occupied)
    return query.all()

@router.post("/{bed_number}/assign", response_model=BedOut)
def assign_bed(bed_number: str, patient_id: int, db: Session = Depends(get_db)):
    bed = db.query(models.Bed).filter(models.Bed.bed_number == bed_number).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    if bed.is_occupied:
        raise HTTPException(status_code=400, detail="Bed is already occupied")
    patient = db.query(models.Patient).filter(models.Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    bed.is_occupied = True
    patient.bed_id = bed.id
    db.commit()
    db.refresh(bed)
    return bed

@router.post("/{bed_number}/release", response_model=BedOut)
def release_bed(bed_number: str, db: Session = Depends(get_db)):
    bed = db.query(models.Bed).filter(models.Bed.bed_number == bed_number).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    if not bed.is_occupied:
        raise HTTPException(status_code=400, detail="Bed is already available")

    assigned_patient = db.query(models.Patient).filter(models.Patient.bed_id == bed.id).first()
    if assigned_patient:
        assigned_patient.bed_id = None

    bed.is_occupied = False
    db.commit()
    db.refresh(bed)
    return bed

@router.post("/{bed_number}/clean", response_model=BedOut)
def clean_bed(bed_number: str, db: Session = Depends(get_db)):
    bed = db.query(models.Bed).filter(models.Bed.bed_number == bed_number).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    bed.last_cleaned = datetime.utcnow()
    db.commit()
    db.refresh(bed)
    return bed

@router.get("/summary", response_model=dict)
def bed_summary(db: Session = Depends(get_db)):
    total = db.query(models.Bed).count()
    occupied = db.query(models.Bed).filter(models.Bed.is_occupied == True).count()
    available = total - occupied
    department_breakdown = {
        row.department: db.query(models.Bed).filter(models.Bed.department == row.department).count()
        for row in db.query(models.Bed.department).distinct().all()
    }
    return {
        "total_beds": total,
        "occupied_beds": occupied,
        "available_beds": available,
        "department_breakdown": department_breakdown
    }