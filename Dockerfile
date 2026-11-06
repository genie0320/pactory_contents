# ==============================================================
# Stage 1: Build React/Vite/Tailwind SPA Frontend
# ==============================================================
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==============================================================
# Stage 2: Production Python Backend Runtime
# ==============================================================
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install runtime utilities & SQLite support
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and configuration
COPY src/ ./src
COPY pyproject.toml .

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure data directory structure exists
RUN mkdir -p /app/data/inbox /app/data/archive /app/data/processed /app/data/index /app/data/outputs /app/data/drafts

# Expose public port 8501
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/api/health || exit 1

# Start FastAPI application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8501"]
