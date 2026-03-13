from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import psycopg2
import os
from app.database import get_db
from app import models

router = APIRouter(prefix="/health", tags=["Health Checks"])

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

        # Check if tables exist
        tables_exist = all([
            db.query(models.Patient).first() is not None or True,  # Allow empty tables
            db.query(models.Doctor).first() is not None or True,
            db.query(models.Bed).first() is not None or True,
            db.query(models.Appointment).first() is not None or True,
            db.query(models.Staff).first() is not None or True,
        ])

        return {
            "status": "healthy",
            "database": "connected",
            "tables_exist": tables_exist,
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
        bed_occupancy_rate = (occupied_beds / bed_count * 100) if bed_count > 0 else 0

        available_doctors = db.query(models.Doctor).filter(models.Doctor.is_available == True).count()
        doctor_availability_rate = (available_doctors / doctor_count * 100) if doctor_count > 0 else 0

        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_patients = db.query(models.Patient).filter(models.Patient.arrival_time >= yesterday).count()
        recent_appointments = db.query(models.Appointment).filter(models.Appointment.created_at >= yesterday).count()

        return {
            "status": "healthy",
            "metrics": {
                "total_patients": patient_count,
                "total_doctors": doctor_count,
                "total_beds": bed_count,
                "total_appointments": appointment_count,
                "total_staff": staff_count,
                "bed_occupancy_rate": round(bed_occupancy_rate, 2),
                "doctor_availability_rate": round(doctor_availability_rate, 2),
                "recent_patients_24h": recent_patients,
                "recent_appointments_24h": recent_appointments
            },
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
        inspector = db.get_bind().engine
        tables = inspector.get_table_names()

        required_tables = ["patients", "doctors", "beds", "appointments", "staff"]
        missing_tables = [table for table in required_tables if table not in tables]

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