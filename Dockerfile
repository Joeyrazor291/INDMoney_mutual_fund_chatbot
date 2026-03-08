FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser binaries
RUN playwright install --with-deps chromium

# Hugging Face Spaces non-root user requirement (UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app

# Copy application files (ensuring user ownership)
COPY --chown=user:user . .

# Build the vectorstore during image creation (bakes database into image)
# This avoids pushing large binary files to Git
RUN python phase_1/chunker.py

# Hugging Face Spaces strictly routes traffic through port 7860
ENV PORT=7860
EXPOSE 7860

# Re-verify port in command to ensure no overrides
CMD ["uvicorn", "phase_4.backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
