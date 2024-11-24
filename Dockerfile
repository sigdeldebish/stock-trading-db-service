# Base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install watchdog for live reload
RUN pip install watchdog

# Copy project files
COPY . /app/

# Command to run Uvicorn with live reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# Command to run watchdog monitoring for file changes for local testing of the DB APP.
# CMD ["watchmedo", "auto-restart", "--directory=/app", "--pattern=*.py", "--recursive", "--", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
