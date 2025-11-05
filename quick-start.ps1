# WorkHub Quick Start Script
# This script will build and start the WorkHub application in Docker

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  WorkHub Task Management System" -ForegroundColor Cyan
Write-Host "  Docker Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
Write-Host ""
Write-Host "Checking environment configuration..." -ForegroundColor Yellow
if (!(Test-Path .env)) {
    Write-Host "✓ Creating .env file from template..." -ForegroundColor Green
    Copy-Item .env.example .env
    Write-Host "  Please edit .env file to configure your environment" -ForegroundColor Yellow
} else {
    Write-Host "✓ .env file exists" -ForegroundColor Green
}

# Build Docker images
Write-Host ""
Write-Host "Building Docker images..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first run..." -ForegroundColor Gray
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Build completed successfully" -ForegroundColor Green

# Start containers
Write-Host ""
Write-Host "Starting containers..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to start containers!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ All containers started" -ForegroundColor Green

# Wait for services to be ready
Write-Host ""
Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check container status
Write-Host ""
Write-Host "Checking container status..." -ForegroundColor Yellow
docker-compose ps

# Test backend health
Write-Host ""
Write-Host "Testing backend API..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method Get -TimeoutSec 10
    Write-Host "✓ Backend is healthy: $($response.message)" -ForegroundColor Green
} catch {
    Write-Host "⚠ Backend is starting up... (this is normal)" -ForegroundColor Yellow
}

# Display success message
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ WorkHub is now running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access the application:" -ForegroundColor Cyan
Write-Host "  • Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  • Backend:  http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "Default login credentials:" -ForegroundColor Cyan
Write-Host "  • Username: admin" -ForegroundColor White
Write-Host "  • Password: admin123" -ForegroundColor White
Write-Host ""
Write-Host "⚠ Please change the admin password after first login!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  • View logs:    docker-compose logs -f" -ForegroundColor Gray
Write-Host "  • Stop:         docker-compose down" -ForegroundColor Gray
Write-Host "  • Restart:      docker-compose restart" -ForegroundColor Gray
Write-Host ""
Write-Host "For more information, see DOCKER_DEPLOYMENT.md" -ForegroundColor Gray
Write-Host ""

# Open browser
$openBrowser = Read-Host "Open application in browser? (y/N)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    Start-Process "http://localhost:3000"
}

