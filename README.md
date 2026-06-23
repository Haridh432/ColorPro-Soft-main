cd# ColorPro — Textile Shade Management System

A full-stack system for fabric shade comparison, quality control, and reporting.

## Architecture

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Django + DRF | API, Auth, Admin, PDF Reports |
| Database | SQLite (dev) → PostgreSQL (prod) | Data persistence |
| Frontend | Next.js + Tailwind CSS | QC Manager dashboard |
| Device | ESP32 | Color scanning hardware |
| ML | scikit-learn | Shade clustering |

## Quick Start

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env from example
copy .env.example .env

# Run database migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start dev server
python manage.py runserver 8000
```

**Access:**
- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/
- Token endpoint: `POST http://localhost:8000/api/token/`

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

**Access:** http://localhost:3000

### 3. ESP32 Device

The device fetches the roll queue and submits scans:

```
GET  /api/device/batch/{batch_id}/rolls/     → Get roll queue
POST /api/scans/device/                       → Submit scan
PATCH /api/device/roll/{roll_id}/hold/        → Hold roll
```

**4-Button Mapping:**
| Button | Action |
|---|---|
| Confirm Scan | POST scan data, advance to next roll |
| Retry Scan | Discard reading, re-scan same roll |
| Hold Roll | Mark as held, skip to next |
| Previous Roll | Navigate back |

## Sample API Calls

```bash
# Create a batch
curl -X POST http://localhost:8000/api/batches/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Batch-001", "description": "Cotton Navy Blue"}'

# Add rolls
curl -X POST http://localhost:8000/api/rolls/bulk/ \
  -H "Content-Type: application/json" \
  -d '{"batch_id": "<uuid>", "roll_numbers": ["R-001", "R-002", "R-003"]}'

# ESP32 scan
curl -X POST http://localhost:8000/api/scans/device/ \
  -H "Content-Type: application/json" \
  -d '{"batch_id": "<uuid>", "roll_id": "<uuid>", "rgb": [42, 75, 130]}'

# Run quality gate
curl -X POST http://localhost:8000/api/compare/<batch_id>/gate/

# Run ML clustering
curl -X POST http://localhost:8000/api/compare/<batch_id>/cluster/

# Generate PDF report
curl -X POST http://localhost:8000/api/reports/generate/<batch_id>/ \
  -H "Authorization: Token <token>"
```

## Quality Gate Thresholds

| Status | ΔE (CIEDE2000) | Action |
|---|---|---|
| ✅ Accepted | ≤ 0.6 | Pass |
| ⚠️ Warning | 0.6 – 0.8 | Flagged for review |
| ❌ Rejected | > 0.8 | Does not meet tolerance |

## Default Credentials

- **Admin:** username `admin` / password `admin123`
