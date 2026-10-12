import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas import DepartmentEnum, StaffRoleEnum

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/reset")
def reset_data(db: Session = Depends(get_db)):
    # Delete dependent records first to avoid foreign key issues.
    db.query(models.Appointment).delete(synchronize_session=False)
    db.query(models.Patient).delete(synchronize_session=False)
    db.query(models.Bed).delete(synchronize_session=False)
    db.query(models.Doctor).delete(synchronize_session=False)
    db.query(models.Staff).delete(synchronize_session=False)
    db.commit()
    return {
        "message": "Reset complete",
        "patients": 0,
        "doctors": 0,
        "beds": 0,
        "appointments": 0,
        "staff": 0
    }

@router.get("/summary")
def admin_summary(db: Session = Depends(get_db)):
    return {
        "patients": db.query(models.Patient).count(),
        "doctors": db.query(models.Doctor).count(),
        "beds": db.query(models.Bed).count(),
        "appointments": db.query(models.Appointment).count(),
        "staff": db.query(models.Staff).count()
    }

@router.post("/seed")
def seed_large_demo(db: Session = Depends(get_db)):
    reset_data(db)

    departments = [dept.value for dept in DepartmentEnum]
    specialties = [
        "Emergency Medicine",
        "Critical Care",
        "Internal Medicine",
        "Family Medicine",
        "Surgery",
        "General Practice"
    ]
    room_types = ["ICU", "General", "ER"]
    appointment_types = [
        "consultation",
        "follow-up",
        "procedure",
        "emergency"
    ]
    staff_roles = [role.value for role in StaffRoleEnum]

    # Create doctors
    doctors = []
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    for i in range(1, 51):
        department = random.choice(departments)
        shift_start = now - timedelta(hours=random.randint(0, 8))
        shift_end = shift_start + timedelta(hours=8)
        doctor = models.Doctor(
            doctor_id=f"DOC-{i:03}",
            name=f"Dr. {['Alden','Brooks','Chen','Diaz','Evans','Frost'][i % 6]} {i}",
            specialty=random.choice(specialties),
            department=department,
            is_available=bool(random.choice([True, True, False])),
            shift_start=shift_start,
            shift_end=shift_end
        )
        db.add(doctor)
        doctors.append(doctor)

    # Create beds
    beds = []
    for i in range(1, 151):
        bed = models.Bed(
            bed_number=f"BED-{i:03}",
            department=random.choice(departments),
            room_type=random.choice(room_types),
            is_occupied=False,
            last_cleaned=now - timedelta(hours=random.randint(1, 72))
        )
        db.add(bed)
        beds.append(bed)

    db.flush()

    # Create patients across one week of arrivals
    patients = []
    start = now - timedelta(days=7)
    for i in range(1001, 2001):
        arrival_offset = random.randint(0, 7 * 24 * 4)
        arrival = start + timedelta(minutes=15 * arrival_offset)
        department = random.choice(departments)
        patient = models.Patient(
            patient_id=i,
            arrival_time=arrival,
            acuity_level=random.choices([1, 2, 3, 4, 5], weights=[20, 25, 25, 20, 10])[0],
            department=department
        )
        db.add(patient)
        patients.append(patient)

    db.flush()

    # Assign roughly 100 beds to random patients
    occupied_beds = random.sample(beds, min(100, len(beds)))
    assigned_patients = random.sample(patients, len(occupied_beds))
    for bed, patient in zip(occupied_beds, assigned_patients):
        bed.is_occupied = True
        patient.bed_id = bed.id

    # Create appointments for a subset of patients
    for i in range(1, 201):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        scheduled_time = now + timedelta(hours=random.randint(1, 72))
        appointment = models.Appointment(
            appointment_id=f"APT-{i:04}",
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=scheduled_time,
            duration_minutes=random.choice([15, 30, 45]),
            status="scheduled",
            appointment_type=random.choice(appointment_types),
            notes="Auto-seeded demo appointment",
            created_at=now,
            updated_at=now
        )
        db.add(appointment)

    # Create staff for completeness
    for i in range(1, 21):
        shift_start = now - timedelta(hours=random.randint(0, 8))
        shift_end = shift_start + timedelta(hours=8)
        staff = models.Staff(
            staff_id=f"STAFF-{i:03}",
            name=f"Staff Member {i}",
            role=random.choice(staff_roles),
            department=random.choice(departments),
            shift_start=shift_start,
            shift_end=shift_end,
            is_active=True,
            hire_date=now - timedelta(days=random.randint(30, 365)),
            contact_info="demo@example.com",
            certifications="BLS, ACLS"
        )
        db.add(staff)

    db.commit()

    return {
        "message": "Large demo dataset seeded successfully",
        "patients": len(patients),
        "doctors": len(doctors),
        "beds": len(beds),
        "appointments": 200,
        "staff": 20
    }
