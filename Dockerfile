# Stage 1: Build dependencies
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
WORKDIR /app

# Copy only requirements to leverage caching
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt gunicorn

# Stage 2: Runtime image
FROM python:3.13-alpine
WORKDIR /app

# Copy only the Python runtime and installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Copy application files
COPY app.py .
COPY lib ./lib
COPY static ./static
COPY templates ./templates

# Ensure lib is a Python package
RUN touch lib/__init__.py

# Set environment variables
ENV PYTHONPATH=/app:/app/lib \
    PORT=5000

# Optional environment variables:
# APTREPO: Set a default repository URL (e.g., APTREPO=https://apt.armbian.com)

# Expose the port
EXPOSE 5000

# Run the app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]