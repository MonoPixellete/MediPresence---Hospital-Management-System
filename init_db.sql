-- Database initialization script for PostgreSQL
-- Run this in your PostgreSQL database (Supabase SQL Editor, pgAdmin, etc.)

-- Create Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    full_name VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Staff Presence table
CREATE TABLE IF NOT EXISTS staff_presence (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    status VARCHAR DEFAULT 'off-duty',
    activity VARCHAR DEFAULT 'idle',
    location VARCHAR DEFAULT 'Unknown',
    shift_start TIMESTAMP,
    shift_end TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_patients INTEGER DEFAULT 0
);

-- Create Patients table
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR NOT NULL,
    illness TEXT NOT NULL,
    room_number VARCHAR NOT NULL,
    assigned_doctor_id INTEGER REFERENCES users(id),
    assigned_nurse_id INTEGER REFERENCES users(id),
    medical_history TEXT,
    vitals TEXT,
    admitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR DEFAULT 'admitted'
);

-- Create Vital Records table
CREATE TABLE IF NOT EXISTS vital_records (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    recorded_by INTEGER REFERENCES users(id),
    temperature FLOAT,
    blood_pressure VARCHAR,
    pulse INTEGER,
    respiration_rate INTEGER,
    oxygen_saturation FLOAT,
    notes TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Medication Schedules table
CREATE TABLE IF NOT EXISTS medication_schedules (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    medication_name VARCHAR NOT NULL,
    dosage VARCHAR NOT NULL,
    route VARCHAR,
    frequency_hours INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    assigned_nurse_id INTEGER REFERENCES users(id),
    status VARCHAR DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Care Plan Steps table
CREATE TABLE IF NOT EXISTS care_plan_steps (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    title VARCHAR NOT NULL,
    description TEXT,
    assigned_to INTEGER REFERENCES users(id),
    status VARCHAR DEFAULT 'pending',
    due_time TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    assigned_to INTEGER REFERENCES users(id),
    assigned_by INTEGER REFERENCES users(id),
    priority VARCHAR DEFAULT 'medium',
    status VARCHAR DEFAULT 'pending',
    deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR NOT NULL,
    related_user_id INTEGER REFERENCES users(id),
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP
);

-- Create Audit Logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR NOT NULL,
    details TEXT,
    ip_address VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Shifts table
CREATE TABLE IF NOT EXISTS shifts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    clock_in TIMESTAMP NOT NULL,
    clock_out TIMESTAMP,
    break_duration INTEGER DEFAULT 0,
    overtime INTEGER DEFAULT 0,
    date VARCHAR NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_staff_presence_user_id ON staff_presence(user_id);
CREATE INDEX IF NOT EXISTS idx_patients_doctor ON patients(assigned_doctor_id);
CREATE INDEX IF NOT EXISTS idx_patients_nurse ON patients(assigned_nurse_id);
CREATE INDEX IF NOT EXISTS idx_vital_records_patient ON vital_records(patient_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged);

