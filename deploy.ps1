# ═══════════════════════════════════════════════════════════
# ColorPro — One-Command Deploy Script
# ═══════════════════════════════════════════════════════════

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host " ColorPro — Deployment Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build the Docker image
Write-Host "[1/3] Building Docker image..." -ForegroundColor Yellow
docker compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "  Image built successfully." -ForegroundColor Green

# Step 2: Start the container
Write-Host ""
Write-Host "[2/3] Starting ColorPro container..." -ForegroundColor Yellow
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to start container!" -ForegroundColor Red
    exit 1
}
Write-Host "  Container started." -ForegroundColor Green

# Step 3: Create default admin user (if it doesn't exist)
Write-Host ""
Write-Host "[3/3] Ensuring admin user exists..." -ForegroundColor Yellow
$pythonCmd = @"
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', '', 'admin123')
    print('  Admin user created (admin / admin123)')
else:
    print('  Admin user already exists.')
"@

docker compose exec colorpro python manage.py shell -c $pythonCmd
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Warning: Could not create admin user (container may still be starting)." -ForegroundColor Yellow
    Write-Host "  Wait a few seconds and run:" -ForegroundColor Yellow
    Write-Host "    docker compose exec colorpro python manage.py createsuperuser" -ForegroundColor Gray
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host " ColorPro is running!" -ForegroundColor Green
Write-Host " Open: http://localhost:8000" -ForegroundColor White
Write-Host " Login: admin / admin123" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Gray
Write-Host "  docker compose logs -f        # View logs" -ForegroundColor Gray
Write-Host "  docker compose stop            # Stop" -ForegroundColor Gray
Write-Host "  docker compose down            # Stop + remove container" -ForegroundColor Gray
Write-Host "  docker compose down -v         # Stop + remove data" -ForegroundColor Gray
Write-Host ""
