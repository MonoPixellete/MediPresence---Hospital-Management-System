# MediPresence - Vercel Deployment

This is the Vercel-compatible version of the MediPresence hospital management system.

## Quick Start

1. **Set up database** (Supabase recommended - free tier available)
   - Create account at https://supabase.com
   - Create new project
   - Run the SQL script from `scripts/init_db.sql` in the SQL Editor

2. **Deploy to Vercel**
   ```bash
   npm install -g vercel
   vercel login
   vercel
   ```

3. **Set environment variables in Vercel dashboard:**
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `SECRET_KEY`: Generate with `openssl rand -hex 32`

4. **Redeploy:**
   ```bash
   vercel --prod
   ```

## Project Structure

```
├── api/                 # Python API routes (Vercel serverless functions)
│   ├── index.py        # Main API handler
│   ├── db.py           # Database models and connection
│   └── auth.py         # Authentication utilities
├── pages/              # Next.js pages
│   ├── index.tsx       # Login/Register page
│   └── dashboard.tsx   # Main dashboard
├── styles/             # CSS styles
├── vercel.json         # Vercel configuration
├── package.json        # Node.js dependencies
├── requirements.txt    # Python dependencies
└── DEPLOYMENT.md       # Detailed deployment guide
```

## Database Options

### Recommended: Supabase (Free)
- 500MB database
- Easy setup
- Built-in SQL editor
- Connection pooling included

### Alternative: Neon
- Serverless PostgreSQL
- Free tier available
- Auto-scaling

## Features

- ✅ User authentication (JWT)
- ✅ Role-based access (Admin, Doctor, Nurse, Receptionist, Staff)
- ✅ Real-time staff presence tracking
- ✅ Patient management
- ✅ Task management
- ✅ Clinical workflow (vitals, medications, care plans)
- ✅ Alerts and notifications
- ✅ Audit logging

## Environment Variables

Required:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key

## Local Development

1. Install dependencies:
   ```bash
   npm install
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export DATABASE_URL="your-postgres-url"
   export SECRET_KEY="your-secret-key"
   ```

3. Run Next.js dev server:
   ```bash
   npm run dev
   ```

## Support

See `DEPLOYMENT.md` for detailed instructions and troubleshooting.

