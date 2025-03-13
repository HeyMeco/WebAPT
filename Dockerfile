FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt \
    && uv pip install --system --no-cache-dir gunicorn

# Copy application files
COPY app.py .
COPY lib ./lib
COPY static ./static
COPY templates ./templates

# Ensure lib is a proper Python package
RUN touch lib/__init__.py

# Set environment variables
ENV PYTHONPATH=/app:/app/lib \
    PORT=5000

# Expose the port
EXPOSE 5000

# Run the app with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]