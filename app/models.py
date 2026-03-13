from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, unique=True, index=True)
    arrival_time = Column(DateTime)
    acuity_level = Column(Integer)
    department = Column(String)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    bed_id = Column(Integer, ForeignKey("beds.id"), nullable=True)

    doctor = relationship("Doctor", back_populates="patients")
    bed = relationship("Bed", back_populates="patient")

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    specialty = Column(String)
    department = Column(String)
    is_available = Column(Boolean, default=True)
    shift_start = Column(DateTime)
    shift_end = Column(DateTime)

    patients = relationship("Patient", back_populates="doctor")

class Bed(Base):
    __tablename__ = "beds"

    id = Column(Integer, primary_key=True, index=True)
    bed_number = Column(String, unique=True, index=True)
    department = Column(String)
    is_occupied = Column(Boolean, default=False)
    room_type = Column(String)
    last_cleaned = Column(DateTime)

    patient = relationship("Patient", back_populates="bed")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(String, unique=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    scheduled_time = Column(DateTime)
    duration_minutes = Column(Integer, default=30)
    status = Column(String, default="scheduled")
    appointment_type = Column(String)
    notes = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    patient = relationship("Patient", backref="appointments")
    doctor = relationship("Doctor", backref="appointments")

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String)
    department = Column(String)
    shift_start = Column(DateTime)
    shift_end = Column(DateTime)
    is_active = Column(Boolean, default=True)
    hire_date = Column(DateTime)
    contact_info = Column(String)
    certifications = Column(String)
    supervisor_id = Column(Integer, ForeignKey("staff.id"), nullable=True)

    supervisor = relationship("Staff", remote_side=[id], backref="subordinates")