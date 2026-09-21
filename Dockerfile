# Dockerfile

# Use official Python lightweight image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose ports for Streamlit (8501) and FastAPI (8001, matching the README)
EXPOSE 8501
EXPOSE 8001

# Script to run both services (Simplified version)
# In production, use docker-compose to separate them
CMD ["sh", "-c", "python -m uvicorn api:app --host 0.0.0.0 --port 8001 & streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]
