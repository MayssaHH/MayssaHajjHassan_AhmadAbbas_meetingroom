# Dockerfile for the Reviews service.

FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies for the whole project.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the image.
COPY . .

WORKDIR /app/services/reviews

EXPOSE 8004

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
