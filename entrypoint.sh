#!/bin/bash
# Wait for Postgres to be ready
until psql $DATABASE_URL -c '\l'; do
  echo "Waiting for Postgres..."
  sleep 2
done

# Create tables
# python data/models.py

# Start Dash app
exec gunicorn app:server --bind 0.0.0.0:8050 --workers 2 --threads 4