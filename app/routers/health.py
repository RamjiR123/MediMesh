from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import case, func, inspect, text
from datetime import datetime, timedelta
import psycopg2
import os
from app.database import get_db
from app import models
from app.operational_alerts import build_operational_alerts

router = APIRouter(prefix="/health", tags=["Health Checks"])
REQUIRED_TABLES = ("patients", "doctors", "beds", "appointments", "staff")


def _safe_percentage(numerator: int, denominator: int) -> float:
    """Return a rounded percentage while guarding against divide-by-zero cases."""
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _get_table_status(db: Session) -> dict[str, bool]:
    existing_tables = set(inspect(db.get_bind()).get_table_names())
    return {table: table in existing_tables for table in REQUIRED_TABLES}


def _bed_occupancy_by_department(db: Session):
    rows = (
        db.query(
            models.Bed.department,
            func.count(models.Bed.id).label("total_beds"),
            func.sum(
                case((models.Bed.is_occupied.is_(True), 1), else_=0)
            ).label("occupied_beds"),
        )
        .group_by(models.Bed.department)
        .order_by(models.Bed.department)
        .all()
    )
    return [
        {
            "department": department or "Unassigned",
            "total_beds": total_beds,
            "occupied_beds": occupied_beds,
            "occupancy_rate": _safe_percentage(occupied_beds, total_beds),
        }
        for department, total_beds, occupied_beds in rows
    ]


@router.get("/")
def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "service": "MediMesh API"
    }

@router.get("/database")
def database_health_check(db: Session = Depends(get_db)):
    """Check database connectivity and basic operations"""
    try:
        # Test basic query
        db.execute(text("SELECT 1"))
        db.commit()

        table_status = _get_table_status(db)
        tables_exist = all(table_status.values())

        return {
            "status": "healthy" if tables_exist else "unhealthy",
            "database": "connected",
            "tables_exist": tables_exist,
            "table_status": table_status,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@router.get("/metrics")
def system_metrics(db: Session = Depends(get_db)):
    """Get system metrics and counts"""
    try:
        patient_count = db.query(models.Patient).count()
        doctor_count = db.query(models.Doctor).count()
        bed_count = db.query(models.Bed).count()
        appointment_count = db.query(models.Appointment).count()
        staff_count = db.query(models.Staff).count()

        # Calculate occupancy rates
        occupied_beds = db.query(models.Bed).filter(models.Bed.is_occupied == True).count()
        bed_occupancy_rate = _safe_percentage(occupied_beds, bed_count)

        available_doctors = db.query(models.Doctor).filter(models.Doctor.is_available == True).count()
        doctor_availability_rate = _safe_percentage(available_doctors, doctor_count)

        # Recent activity (last 24 hours)
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        recent_patients = db.query(models.Patient).filter(models.Patient.arrival_time >= yesterday).count()
        recent_appointments = db.query(models.Appointment).filter(models.Appointment.created_at >= yesterday).count()
        upcoming_appointments = db.query(models.Appointment).filter(
            models.Appointment.scheduled_time.between(now, now + timedelta(days=1)),
            models.Appointment.status == "scheduled",
        ).count()

        metric_snapshot = {
            "total_patients": patient_count,
            "total_doctors": doctor_count,
            "total_beds": bed_count,
            "occupied_beds": occupied_beds,
            "bed_occupancy_by_department": _bed_occupancy_by_department(db),
            "total_appointments": appointment_count,
            "total_staff": staff_count,
            "bed_occupancy_rate": round(bed_occupancy_rate, 2),
            "doctor_availability_rate": round(doctor_availability_rate, 2),
            "recent_patients_24h": recent_patients,
            "recent_appointments_24h": recent_appointments,
            "upcoming_appointments_24h": upcoming_appointments,
        }

        return {
            "status": "healthy",
            "metrics": metric_snapshot,
            "alerts": build_operational_alerts({
                "bed_occupancy_rate": round(bed_occupancy_rate, 2),
                "total_doctors": doctor_count,
                "doctor_availability_rate": round(doctor_availability_rate, 2),
                "recent_patients_24h": recent_patients,
                "upcoming_appointments_24h": upcoming_appointments,
            }),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@router.get("/readiness")
def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe"""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))

        # Check if critical tables exist
        table_status = _get_table_status(db)
        missing_tables = [table for table, exists in table_status.items() if not exists]

        if missing_tables:
            return {
                "status": "not ready",
                "reason": f"Missing tables: {missing_tables}",
                "timestamp": datetime.utcnow()
            }

        return {
            "status": "ready",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "not ready",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@router.get("/liveness")
def liveness_check():
    """Kubernetes liveness probe"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow()
    }