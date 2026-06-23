# ═══════════════════════════════════════════════════════════
# ColorPro — Unified Production Dockerfile
# Builds frontend + backend into a single deployable image
# ═══════════════════════════════════════════════════════════

# ── Stage 1: Build the Next.js frontend into static HTML ──
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund

COPY frontend/ .
RUN npm run build
# Produces static files in /frontend/out/

# ── Stage 2: Python production image ──
FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=shade_project.settings

WORKDIR /app

# Install system dependencies for xhtml2pdf / cairo
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Copy compiled frontend static files into Django's static dir
COPY --from=frontend-builder /frontend/out/ /app/frontend_build/

# Collect static files (frontend + Django admin) into /app/staticfiles/
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Create directories for runtime data
RUN mkdir -p /app/media

EXPOSE 8000

# Run migrations and start gunicorn
CMD sh -c "\
    python manage.py migrate --noinput && \
    gunicorn shade_project.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 3 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile -"
