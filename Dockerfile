FROM python:3.11-slim

# Install netcat for database connection check
RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8092

# Create startup script
COPY start.sh .
RUN chmod +x start.sh

# Run the startup script
CMD ["./start.sh"]