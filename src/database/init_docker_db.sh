#!/bin/bash

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h localhost -p 5432 -U retail_user
do
  sleep 2
done

# Create database schema
echo "Creating database schema..."
PGPASSWORD=retail_password psql -h localhost -U retail_user -d retail_analytics -f schema.sql

echo "Database initialization completed!" 