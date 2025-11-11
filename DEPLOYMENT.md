# Deployment Guide for Vercel

This guide will help you deploy the MediPresence application to Vercel with a cloud database.

## Prerequisites

1. A Vercel account (sign up at https://vercel.com)
2. A Supabase account (free tier available at https://supabase.com) OR any PostgreSQL database
3. Git installed on your machine
4. Node.js 18+ installed

## Step 1: Set Up Database (Supabase - Recommended)

### Option A: Using Supabase (Free & Easy)

1. Go to https://supabase.com and create a free account
2. Create a new project
3. Go to **Settings** → **Database**
4. Copy the **Connection string** (URI format)
   - It should look like: `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
5. Save this for later

### Option B: Using Other PostgreSQL Providers

- **Neon** (https://neon.tech) - Serverless PostgreSQL
- **Railway** (https://railway.app) - Easy PostgreSQL setup
- **AWS RDS** - For production
- **Google Cloud SQL** - For production

## Step 2: Initialize Database Tables

1. Connect to your PostgreSQL database using any SQL client (pgAdmin, DBeaver, or Supabase SQL Editor)
2. Run the SQL script below to create all tables:

```sql
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
```

## Step 3: Prepare Your Code

1. Make sure all files are in place:
   - `package.json`
   - `next.config.js`
   - `vercel.json`
   - `requirements.txt`
   - `api/` folder with Python files
   - `pages/` folder with Next.js pages

2. Install dependencies locally (optional, for testing):
```bash
npm install
```

## Step 4: Deploy to Vercel

### Method 1: Using Vercel CLI (Recommended)

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Navigate to your project directory:
```bash
cd /Users/kavya/Downloads/Projectv2
```

4. Deploy:
```bash
vercel
```

5. Follow the prompts:
   - Link to existing project? **No** (first time)
   - Project name: **medipresence** (or your choice)
   - Directory: **./** (current directory)
   - Override settings? **No**

6. Set environment variables:
```bash
vercel env add DATABASE_URL
# Paste your PostgreSQL connection string when prompted

vercel env add SECRET_KEY
# Enter a random secret key (e.g., generate with: openssl rand -hex 32)
```

7. Redeploy with environment variables:
```bash
vercel --prod
```

### Method 2: Using Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Click **Add New Project**
3. Import your Git repository (GitHub/GitLab/Bitbucket)
   - If not using Git, you can drag and drop the folder
4. Configure project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `./`
5. Add Environment Variables:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `SECRET_KEY`: A random secret key (use `openssl rand -hex 32`)
6. Click **Deploy**

## Step 5: Configure API Routes

The API routes are automatically handled by Vercel. Make sure:

1. Your `vercel.json` is configured correctly
2. Python dependencies are in `requirements.txt`
3. API files are in the `api/` directory

## Step 6: Test Your Deployment

1. Visit your Vercel deployment URL (e.g., `https://medipresence.vercel.app`)
2. Register a new user
3. Login and test the dashboard

## Step 7: Add Dummy Data (Optional)

You can create a script to populate initial data:

```python
# scripts/seed_data.py
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api.db import SessionLocal, User, StaffPresence, Patient
from api.auth import hash_password

db = SessionLocal()

# Create admin user
admin = User(
    username="admin1",
    email="admin@example.com",
    hashed_password=hash_password("AdminPass123!"),
    role="admin",
    full_name="Dr. Alice Admin"
)
db.add(admin)
db.commit()

print("Database seeded successfully!")
```

Run it locally with your DATABASE_URL set, or use Supabase SQL Editor.

## Troubleshooting

### Issue: "Module not found" errors
- Make sure all dependencies are in `requirements.txt`
- Check that Python version is compatible (3.9+)

### Issue: Database connection errors
- Verify `DATABASE_URL` is set correctly in Vercel environment variables
- Check that your database allows connections from Vercel's IPs
- For Supabase: Go to Settings → Database → Connection Pooling and use the pooler URL

### Issue: API routes not working
- Check Vercel function logs in the dashboard
- Ensure `api/index.py` is properly formatted
- Verify CORS settings if accessing from different domain

### Issue: Next.js build fails
- Run `npm install` locally to check for dependency issues
- Check `next.config.js` is correct
- Verify TypeScript types if using TypeScript

## Environment Variables Summary

Required environment variables in Vercel:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key (generate with `openssl rand -hex 32`)

Optional:
- `NEXT_PUBLIC_API_BASE`: API base URL (defaults to `/api`)

## Database Recommendations

### For Development/Testing:
- **Supabase Free Tier**: 500MB database, perfect for testing
- **Neon Free Tier**: Serverless PostgreSQL

### For Production:
- **Supabase Pro**: $25/month, better performance
- **AWS RDS**: Enterprise-grade, scalable
- **Google Cloud SQL**: Managed PostgreSQL

## Security Notes

1. **Never commit** `.env` files or database credentials
2. Use Vercel's environment variables for secrets
3. Enable SSL for database connections
4. Use connection pooling for better performance
5. Rotate `SECRET_KEY` regularly in production

## Support

If you encounter issues:
1. Check Vercel function logs
2. Check database connection logs
3. Verify all environment variables are set
4. Test API endpoints using curl or Postman

## Next Steps

After deployment:
1. Set up custom domain (optional)
2. Configure monitoring and alerts
3. Set up automated backups for database
4. Enable Vercel Analytics
5. Configure rate limiting if needed

