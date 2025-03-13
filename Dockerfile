FROM python:3.13-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn  # Explicitly ensure gunicorn is installed

# Copy application files
COPY app.py .
COPY lib ./lib
COPY static ./static
COPY templates ./templates

# Ensure lib is a proper Python package
RUN touch lib/__init__.py

# Set environment variables
ENV PYTHONPATH=/app:/app/lib
ENV PORT=5000

# Expose the port
EXPOSE 5000

# Run the app with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]