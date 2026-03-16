FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing byte-compiled files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install project dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entirety of our application context
COPY . .

# Avoid running as root for security best practices
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# gthread workers allow APScheduler threads to make slow RSS HTTP calls
# without triggering the 30s sync-worker timeout.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--worker-class", "gthread", "--workers", "1", "--threads", "4", "--timeout", "120", "run:app"]
