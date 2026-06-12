# ── Hugging Face Spaces requires port 7860 ──────────────────────────────────
FROM python:3.10-slim

# HF Spaces requires a non-root user called "user" with uid 1000
RUN useradd -m -u 1000 user
USER user

# Set working directory
WORKDIR /app

# Copy requirements first (better Docker layer caching)
COPY --chown=user ./requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy all project files
COPY --chown=user . /app

# Hugging Face Spaces MUST use port 7860
EXPOSE 7860

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
