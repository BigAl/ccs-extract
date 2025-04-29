# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
COPY setup.py .

# Install dependencies
RUN pip install --no-cache-dir reportlab && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e ".[dev]"

# Copy the rest of the application
COPY . .

# Create necessary directories and set up configuration
RUN mkdir -p input output && \
    cp transaction_config.template.json transaction_config.json && \
    chmod 755 input output && \
    chmod 644 transaction_config.json && \
    chmod g+w /app/output

# Create a non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set the entrypoint
ENTRYPOINT ["python", "ccs_extract.py"] 