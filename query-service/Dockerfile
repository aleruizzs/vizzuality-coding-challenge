FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${UVICORN_PORT} --reload"]