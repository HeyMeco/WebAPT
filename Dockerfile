FROM python:3.9-slim as builder

WORKDIR /app
RUN pip install uv
COPY requirements.txt .
RUN uv pip compile requirements.txt -o requirements.lock
RUN uv pip install --no-cache -r requirements.txt --system

FROM python:3.9-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY . .

ENV PORT=5000

EXPOSE 5000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT app:app"] 