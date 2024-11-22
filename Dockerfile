# Use official Python image as base
FROM python:3.10-slim

# Set working directory in the container
WORKDIR /app

# Copy the FastAPI app files to the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the FastAPI port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]