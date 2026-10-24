# Use an official, lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the rest of the application code
COPY . .

# Ensure the upload directory exists
RUN mkdir -p static/uploads

# Set the default port for local testing, Cloud Run will override this automatically
ENV PORT=8080

# Command to run the application using Gunicorn (Note: no brackets here so it can read the $PORT variable)
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 2 main:app