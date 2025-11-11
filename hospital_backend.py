"""
MediPresence Backend - FastAPI + WebSockets + SQLite
Run: uvicorn backend:app --reload --port 8000
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import asyncio
import threading
import jwt
import json
from passlib.context import CryptContext

# Database Setup
DATABASE_URL = "sqlite:///./medipresence.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    role = Column(String)  # admin, doctor, nurse, receptionist, staff
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class StaffPresence(Base):
    __tablename__ = "staff_presence"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="off-duty")  # on-duty, off-duty
    activity = Column(String, default="idle")  # active, busy, idle
    location = Column(String, default="Unknown")
    shift_start = Column(DateTime)
    shift_end = Column(DateTime)
    last_active = Column(DateTime, default=datetime.utcnow)
    assigned_patients = Column(Integer, default=0)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    illness = Column(Text)
    room_number = Column(String)
    assigned_doctor_id = Column(Integer, ForeignKey("users.id"))
    assigned_nurse_id = Column(Integer, ForeignKey("users.id"))
    medical_history = Column(Text)
    vitals = Column(Text)  # JSON string
    admitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="admitted")

class VitalRecord(Base):
    __tablename__ = "vital_records"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    recorded_by = Column(Integer, ForeignKey("users.id"))
    temperature = Column(Float, nullable=True)
    blood_pressure = Column(String, nullable=True)
    pulse = Column(Integer, nullable=True)
    respiration_rate = Column(Integer, nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    medication_name = Column(String)
    dosage = Column(String)
    route = Column(String, nullable=True)
    frequency_hours = Column(Integer)
    start_time = Column(DateTime, default=datetime.utcnow)
    next_dose_time = Column(DateTime)
    last_administered_at = Column(DateTime, nullable=True)
    status = Column(String, default="scheduled")  # scheduled, administered, overdue
    assigned_nurse_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))

class CarePlanStep(Base):
    __tablename__ = "care_plan_steps"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    title = Column(String)
    description = Column(Text)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_time = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, in-progress, completed
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    assigned_by = Column(Integer, ForeignKey("users.id"))
    priority = Column(String, default="medium")  # low, medium, high, critical
    status = Column(String, default="pending")  # pending, in-progress, completed
    deadline = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String)
    message = Column(Text)
    priority = Column(String)  # critical, high, medium, low
    related_user_id = Column(Integer, ForeignKey("users.id"))
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)
    details = Column(Text)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Shift(Base):
    __tablename__ = "shifts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    clock_in = Column(DateTime)
    clock_out = Column(DateTime, nullable=True)
    break_duration = Column(Integer, default=0)  # minutes
    overtime = Column(Integer, default=0)  # minutes
    date = Column(String)

# Create tables
Base.metadata.create_all(bind=engine)

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

class TaskCreate(BaseModel):
    title: str
    description: str
    assigned_to: int
    priority: str
    deadline: datetime

class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str
    illness: str
    room_number: str
    assigned_doctor_id: int
    assigned_nurse_id: int

class StatusUpdate(BaseModel):
    status: str
    activity: Optional[str] = None
    location: Optional[str] = None

class VitalCreate(BaseModel):
    temperature: Optional[float] = None
    blood_pressure: Optional[str] = None
    pulse: Optional[int] = None
    respiration_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    notes: Optional[str] = None

class MedicationCreate(BaseModel):
    medication_name: str
    dosage: str
    route: Optional[str] = None
    frequency_hours: int
    start_time: Optional[datetime] = None
    assigned_nurse_id: Optional[int] = None

class CarePlanStepCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    due_time: Optional[datetime] = None

class MedicationAdministration(BaseModel):
    administered_time: Optional[datetime] = None

class CarePlanStatusUpdate(BaseModel):
    status: str

# FastAPI App
app = FastAPI(title="MediPresence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth functions
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Async logging
def log_action(user_id: int, action: str, details: str):
    threading.Thread(target=_write_log, args=(user_id, action, details)).start()

def _write_log(user_id: int, action: str, details: str):
    db = SessionLocal()
    log = AuditLog(user_id=user_id, action=action, details=details)
    db.add(log)
    db.commit()
    db.close()

# Monitoring Threads
def shift_monitor():
    while True:
        db = SessionLocal()
        now = datetime.utcnow()
        presences = db.query(StaffPresence).filter(StaffPresence.status == "on-duty").all()
        for presence in presences:
            if presence.shift_end and now > presence.shift_end:
                alert = Alert(
                    alert_type="shift_overdue",
                    message=f"Staff member (ID: {presence.user_id}) exceeded shift time",
                    priority="high",
                    related_user_id=presence.user_id
                )
                db.add(alert)
                asyncio.run(manager.broadcast({"type": "alert", "data": "Shift overdue detected"}))
        db.commit()
        db.close()
        asyncio.run(asyncio.sleep(60))

def idle_monitor():
    while True:
        db = SessionLocal()
        now = datetime.utcnow()
        presences = db.query(StaffPresence).filter(StaffPresence.status == "on-duty").all()
        for presence in presences:
            if presence.last_active and (now - presence.last_active).seconds > 600:  # 10 min
                if presence.activity != "idle":
                    presence.activity = "idle"
                    asyncio.run(manager.broadcast({"type": "status_update", "user_id": presence.user_id, "activity": "idle"}))
        db.commit()
        db.close()
        asyncio.run(asyncio.sleep(30))

def emergency_alert_monitor():
    while True:
        db = SessionLocal()
        presences = db.query(StaffPresence).filter(StaffPresence.status == "on-duty").all()
        for presence in presences:
            # Check if doctor offline unexpectedly
            user = db.query(User).filter(User.id == presence.user_id).first()
            if user and user.role == "doctor":
                if (datetime.utcnow() - presence.last_active).seconds > 1800:  # 30 min
                    alert = Alert(
                        alert_type="doctor_offline",
                        message=f"Doctor {user.full_name} inactive for 30+ minutes",
                        priority="critical",
                        related_user_id=user.id
                    )
                    db.add(alert)
                    asyncio.run(manager.broadcast({"type": "emergency_alert", "message": alert.message}))
        db.commit()
        db.close()
        asyncio.run(asyncio.sleep(120))

# Start monitoring threads
threading.Thread(target=shift_monitor, daemon=True).start()
threading.Thread(target=idle_monitor, daemon=True).start()
threading.Thread(target=emergency_alert_monitor, daemon=True).start()

# API Endpoints
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
    
    # Create presence record
    presence = StaffPresence(user_id=new_user.id)
    db.add(presence)
    db.commit()
    
    return {"message": "User created successfully", "user_id": new_user.id}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Clock in
    shift = Shift(user_id=db_user.id, clock_in=datetime.utcnow(), date=datetime.utcnow().strftime("%Y-%m-%d"))
    db.add(shift)
    
    # Update presence
    presence = db.query(StaffPresence).filter(StaffPresence.user_id == db_user.id).first()
    if presence:
        presence.status = "on-duty"
        presence.activity = "active"
        presence.shift_start = datetime.utcnow()
        presence.last_active = datetime.utcnow()
    
    db.commit()
    log_action(db_user.id, "login", f"User {db_user.username} logged in")
    
    token = create_access_token({"sub": db_user.username})
    return {"token": token, "role": db_user.role, "user_id": db_user.id, "full_name": db_user.full_name}

@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "role": current_user.role, "full_name": current_user.full_name}

@app.get("/staff/presence")
def get_staff_presence(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
def update_status(update: StatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
    log_action(current_user.id, "status_update", f"Status: {update.status}, Activity: {update.activity}")
    
    asyncio.run(manager.broadcast({"type": "status_update", "user_id": current_user.id}))
    return {"message": "Status updated"}

@app.post("/patients")
def create_patient(patient: PatientCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_patient = Patient(**patient.dict())
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    log_action(current_user.id, "patient_created", f"Patient {patient.name} registered")
    return {"message": "Patient created", "patient_id": new_patient.id}

@app.get("/patients")
def get_patients(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    patients = db.query(Patient).all()
    return patients

@app.post("/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_task = Task(**task.dict(), assigned_by=current_user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    asyncio.run(manager.broadcast({"type": "new_task", "task_id": new_task.id}))
    log_action(current_user.id, "task_created", f"Task '{task.title}' assigned")
    return {"message": "Task created", "task_id": new_task.id}

@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "admin":
        tasks = db.query(Task).all()
    else:
        tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
    return tasks

@app.get("/patients/{patient_id}/vitals")
def get_patient_vitals(patient_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = db.query(VitalRecord).filter(VitalRecord.patient_id == patient_id).order_by(VitalRecord.recorded_at.desc()).all()
    response = []
    for record in records:
        response.append({
            "id": record.id,
            "patient_id": record.patient_id,
            "temperature": record.temperature,
            "blood_pressure": record.blood_pressure,
            "pulse": record.pulse,
            "respiration_rate": record.respiration_rate,
            "oxygen_saturation": record.oxygen_saturation,
            "notes": record.notes,
            "recorded_at": record.recorded_at.isoformat() if record.recorded_at else None,
            "recorded_by": record.recorded_by
        })
    return response

@app.post("/patients/{patient_id}/vitals")
def add_patient_vitals(patient_id: int, vitals: VitalCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    record = VitalRecord(
        patient_id=patient_id,
        recorded_by=current_user.id,
        temperature=vitals.temperature,
        blood_pressure=vitals.blood_pressure,
        pulse=vitals.pulse,
        respiration_rate=vitals.respiration_rate,
        oxygen_saturation=vitals.oxygen_saturation,
        notes=vitals.notes
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    log_action(current_user.id, "vitals_recorded", f"Vitals recorded for patient {patient_id}")
    return {"message": "Vitals recorded", "record_id": record.id}

@app.get("/patients/{patient_id}/medications")
def get_patient_medications(patient_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meds = db.query(MedicationSchedule).filter(MedicationSchedule.patient_id == patient_id).order_by(MedicationSchedule.next_dose_time.asc()).all()
    response = []
    for med in meds:
        response.append({
            "id": med.id,
            "patient_id": med.patient_id,
            "medication_name": med.medication_name,
            "dosage": med.dosage,
            "route": med.route,
            "frequency_hours": med.frequency_hours,
            "start_time": med.start_time.isoformat() if med.start_time else None,
            "next_dose_time": med.next_dose_time.isoformat() if med.next_dose_time else None,
            "last_administered_at": med.last_administered_at.isoformat() if med.last_administered_at else None,
            "status": med.status,
            "assigned_nurse_id": med.assigned_nurse_id
        })
    return response

@app.post("/patients/{patient_id}/medications")
def add_patient_medication(patient_id: int, medication: MedicationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    start_time = medication.start_time or datetime.utcnow()
    next_dose = start_time
    med = MedicationSchedule(
        patient_id=patient_id,
        medication_name=medication.medication_name,
        dosage=medication.dosage,
        route=medication.route,
        frequency_hours=medication.frequency_hours,
        start_time=start_time,
        next_dose_time=next_dose,
        assigned_nurse_id=medication.assigned_nurse_id,
        created_by=current_user.id
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    log_action(current_user.id, "medication_added", f"Medication {med.medication_name} scheduled for patient {patient_id}")
    return {"message": "Medication scheduled", "medication_id": med.id}

@app.post("/medications/{medication_id}/mark-administered")
def mark_medication_administered(medication_id: int, admin: MedicationAdministration, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    med = db.query(MedicationSchedule).filter(MedicationSchedule.id == medication_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication schedule not found")
    admin_time = admin.administered_time or datetime.utcnow()
    med.last_administered_at = admin_time
    med.next_dose_time = admin_time + timedelta(hours=med.frequency_hours)
    med.status = "scheduled"
    db.commit()
    log_action(current_user.id, "medication_administered", f"Medication {med.medication_name} administered for patient {med.patient_id}")
    return {"message": "Medication marked as administered", "next_dose_time": med.next_dose_time.isoformat() if med.next_dose_time else None}

@app.get("/patients/{patient_id}/care-plan")
def get_care_plan(patient_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    steps = db.query(CarePlanStep).filter(CarePlanStep.patient_id == patient_id).order_by(CarePlanStep.due_time.asc()).all()
    response = []
    for step in steps:
        response.append({
            "id": step.id,
            "patient_id": step.patient_id,
            "title": step.title,
            "description": step.description,
            "assigned_to": step.assigned_to,
            "due_time": step.due_time.isoformat() if step.due_time else None,
            "status": step.status,
            "created_at": step.created_at.isoformat() if step.created_at else None,
            "completed_at": step.completed_at.isoformat() if step.completed_at else None
        })
    return response

@app.post("/patients/{patient_id}/care-plan")
def add_care_plan_step(patient_id: int, step: CarePlanStepCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    new_step = CarePlanStep(
        patient_id=patient_id,
        title=step.title,
        description=step.description,
        assigned_to=step.assigned_to,
        due_time=step.due_time,
        created_by=current_user.id
    )
    db.add(new_step)
    db.commit()
    db.refresh(new_step)
    log_action(current_user.id, "care_plan_added", f"Care plan step '{new_step.title}' created for patient {patient_id}")
    return {"message": "Care plan step created", "step_id": new_step.id}

@app.post("/care-plan/{step_id}/status")
def update_care_plan_status(step_id: int, status_update: CarePlanStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    step = db.query(CarePlanStep).filter(CarePlanStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Care plan step not found")
    step.status = status_update.status
    if status_update.status == "completed":
        step.completed_at = datetime.utcnow()
    db.commit()
    log_action(current_user.id, "care_plan_update", f"Care plan step {step_id} marked as {status_update.status}")
    return {"message": "Care plan status updated"}

@app.get("/alerts")
def get_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alerts = db.query(Alert).filter(Alert.acknowledged == False).order_by(Alert.created_at.desc()).all()
    return alerts

@app.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    return {"message": "Alert acknowledged"}

@app.get("/audit-logs")
def get_audit_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    return logs

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast({"type": "message", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)