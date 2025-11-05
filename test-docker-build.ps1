# Docker Build Verification Script
Write-Host "=== Docker Build Verification ===" -ForegroundColor Cyan

Write-Host "`n1. Checking Docker and Docker Compose..." -ForegroundColor Yellow
docker --version
docker-compose --version

Write-Host "`n2. Checking for .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file exists" -ForegroundColor Green
} else {
    Write-Host "⚠ .env file not found. Creating template..." -ForegroundColor Yellow
    @"
# Database Passwords
SA_PASSWORD=YourStrong!Passw0rd

# Mail Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=
EMAIL_NOTIFICATIONS_ENABLED=false
"@ | Out-File -FilePath ".env" -Encoding utf8
    Write-Host "✓ Created .env file with defaults" -ForegroundColor Green
}

Write-Host "`n3. Checking frontend package.json for moment.js..." -ForegroundColor Yellow
$packageJson = Get-Content "workhub-frontend/package.json" -Raw | ConvertFrom-Json
if ($packageJson.dependencies.moment) {
    Write-Host "✓ moment.js found in dependencies" -ForegroundColor Green
} else {
    Write-Host "✗ moment.js missing - this will cause build failure" -ForegroundColor Red
}

Write-Host "`n4. Checking backend files..." -ForegroundColor Yellow
if (Test-Path "workhub-backend/start.sh") {
    Write-Host "✓ start.sh exists" -ForegroundColor Green
} else {
    Write-Host "✗ start.sh missing" -ForegroundColor Red
}

if (Test-Path "workhub-frontend/nginx.conf") {
    Write-Host "✓ nginx.conf exists" -ForegroundColor Green
} else {
    Write-Host "✗ nginx.conf missing" -ForegroundColor Red
}

Write-Host "`n5. Stopping any existing containers..." -ForegroundColor Yellow
docker-compose down

Write-Host "`n6. Building Docker images..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Gray

# Build with progress output
docker-compose build --progress=plain 2>&1 | Tee-Object -FilePath "docker-build.log"

Write-Host "`n=== Build Complete ===" -ForegroundColor Cyan
Write-Host "Check docker-build.log for detailed output" -ForegroundColor Gray

