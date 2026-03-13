from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models
from app.schemas import StaffCreate, StaffUpdate, StaffOut

router = APIRouter(prefix="/staff", tags=["Staff"])

@router.post("/", response_model=StaffOut)
def create_staff(staff: StaffCreate, db: Session = Depends(get_db)):
    db_staff = models.Staff(**staff.dict())
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff

@router.get("/", response_model=List[StaffOut])
def list_staff(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    staff = db.query(models.Staff).offset(skip).limit(limit).all()
    return staff

@router.get("/{staff_id}", response_model=StaffOut)
def get_staff(staff_id: str, db: Session = Depends(get_db)):
    staff = db.query(models.Staff).filter(models.Staff.staff_id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return staff

@router.put("/{staff_id}", response_model=StaffOut)
def update_staff(staff_id: str, staff_update: StaffUpdate, db: Session = Depends(get_db)):
    staff = db.query(models.Staff).filter(models.Staff.staff_id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    for key, value in staff_update.dict(exclude_unset=True).items():
        setattr(staff, key, value)
    db.commit()
    db.refresh(staff)
    return staff

@router.delete("/{staff_id}")
def delete_staff(staff_id: str, db: Session = Depends(get_db)):
    staff = db.query(models.Staff).filter(models.Staff.staff_id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    db.delete(staff)
    db.commit()
    return {"message": "Staff member deleted successfully"}

@router.get("/department/{department}", response_model=List[StaffOut])
def get_staff_by_department(department: str, db: Session = Depends(get_db)):
    staff = db.query(models.Staff).filter(models.Staff.department == department).all()
    return staff

@router.get("/active/", response_model=List[StaffOut])
def list_active_staff(db: Session = Depends(get_db)):
    staff = db.query(models.Staff).filter(models.Staff.is_active == True).all()
    return staff