# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from root if possible, or create one here
# For now, let's create a minimal requirements.txt for the backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to have access to phase_2 and phase_3
COPY . .

# Set PYTHONPATH to include the root
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "phase_4.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
