# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY setup.py .

# Install dependencies
RUN pip install --no-cache-dir -e .

# Copy the rest of the application
COPY . .

# Create volumes for input and output directories
VOLUME ["/app/input", "/app/output"]

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create a non-root user and set up permissions
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/input /app/output && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/input /app/output

USER appuser

# Set the entrypoint with error handling
ENTRYPOINT ["python", "-u", "ccs_extract.py"] 