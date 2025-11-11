"""
Database connection and models for Vercel deployment
Uses PostgreSQL (Supabase recommended)
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Create engine (remove check_same_thread for PostgreSQL)
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models (same as original)
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
    status = Column(String, default="off-duty")
    activity = Column(String, default="idle")
    location = Column(String, default="Unknown")
    shift_start = Column(DateTime, nullable=True)
    shift_end = Column(DateTime, nullable=True)
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
    medical_history = Column(Text, nullable=True)
    vitals = Column(Text, nullable=True)  # JSON string
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
    start_time = Column(DateTime)
    assigned_nurse_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class CarePlanStep(Base):
    __tablename__ = "care_plan_steps"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    title = Column(String)
    description = Column(Text, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="pending")
    due_time = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    assigned_by = Column(Integer, ForeignKey("users.id"))
    priority = Column(String, default="medium")
    status = Column(String, default="pending")
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String)
    message = Column(Text)
    priority = Column(String)
    related_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
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
    break_duration = Column(Integer, default=0)
    overtime = Column(Integer, default=0)
    date = Column(String)

# Initialize database
def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

