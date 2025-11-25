# Dockerfile for the Rooms service.

FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies for the whole project.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the image.
COPY . .

WORKDIR /app/services/rooms

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
