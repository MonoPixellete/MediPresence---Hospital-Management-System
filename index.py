"""
Main API handler for Vercel serverless functions
Uses Mangum adapter to convert FastAPI ASGI app to AWS Lambda format
"""
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from db import get_db, Session, User, StaffPresence, Patient, Task, Alert, AuditLog, VitalRecord
from auth import hash_password, verify_password, create_access_token, decode_token
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os

app = FastAPI(title="MediPresence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str
    full_name: str

class UserLogin(BaseModel):
    username: str
    password: str

class StatusUpdate(BaseModel):
    status: str
    activity: Optional[str] = None
    location: Optional[str] = None

class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str
    illness: str
    room_number: str
    assigned_doctor_id: int
    assigned_nurse_id: int

class TaskCreate(BaseModel):
    title: str
    description: str
    assigned_to: int
    priority: str
    deadline: datetime

class VitalCreate(BaseModel):
    patient_id: int
    temperature: Optional[float] = None
    blood_pressure: Optional[str] = None
    pulse: Optional[int] = None
    respiration_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    notes: Optional[str] = None

# Helper function to get current user from token
def get_current_user_from_header(request: Request, db: Session):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = auth_header.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# API Routes
@app.get("/")
def root():
    return {"message": "MediPresence API", "status": "running"}

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
        full_name=user.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    presence = StaffPresence(user_id=new_user.id)
    db.add(presence)
    db.commit()
    
    return {"message": "User created successfully", "user_id": new_user.id}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    presence = db.query(StaffPresence).filter(StaffPresence.user_id == db_user.id).first()
    if presence:
        presence.status = "on-duty"
        presence.activity = "active"
        presence.shift_start = datetime.utcnow()
        presence.last_active = datetime.utcnow()
        db.commit()
    
    token = create_access_token({"sub": db_user.username})
    return {
        "token": token,
        "role": db_user.role,
        "user_id": db_user.id,
        "full_name": db_user.full_name
    }

@app.get("/me")
def get_me(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_header(request, db)
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "full_name": current_user.full_name
    }

@app.get("/staff/presence")
def get_staff_presence(request: Request, db: Session = Depends(get_db)):
    try:
        get_current_user_from_header(request, db)
    except:
        pass  # Allow unauthenticated access for public status
    
    presences = db.query(StaffPresence, User).join(User).all()
    result = []
    for presence, user in presences:
        result.append({
            "id": presence.id,
            "user_id": user.id,
            "full_name": user.full_name,
            "role": user.role,
            "status": presence.status,
            "activity": presence.activity,
            "location": presence.location,
            "assigned_patients": presence.assigned_patients,
            "last_active": presence.last_active.isoformat() if presence.last_active else None
        })
    return result

@app.post("/staff/update-status")
def update_status(update: StatusUpdate, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_header(request, db)
    
    presence = db.query(StaffPresence).filter(StaffPresence.user_id == current_user.id).first()
    if not presence:
        raise HTTPException(status_code=404, detail="Presence record not found")
    
    presence.status = update.status
    if update.activity:
        presence.activity = update.activity
    if update.location:
        presence.location = update.location
    presence.last_active = datetime.utcnow()
    db.commit()
    
    return {"message": "Status updated"}

@app.post("/patients")
def create_patient(patient: PatientCreate, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_header(request, db)
    
    new_patient = Patient(**patient.dict())
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return {"message": "Patient created", "patient_id": new_patient.id}

@app.get("/patients")
def get_patients(request: Request, db: Session = Depends(get_db)):
    get_current_user_from_header(request, db)
    
    patients = db.query(Patient).all()
    return [{
        "id": p.id,
        "name": p.name,
        "age": p.age,
        "gender": p.gender,
        "illness": p.illness,
        "room_number": p.room_number,
        "assigned_doctor_id": p.assigned_doctor_id,
        "assigned_nurse_id": p.assigned_nurse_id,
        "status": p.status,
        "admitted_at": p.admitted_at.isoformat() if p.admitted_at else None
    } for p in patients]

@app.post("/tasks")
def create_task(task: TaskCreate, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_header(request, db)
    
    new_task = Task(**task.dict(), assigned_by=current_user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {"message": "Task created", "task_id": new_task.id}

@app.get("/tasks")
def get_tasks(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_header(request, db)
    
    if current_user.role == "admin":
        tasks = db.query(Task).all()
    else:
        tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
    
    return [{
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "assigned_to": t.assigned_to,
        "priority": t.priority,
        "status": t.status,
        "deadline": t.deadline.isoformat() if t.deadline else None,
        "created_at": t.created_at.isoformat() if t.created_at else None
    } for t in tasks]

@app.get("/alerts")
def get_alerts(request: Request, db: Session = Depends(get_db)):
    get_current_user_from_header(request, db)
    
    alerts = db.query(Alert).filter(Alert.acknowledged == False).order_by(Alert.created_at.desc()).all()
    return [{
        "id": a.id,
        "alert_type": a.alert_type,
        "message": a.message,
        "priority": a.priority,
        "created_at": a.created_at.isoformat() if a.created_at else None
    } for a in alerts]

@app.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, request: Request, db: Session = Depends(get_db)):
    get_current_user_from_header(request, db)
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    return {"message": "Alert acknowledged"}

@app.get("/audit-logs")
def get_audit_logs(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_header(request, db)
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    return [{
        "id": l.id,
        "user_id": l.user_id,
        "action": l.action,
        "details": l.details,
        "created_at": l.created_at.isoformat() if l.created_at else None
    } for l in logs]

@app.post("/vitals")
def create_vital(vital: VitalCreate, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_header(request, db)
    
    new_vital = VitalRecord(
        patient_id=vital.patient_id,
        recorded_by=current_user.id,
        temperature=vital.temperature,
        blood_pressure=vital.blood_pressure,
        pulse=vital.pulse,
        respiration_rate=vital.respiration_rate,
        oxygen_saturation=vital.oxygen_saturation,
        notes=vital.notes
    )
    db.add(new_vital)
    db.commit()
    db.refresh(new_vital)
    return {"message": "Vital recorded", "vital_id": new_vital.id}

@app.get("/vitals/{patient_id}")
def get_vitals(patient_id: int, request: Request, db: Session = Depends(get_db)):
    get_current_user_from_header(request, db)
    
    vitals = db.query(VitalRecord).filter(VitalRecord.patient_id == patient_id).order_by(VitalRecord.recorded_at.desc()).all()
    return [{
        "id": v.id,
        "temperature": v.temperature,
        "blood_pressure": v.blood_pressure,
        "pulse": v.pulse,
        "respiration_rate": v.respiration_rate,
        "oxygen_saturation": v.oxygen_saturation,
        "notes": v.notes,
        "recorded_at": v.recorded_at.isoformat() if v.recorded_at else None
    } for v in vitals]

# Vercel serverless handler - Mangum adapter
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    # Fallback if mangum not available
    handler = app
