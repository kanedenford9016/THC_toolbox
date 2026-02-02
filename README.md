# Torn Faction War Calculator

A secure, professional web application for managing faction war payouts in Torn.com. Features encrypted data storage, comprehensive audit logging, automatic member synchronization, and professional PDF report generation.

## Features

- **Secure Authentication**: Torn API key validation with faction admin role verification
- **Session Management**: 24-hour access tokens with 7-day refresh tokens and 30-minute inactivity auto-logout
- **Encrypted Data**: Bank-level encryption for sensitive fields (API keys, payouts, bonuses)
- **War Session Management**: Single active war session tracking with custom naming
- **Member Synchronization**: Automatic member sync from Torn API with status flagging for members who left
- **Payout Calculator**: Flat-rate calculator with optional per-member bonuses and "Other" payments
- **PDF Reports**: Professional blue/gray color-schemed PDF war reports
- **Audit Logging**: Comprehensive logging of all actions with 30-day retention and archival
- **Rate Limiting**: 80 requests/minute to Torn API with intelligent queuing
- **Compliance**: Read-only archive access for compliance audits

## Tech Stack

### Backend
- Python 3.11.8
- Flask (REST API)
- PostgreSQL (Vercel Postgres with SSL)
- Cryptography (Fernet encryption)
- PyJWT (Authentication)
- ReportLab (PDF generation)

### Frontend
- React 18
- React Router
- Axios (API client)

### Deployment
- Vercel (Frontend & Backend)
- Vercel Postgres (Database with SSL)
- Vercel Cron (Monthly log archival)

## Project Structure

```
torn_web_toolbox/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   └── models.py              # Database models
│   │   ├── routes/
│   │   │   ├── auth_routes.py         # Authentication endpoints
│   │   │   ├── war_routes.py          # War session endpoints
│   │   │   ├── member_routes.py       # Member management endpoints
│   │   │   ├── payment_routes.py      # Other payments endpoints
│   │   │   └── export_routes.py       # PDF export & archive endpoints
│   │   ├── services/
│   │   │   ├── auth.py                # Authentication service
│   │   │   ├── torn_api.py            # Torn API integration
│   │   │   ├── calculator.py          # Payout calculator
│   │   │   ├── war_session.py         # War session management
│   │   │   └── pdf_report.py          # PDF generation
│   │   └── utils/
│   │       └── encryption.py          # Encryption utilities
│   ├── config/
│   │   ├── settings.py                # Application configuration
│   │   └── database.py                # Database connection
│   ├── migrations/
│   │   └── 001_initial_schema.sql     # Database schema
│   ├── scripts/
│   │   └── archive_logs.py            # Archival cron script
│   ├── app.py                         # Flask application entry point
│   ├── requirements.txt               # Python dependencies
│   └── .env.example                   # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── components/                # React components (to be created)
│   │   ├── pages/                     # Page components (to be created)
│   │   ├── services/
│   │   │   └── api.js                 # API client
│   │   └── utils/                     # Utility functions (to be created)
│   ├── public/                        # Static assets
│   └── package.json                   # npm dependencies
├── vercel.json                        # Vercel configuration
└── README.md                          # This file
```

## Setup Instructions

### Prerequisites

- Python 3.11.8
- Node.js 18+ and npm
- PostgreSQL (or Vercel Postgres account)
- Vercel account
- Torn.com API key with faction admin permissions

### 1. Clone and Setup Environment

```powershell
cd e:\Projects\torn_web_toolbox

# Backend setup
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Create .env file from template
copy .env.example .env
```

### 2. Configure Environment Variables

Edit `backend/.env` with your credentials:

```env
# Generate encryption key using Python:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_MASTER_KEY=your-generated-key-here

# Generate JWT secret (any secure random string)
JWT_SECRET=your-secure-random-string

# Your PostgreSQL connection string
POSTGRES_URL=postgresql://user:password@host:5432/database?sslmode=require

# Torn API configuration
TORN_API_BASE_URL=https://api.torn.com/v2
RATE_LIMIT_PER_MINUTE=80
```

### 3. Database Setup

#### Local Development with PostgreSQL

1. Install PostgreSQL and pgAdmin4
2. Create a new database: `torn_war_calculator`
3. Run the migration script:

```powershell
cd backend
$env:POSTGRES_URL="postgresql://localhost:5432/torn_war_calculator?sslmode=require"
psql -U postgres -d torn_war_calculator -f migrations/001_initial_schema.sql
```

#### Production with Vercel Postgres

1. Go to Vercel Dashboard → Storage → Create Database → Postgres
2. Copy the connection string
3. Update `POSTGRES_URL` in environment variables
4. Vercel Postgres includes SSL by default

### 4. Run Backend Locally

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python app.py
```

Backend will run on `http://localhost:5000`

### 5. Setup Frontend

```powershell
cd frontend
npm install

# Create .env file
echo "REACT_APP_BACKEND_API_URL=http://localhost:5000" > .env

npm start
```

Frontend will run on `http://localhost:3000`

## Deployment to Vercel

### 1. Install Vercel CLI

```powershell
npm install -g vercel
```

### 2. Link Project to Vercel

```powershell
cd e:\Projects\torn_web_toolbox
vercel
```

Follow the prompts to create a new project.

### 3. Configure Environment Variables in Vercel

Go to Vercel Dashboard → Settings → Environment Variables and add:

- `POSTGRES_URL` - Your Vercel Postgres connection string
- `ENCRYPTION_MASTER_KEY` - Generated encryption key
- `JWT_SECRET` - Generated JWT secret
- `FLASK_SECRET_KEY` - Generated Flask secret
- `TORN_API_BASE_URL` - `https://api.torn.com/v2`
- `RATE_LIMIT_PER_MINUTE` - `80`
- `REACT_APP_BACKEND_API_URL` - Your Vercel backend URL (e.g., `https://your-project.vercel.app/api`)

### 4. Deploy

```powershell
vercel --prod
```

### 5. Configure SSL for Database

Vercel Postgres includes SSL by default. No additional configuration needed.

For external PostgreSQL:

1. Obtain SSL certificates from your PostgreSQL provider
2. Upload certificates to Vercel secrets
3. Update connection string with SSL parameters:
   ```
   postgresql://user:pass@host:5432/db?sslmode=require&sslcert=/path/to/cert&sslkey=/path/to/key
   ```

## API Documentation

### Authentication

#### POST `/auth/login`
Login with Torn API key
```json
Request: { "torn_api_key": "your_key" }
Response: { "message": "Login successful", "user": {...} }
```

#### POST `/auth/refresh`
Refresh access token

#### POST `/auth/logout`
Logout and clear session

### War Sessions

#### POST `/war/create`
Create new war session
```json
Request: { "war_name": "War vs Example - Jan 2026" }
```

#### GET `/war/active`
Get currently active war session

#### POST `/war/{session_id}/complete`
Mark war session as completed

#### POST `/war/{session_id}/calculate`
Calculate payouts
```json
Request: {
  "total_earnings": 50000000,
  "price_per_hit": 10000
}
```

#### GET `/war/history`
Get all completed war sessions

### Members

#### POST `/members/refresh`
Sync members from Torn API
```json
Request: { "war_session_id": "uuid" }
```

#### GET `/members/session/{session_id}`
Get all members for a session

#### POST `/members/{member_id}/bonus`
Add/update member bonus
```json
Request: {
  "bonus_amount": 50000,
  "bonus_reason": "MVP performance"
}
```

#### DELETE `/members/{member_id}/bonus`
Remove member bonus

### Payments

#### POST `/payments/{session_id}`
Create other payment
```json
Request: {
  "amount": 1000000,
  "description": "Territory upgrade costs"
}
```

#### GET `/payments/{session_id}`
Get all other payments for session

#### PUT `/payments/{payment_id}`
Update other payment

#### DELETE `/payments/{payment_id}`
Delete other payment

### Export & Archive

#### GET `/export/{session_id}/pdf?user_name=AdminName`
Download PDF war report

#### GET `/archive/?start_date=2026-01-01&end_date=2026-01-31&action_type=PAYOUT_CALCULATED&limit=100`
Query archived audit logs

## Security Features

1. **Bank-Level Encryption**: All sensitive data encrypted at rest using Fernet (AES-128)
2. **SSL/TLS**: All connections encrypted in transit (HTTPS)
3. **Session Security**: HTTP-only cookies, CSRF protection
4. **Rate Limiting**: Protection against API abuse
5. **Audit Trail**: Complete logging of all actions
6. **Data Retention**: Automated archival with compliance access

## Usage

1. **Login**: Enter your Torn API key (must have faction admin permissions)
2. **Create War Session**: Click "New War" and enter a name or use the default
3. **Sync Members**: Click "Refresh from Torn" to fetch current member list and hit counts
4. **Calculate Payouts**:
   - Enter total war earnings
   - Set price per hit
   - Add bonuses for specific members (optional)
   - Add "Other" payments (optional)
   - Click "Calculate"
5. **Review Results**: See breakdown of all payouts and remaining balance
6. **Export PDF**: Click "Export PDF" for a professional report
7. **Complete War**: Mark war as complete when finished

## Troubleshooting

### Backend Issues

**Database Connection Failed**
- Verify `POSTGRES_URL` is correct
- Ensure SSL is enabled: `?sslmode=require`
- Check firewall rules allow connections

**Encryption Errors**
- Regenerate `ENCRYPTION_MASTER_KEY` if corrupted
- Ensure key is valid base64-encoded Fernet key

**Torn API Errors**
- Verify API key has correct permissions
- Check rate limit (80/min)
- Ensure `TORN_API_BASE_URL` is `https://api.torn.com/v2`

### Frontend Issues

**CORS Errors**
- Verify `REACT_APP_BACKEND_API_URL` points to correct backend
- Check backend CORS configuration allows frontend origin

**Authentication Failed**
- Clear browser cookies
- Check access token expiry (24 hours)
- Verify refresh token is valid (7 days)

## Contributing

This is a private faction tool. For issues or feature requests, contact the faction leadership.

## License

Proprietary - For internal faction use only.

## Support

For technical support, contact the faction tech admin or refer to the Torn API documentation at https://www.torn.com/api.html
