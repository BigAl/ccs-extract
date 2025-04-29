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

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Set the entrypoint
ENTRYPOINT ["python", "ccs_extract.py"] 