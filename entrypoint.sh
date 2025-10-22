#!/bin/bash
# Wait for Postgres to be ready
until psql $DATABASE_URL -c '\l'; do
  echo "Waiting for Postgres..."
  sleep 2
done

# Create tables
# python data/models.py

# Start Dash app
python app.py