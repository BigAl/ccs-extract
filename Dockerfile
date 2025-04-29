# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy setup files first to leverage Docker cache
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
    cp transaction_config.template.json transaction_config.json && \
    chown -R appuser:appuser /app && \
    # Set directory permissions to 755 (owner: rwx, group: rx, others: rx)
    chmod 755 /app/input /app/output && \
    # Set file permissions to 644 (owner: rw, group: r, others: r)
    chmod 644 /app/transaction_config.json && \
    # Ensure appuser can write to output directory
    chmod g+w /app/output

# Switch to non-root user
USER appuser

# Set the entrypoint
ENTRYPOINT ["python", "ccs_extract.py"] 