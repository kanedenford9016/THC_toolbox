# Torn Faction War Calculator - Setup Script
# Run this script to set up the development environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Torn War Calculator - Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
    
    if ($pythonVersion -notmatch "Python 3\.11") {
        Write-Host "⚠ Warning: Python 3.11.8 recommended, but continuing..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Python not found! Please install Python 3.11.8" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "Checking Node.js version..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found! Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create virtual environment
Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
cd backend
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists, skipping..." -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment and install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "✓ Python dependencies installed" -ForegroundColor Green

# Generate encryption key if .env doesn't exist
Write-Host ""
Write-Host "Checking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    
    # Generate encryption key
    $encryptionKey = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    $jwtSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    $flaskSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    
    # Update .env file
    (Get-Content ".env") -replace "ENCRYPTION_MASTER_KEY=your-256-bit-base64-encoded-key-here", "ENCRYPTION_MASTER_KEY=$encryptionKey" | Set-Content ".env"
    (Get-Content ".env") -replace "JWT_SECRET=your-jwt-secret-key-here", "JWT_SECRET=$jwtSecret" | Set-Content ".env"
    (Get-Content ".env") -replace "FLASK_SECRET_KEY=your-flask-secret-key-here", "FLASK_SECRET_KEY=$flaskSecret" | Set-Content ".env"
    
    Write-Host "✓ .env file created with generated keys" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠ IMPORTANT: Update POSTGRES_URL in backend/.env with your database connection string!" -ForegroundColor Yellow
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

cd ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Frontend Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Install frontend dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
cd frontend
if (Test-Path "node_modules") {
    Write-Host "node_modules already exists, skipping..." -ForegroundColor Yellow
} else {
    npm install
    Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
}

# Create frontend .env
if (-not (Test-Path ".env")) {
    Write-Host "Creating frontend .env file..." -ForegroundColor Yellow
    "REACT_APP_BACKEND_API_URL=http://localhost:5000" | Out-File -FilePath ".env" -Encoding utf8
    Write-Host "✓ Frontend .env file created" -ForegroundColor Green
}

cd ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Update backend/.env with your PostgreSQL connection string (POSTGRES_URL)"
Write-Host "2. Run database migrations: psql -U postgres -d torn_war_calculator -f backend/migrations/001_initial_schema.sql"
Write-Host "3. Start backend: cd backend; .\venv\Scripts\Activate.ps1; python app.py"
Write-Host "4. Start frontend: cd frontend; npm start"
Write-Host ""
Write-Host "For deployment instructions, see README.md" -ForegroundColor Cyan
Write-Host ""
