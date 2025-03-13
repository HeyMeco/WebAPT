FROM python:3.9-slim as builder

WORKDIR /app
RUN pip install uv
COPY requirements.txt .
RUN uv pip compile requirements.txt -o requirements.lock
RUN uv pip install --no-cache -r requirements.txt --system

FROM python:3.9-slim

WORKDIR /app
COPY --from=builder /usr/local /usr/local
# Copy everything at once
COPY . .

ENV PORT=5000
ENV PYTHONPATH=/app

EXPOSE 5000

CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "app:app"] 