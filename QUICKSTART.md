# Quick Start Guide

## Development Setup

1. Run setup script:
```powershell
.\setup.ps1
```

2. Update `backend/.env` with your PostgreSQL connection:
```env
POSTGRES_URL=postgresql://user:password@localhost:5432/torn_war_calculator?sslmode=require
```

3. Run database migrations:
```powershell
psql -U postgres -d torn_war_calculator -f backend/migrations/001_initial_schema.sql
```

4. Start backend (Terminal 1):
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python app.py
```

5. Start frontend (Terminal 2):
```powershell
cd frontend
npm start
```

## Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

## First Login

1. Get your Torn API key from https://www.torn.com/preferences.php#tab=api
2. Ensure you have faction admin permissions (Leader, Co-leader, or Officer)
3. Enter your API key on the login page

## Deployment

See README.md for full deployment instructions to Vercel.
