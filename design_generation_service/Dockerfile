# Start with the Python slim base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (only fonts are needed now)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-color-emoji \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and service account key
COPY main.py .
COPY models.py .
COPY sunlit-runway-472202-p8-75230f6c1db6.json .
COPY templates/ ./templates/


# Expose the app port
EXPOSE 8080

# Command to run the application
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "main:app", "--timeout", "600"]