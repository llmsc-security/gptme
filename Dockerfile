# Use Python 3.12 slim as base image
FROM python:3.12-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pyproject.toml and poetry.lock for dependency installation
COPY pyproject.toml poetry.lock ./

# Copy README.md (explicitly, to avoid .dockerignore issues)
COPY README.md ./

# Copy the gptme package
COPY gptme/ ./gptme/

# Install Poetry
RUN python -m venv /opt/poetry && \
    /opt/poetry/bin/pip install poetry && \
    /opt/poetry/bin/poetry self add poetry-plugin-export

# Export requirements with server extras
RUN /opt/poetry/bin/poetry export --without-hashes --without dev -E server -f requirements.txt -o requirements-server.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements-server.txt

# Install the gptme package
RUN pip install --no-cache-dir -e .

# Create non-root user (uid 1000) and workspace
RUN useradd -m -u 1000 appuser && \
    mkdir /workspace && \
    chown -R appuser:appuser /workspace

# Switch to non-root user
USER appuser

# Set environment variables
ENV HOME=/home/appuser
ENV PATH=/home/appuser/.local/bin:$PATH

# Set working directory
WORKDIR /workspace

# Expose the server port (11130)
EXPOSE 11130

# Default host and port
ENV GPTME_SERVER_HOST=0.0.0.0
ENV GPTME_SERVER_PORT=11130

# Run the server
CMD ["gptme-server", "serve", "--host", "0.0.0.0", "--port", "11130"]
