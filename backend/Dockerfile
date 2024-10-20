# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose the port that the app runs on
# Cloud Run expects the service to listen on the port specified by the PORT environment variable, default 8080
EXPOSE 8080

# Set environment variables for gRPC
ENV GRPC_PORT=50051

# Define the default command to run the app using Uvicorn
CMD ["uvicorn", "microservice:app", "--host", "0.0.0.0", "--port", "8080"]
