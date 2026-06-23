# ═══════════════════════════════════════════════════════════
# ColorPro — One-Command Dev Startup
# Starts both Django backend and Next.js frontend
# ═══════════════════════════════════════════════════════════

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host " ColorPro — Development Server" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── Locate Python (prefer venv) ──
$venvPython = Join-Path $backendDir "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = Join-Path $backendDir "venv\Scripts\python"
}
if (-not (Test-Path $venvPython)) {
    $venvPython = "python"
    Write-Host "  [!] No venv found. Using system Python." -ForegroundColor Yellow
}

function Start-Backend {
    Write-Host "[Backend] Starting Django on http://localhost:8000 ..." -ForegroundColor Green

    # Run migrations silently first
    Write-Host "  Running migrations..." -ForegroundColor Gray
    Start-Process -FilePath $venvPython -ArgumentList "manage.py migrate --noinput" -WorkingDirectory $backendDir -NoNewWindow -Wait 2>$null

    # Start Django dev server
    $backendProcess = Start-Process -FilePath $venvPython -ArgumentList "manage.py runserver 0.0.0.0:8000" -WorkingDirectory $backendDir -PassThru -NoNewWindow
    return $backendProcess
}

function Start-Frontend {
    Write-Host "[Frontend] Starting Next.js on http://localhost:3000 ..." -ForegroundColor Green
    $npmCmd = "npm.cmd"
    $frontendProcess = Start-Process -FilePath $npmCmd -ArgumentList "run dev" -WorkingDirectory $frontendDir -PassThru -NoNewWindow
    return $frontendProcess
}

# ── Start Services ──
$processes = @()

if (-not $FrontendOnly) {
    $processes += Start-Backend
}

if (-not $BackendOnly) {
    $processes += Start-Frontend
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
if (-not $FrontendOnly -and -not $BackendOnly) {
    Write-Host " Both servers are running!" -ForegroundColor Green
    Write-Host " Backend:  http://localhost:8000" -ForegroundColor White
    Write-Host " Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host " Admin:    http://localhost:8000/admin/" -ForegroundColor White
} elseif ($BackendOnly) {
    Write-Host " Backend is running!" -ForegroundColor Green
    Write-Host " API:   http://localhost:8000/api/" -ForegroundColor White
    Write-Host " Admin: http://localhost:8000/admin/" -ForegroundColor White
} else {
    Write-Host " Frontend is running!" -ForegroundColor Green
    Write-Host " Dashboard: http://localhost:3000" -ForegroundColor White
}
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop all servers." -ForegroundColor Gray
Write-Host ""

# ── Keep alive until Ctrl+C ──
try {
    while ($true) {
        Start-Sleep -Seconds 1
        # Check if any process has exited unexpectedly
        foreach ($proc in $processes) {
            if ($proc.HasExited) {
                Write-Host "[!] A server process has stopped unexpectedly (Exit code: $($proc.ExitCode))" -ForegroundColor Red
            }
        }
    }
} finally {
    Write-Host ""
    Write-Host "Shutting down servers..." -ForegroundColor Yellow
    foreach ($proc in $processes) {
        if (-not $proc.HasExited) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "All servers stopped." -ForegroundColor Green
}
