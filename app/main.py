import os

from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, database
from .routers import patients, doctors, beds, appointments, staff, health, predictive, admin

# This line is the magic — it creates the tables if they don't exist
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="MediMesh API")

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

from fastapi.responses import FileResponse

@app.get("/", include_in_schema=False)
def root():
    return FileResponse(os.path.join(static_dir, "index.html"))

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
app.include_router(admin.router)
