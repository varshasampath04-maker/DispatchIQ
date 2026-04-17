print("STEP 1: FILE START")

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
from database import engine, get_db, Base
import models
from helpers import RESPONSES, process_driver_response, calculate_risk
import random

load_dotenv()
print("STEP 2: ALL IMPORTS DONE")

app = FastAPI(title="Shipments API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
print("STEP 3: APP CREATED")

Base.metadata.create_all(bind=engine)
print("STEP 4: DB READY")
# ---------- Schemas ----------
class ShipmentCreate(BaseModel):
    driver_name: str
    status:      Optional[str]      = "pending"
    eta:         Optional[datetime] = None
    score:       Optional[float]    = None
    decision:    Optional[str]      = None

class ShipmentOut(ShipmentCreate):
    id: int
    class Config:
        from_attributes = True

# ---------- Routes ----------
@app.post("/shipments/", response_model=ShipmentOut, status_code=201)
def create(payload: ShipmentCreate, db: Session = Depends(get_db)):
    row = models.Shipment(**payload.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return row

@app.get("/shipments/", response_model=list[ShipmentOut])
def list_all(db: Session = Depends(get_db)):
    return db.query(models.Shipment).all()

@app.get("/shipments/{id}", response_model=ShipmentOut)
def get_one(id: int, db: Session = Depends(get_db)):
    row = db.get(models.Shipment, id)
    if not row: raise HTTPException(404, "Not found")
    return row

@app.patch("/shipments/{id}", response_model=ShipmentOut)
def update(id: int, payload: ShipmentCreate, db: Session = Depends(get_db)):
    row = db.get(models.Shipment, id)
    if not row: raise HTTPException(404, "Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit(); db.refresh(row)
    return row

@app.delete("/shipments/{id}", status_code=204)
def delete(id: int, db: Session = Depends(get_db)):
    row = db.get(models.Shipment, id)
    if not row: raise HTTPException(404, "Not found")
    db.delete(row); db.commit()

@app.post("/dispatch", response_model=list[ShipmentOut])
def dispatch(db: Session = Depends(get_db)):
    shipments = db.query(models.Shipment).all()

    for row in shipments:
        text   = random.choice(RESPONSES)
        parsed = process_driver_response(text)
        risk   = calculate_risk(parsed)

        # ✅ LOGS
        print(f"[DISPATCH] Driver response: {text}")
        print(f"[AI] Parsed: {parsed}")
        print(f"[RISK] Score: {risk['score']} → {risk['decision']}")

        row.score    = risk["score"]
        row.decision = risk["decision"]

        # ✅ STATUS
        if risk["decision"] == "HOLD":
            row.status = "critical"
        elif risk["decision"] == "DELAY":
            row.status = "delayed"
        else:
            row.status = "on_track"

    db.commit()

    for row in shipments:
        db.refresh(row)

    return shipments