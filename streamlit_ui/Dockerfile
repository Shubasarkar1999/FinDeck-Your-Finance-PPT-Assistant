FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Expose the port Streamlit will run on. Cloud Run will map this to 80/443.
EXPOSE 8080

# The command to run the Streamlit app. Cloud Run requires binding to 0.0.0.0 and uses the PORT env var.
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]