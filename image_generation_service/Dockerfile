# Use the full Python 3.10 image, not the 'slim' version.
# The full image includes more system-level libraries, which resolves
# low-level crashes caused by preview SDKs like the one for Imagen 3.
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY . .

# Command to run the application using Gunicorn
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "main:app", "--timeout", "300"]

