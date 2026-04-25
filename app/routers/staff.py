from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
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

@router.get("/search", response_model=List[StaffOut])
def search_staff(
    role: Optional[str] = None,
    department: Optional[str] = None,
    is_active: Optional[bool] = None,
    on_shift: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Staff)
    if role:
        query = query.filter(models.Staff.role == role)
    if department:
        query = query.filter(models.Staff.department == department)
    if is_active is not None:
        query = query.filter(models.Staff.is_active == is_active)
    if on_shift is not None:
        now = datetime.utcnow()
        if on_shift:
            query = query.filter(models.Staff.shift_start <= now, models.Staff.shift_end >= now)
        else:
            query = query.filter((models.Staff.shift_start > now) | (models.Staff.shift_end < now))
    return query.all()

@router.get("/team/{staff_id}", response_model=List[StaffOut])
def get_staff_team(staff_id: str, db: Session = Depends(get_db)):
    leader = db.query(models.Staff).filter(models.Staff.staff_id == staff_id).first()
    if not leader:
        raise HTTPException(status_code=404, detail="Staff member not found")
    team = db.query(models.Staff).filter(models.Staff.supervisor_id == leader.id).all()
    return team

@router.get("/summary", response_model=dict)
def staff_summary(db: Session = Depends(get_db)):
    total = db.query(models.Staff).count()
    active = db.query(models.Staff).filter(models.Staff.is_active == True).count()
    on_shift = db.query(models.Staff).filter(models.Staff.shift_start <= datetime.utcnow(), models.Staff.shift_end >= datetime.utcnow()).count()
    department_counts = {
        row.department: db.query(models.Staff).filter(models.Staff.department == row.department).count()
        for row in db.query(models.Staff.department).distinct().all()
    }
    return {
        "total_staff": total,
        "active_staff": active,
        "currently_on_shift": on_shift,
        "department_counts": department_counts
    }

@router.post("/{staff_id}/deactivate", response_model=StaffOut)
def deactivate_staff(staff_id: str, db: Session = Depends(get_db)):
    staff = db.query(models.Staff).filter(models.Staff.staff_id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    staff.is_active = False
    db.commit()
    db.refresh(staff)
    return staff