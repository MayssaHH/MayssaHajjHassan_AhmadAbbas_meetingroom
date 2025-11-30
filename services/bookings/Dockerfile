# Dockerfile for the Bookings service.

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["uvicorn", "services.bookings.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
