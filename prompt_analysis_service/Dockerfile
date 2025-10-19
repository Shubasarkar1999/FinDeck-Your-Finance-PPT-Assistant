# Start from an official Python runtime as a parent image.
FROM python:3.10-slim

# Install system dependencies for Node.js, Chromium, and Marp CLI.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    chromium \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0

# Add the official Node.js repository and install Node.js.
ENV NODE_MAJOR=20
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs

# Install the Marp CLI and clean up the apt cache.
RUN npm install -g @marp-team/marp-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# This environment variable tells Puppeteer to disable the security sandbox.
ENV CHROME_NO_SANDBOX=true

# --- THIS IS THE FIX ---
# This environment variable explicitly tells Marp/Puppeteer where to find the
# Chromium executable inside the container. This prevents the "silent failure"
# where the process exits successfully but no file is created.
ENV CHROME_PATH=/usr/bin/chromium
# --------------------------

# Set the working directory in the container.
WORKDIR /app

# Copy and install Python dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container.
COPY . .

# Use Gunicorn for production.
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "main:app"]

