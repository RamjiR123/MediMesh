from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, database
from .routers import patients, doctors, beds, appointments, staff, health, predictive

# This line is the magic — it creates the tables if they don't exist
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="MediMesh API")

# Dependency to get the database session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Include routers
app.include_router(patients.router)
app.include_router(doctors.router)
app.include_router(beds.router)
app.include_router(appointments.router)
app.include_router(staff.router)
app.include_router(health.router)
app.include_router(predictive.router)
