FROM python:3.12-slim

# Set workdir
WORKDIR /app

# Install system dependencies if needed (e.g., gcc, build-essential, etc.)
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and metadata first for caching
COPY pyproject.toml README.md ./
RUN pip install --upgrade pip && pip install .

# Copy app code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
