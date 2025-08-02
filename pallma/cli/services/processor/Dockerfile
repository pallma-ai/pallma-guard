FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if needed (e.g., gcc, build-essential, etc.)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and metadata first for caching
COPY pyproject.toml README.md ./
RUN pip install --upgrade pip && pip install .

# Copy the rest of the code
COPY . .

CMD ["python", "main.py"] 