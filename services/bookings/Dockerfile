# Dockerfile for the Bookings service.

FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies for the whole project.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the image.
COPY . .

ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["uvicorn", "services.bookings.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
