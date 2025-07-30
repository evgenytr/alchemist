#!/bin/bash

echo "Starting application..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h db -p 5432 -U postgres; do
  echo "PostgreSQL is not ready yet, waiting..."
  sleep 2
done
echo "PostgreSQL is ready!"

# Run database setup
echo "Setting up database..."
python setup-postgres.py

# Start the FastAPI application
echo "Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 8092