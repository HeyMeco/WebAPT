FROM python:3.9-slim as builder

WORKDIR /app
RUN pip install uv
COPY requirements.txt .
RUN uv pip compile requirements.txt -o requirements.lock
RUN uv pip install --no-cache -r requirements.txt --system

FROM python:3.9-slim

WORKDIR /app
COPY --from=builder /usr/local /usr/local

# Copy everything separately to ensure lib directory is copied correctly
COPY app.py .
COPY lib ./lib
COPY static ./static
COPY templates ./templates

# Create empty __init__.py if it doesn't exist
RUN if [ ! -f lib/__init__.py ]; then touch lib/__init__.py; fi

# Set Python path explicitly to include current directory
ENV PYTHONPATH=.
ENV PORT=5000

EXPOSE 5000

# Run with explicit module path
CMD ["sh", "-c", "cd /app && PYTHONPATH=/app python -m gunicorn --bind 0.0.0.0:$PORT app:app"] 