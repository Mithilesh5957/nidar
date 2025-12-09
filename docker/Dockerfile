FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose ports
EXPOSE 8000 5760 5762

# Run the application
CMD ["uvicorn", "vps_app:app", "--host", "0.0.0.0", "--port", "8000"]
