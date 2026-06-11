FROM python:3.9

# Create a non-root user for security (Hugging Face requirement)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirements and install them
COPY --chown=user ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy the rest of your backend application files
COPY --chown=user . /app

# Hugging Face explicitly requires port 7860
CMD ["uvicorn", "your_file_name:app", "--host", "0.0.0.0", "--port", "7860"]