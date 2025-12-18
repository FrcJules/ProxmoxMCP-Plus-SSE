# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y     git     curl     && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install mcpo uv

# Copy project files
COPY . .

# Create virtual environment and install dependencies
RUN uv venv &&     . .venv/bin/activate &&     uv pip install -e ".[dev]"

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8811

# Use entrypoint script
CMD ["/app/entrypoint.sh"]
