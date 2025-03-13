FROM python:3.9-slim

WORKDIR /app

# Install dependencies using standard pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY lib ./lib
COPY static ./static
COPY templates ./templates

# Create empty __init__.py if it doesn't exist
RUN if [ ! -f lib/__init__.py ]; then touch lib/__init__.py; fi

# Set Python path explicitly to include current directory
ENV PYTHONPATH=/app
ENV PORT=5000

EXPOSE 5000

# Run with explicit module path 
CMD ["sh", "-c", "python -m gunicorn --bind 0.0.0.0:$PORT app:app"] 