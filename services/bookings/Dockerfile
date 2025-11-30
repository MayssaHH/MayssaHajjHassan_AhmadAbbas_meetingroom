# Dockerfile for the Bookings service.

FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies for the whole project.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the image.
COPY . .

<<<<<<< HEAD
# Set PYTHONPATH to include /app so imports work correctly
=======
>>>>>>> 0ea6d4cabd446806e51d5cbe4b57f6d5e82d25d4
ENV PYTHONPATH=/app

EXPOSE 8003

<<<<<<< HEAD
# Note: use full module path so /app is on sys.path and common/ is importable
=======
>>>>>>> 0ea6d4cabd446806e51d5cbe4b57f6d5e82d25d4
CMD ["uvicorn", "services.bookings.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
