# 🏥 MediPresence - Hospital Management System

A comprehensive hospital management system with real-time staff presence tracking, patient management, clinical workflows, and task management.

## Features

- ✅ **User Authentication** - JWT-based authentication with role-based access control
- ✅ **Staff Presence Tracking** - Real-time status monitoring (on-duty, off-duty, active, busy, idle)
- ✅ **Patient Management** - Complete patient records with room assignments
- ✅ **Clinical Workflow** - Vitals recording, medication schedules, care plans
- ✅ **Task Management** - Assign and track tasks with priorities
- ✅ **Alerts & Notifications** - Real-time alerts for critical events
- ✅ **Audit Logging** - Complete activity tracking for compliance

## Tech Stack

- **Frontend**: Next.js (React), TypeScript
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL (Supabase/Neon recommended)
- **Deployment**: Vercel (Serverless)

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   npm install
   pip install -r requirements.txt
   ```

2. **Set up database:**
   - Create a PostgreSQL database (Supabase recommended)
   - Run `scripts/init_db.sql` to create tables

3. **Set environment variables:**
   ```bash
   export DATABASE_URL="your-postgres-connection-string"
   export SECRET_KEY="your-secret-key"
   ```

4. **Run development server:**
   ```bash
   npm run dev
   ```

### Deploy to Vercel

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

Quick steps:
1. Set up PostgreSQL database (Supabase recommended)
2. Push code to GitHub
3. Import to Vercel
4. Set environment variables (`DATABASE_URL`, `SECRET_KEY`)
5. Deploy!

## Project Structure

```
├── api/                 # Python API routes (Vercel serverless)
│   ├── index.py        # Main API handler
│   ├── db.py           # Database models
│   └── auth.py         # Authentication
├── pages/              # Next.js pages
│   ├── index.tsx       # Login/Register
│   └── dashboard.tsx   # Main dashboard
├── styles/             # CSS styles
├── scripts/            # Database scripts
└── vercel.json        # Vercel configuration
```

## Default Login Credentials

After setting up the database, register a new user through the web interface, or create an admin user:

```sql
-- Example: Create admin user (password: AdminPass123!)
-- Use the registration endpoint or create directly in database
```

## Database Setup

1. **Recommended: Supabase** (Free tier available)
   - Sign up at https://supabase.com
   - Create new project
   - Run `scripts/init_db.sql` in SQL Editor

2. **Alternative: Neon** (Serverless PostgreSQL)
   - Sign up at https://neon.tech
   - Create database
   - Run `scripts/init_db.sql`

## Environment Variables

Required:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key (generate with `openssl rand -hex 32`)

## Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Detailed deployment guide
- [README_VERCEL.md](README_VERCEL.md) - Vercel-specific instructions

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.

