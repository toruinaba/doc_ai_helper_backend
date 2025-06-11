FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements for installation
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

# Expose the port the app will run on
EXPOSE 8000

# Development environment - default to bash for interactive development
CMD ["/bin/bash"]
