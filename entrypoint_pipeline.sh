#!/bin/sh
set -e  # stop on first error

echo "Fetching new PubMed data..."
python /app/data/get_pubmed_data.py

echo "Running relevance prediction..."
python /app/model/predict.py

echo "Populating database..."
python /app/data/populate.py
