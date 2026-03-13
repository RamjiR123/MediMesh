from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
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