# Use the official Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .
# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

ENV PYTHONPATH=.


# Add and configure a non-root user
RUN addgroup --system appuser && adduser --system --ingroup appuser -u 999 appuser
RUN chown -R appuser:appuser /app

# Set permissions and make start script executable
COPY /scripts/start-api.sh /start.sh
RUN chmod a+x /start.sh

# Switch to the non-root user
USER 999

# Expose the FastAPI port
EXPOSE 8080

# Entrypoint for container
ENTRYPOINT ["/start.sh"]