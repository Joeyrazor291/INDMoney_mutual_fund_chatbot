FROM python:3.11-slim

WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip

# Copy only necessary application files
COPY phase_1/ ./phase_1/
COPY phase_2/ ./phase_2/
COPY phase_3/ ./phase_3/
COPY phase_4/backend/ ./phase_4/backend/
COPY phase_5/ ./phase_5/
COPY data/ ./data/
# COPY .env .env
# Expose port (Render uses the PORT environment variable natively)
ENV PORT=10000
EXPOSE ${PORT}

# Start command (using shell form to expand the PORT variable)
CMD uvicorn phase_4.backend.main:app --host 0.0.0.0 --port ${PORT}
