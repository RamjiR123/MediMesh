from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models, database
from fastapi import FastAPI
from app.routers import patients

# This command creates the tables in PostgreSQL
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="MediMesh API")

@app.get("/")
def read_root():
    return {"message": "MediMesh API is Live", "database": "Tables Created"}

@app.get("/patients")
def get_patients(db: Session = Depends(database.get_db)):
    # This will eventually return the data from your DB
    return db.query(models.Patient).all()

app = FastAPI(title="MediMesh API")
app.include_router(patients.router)
