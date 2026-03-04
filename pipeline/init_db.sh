#!/bin/sh
set -e

echo "Running model / schema initialization..."
python /app/data/models.py

echo "Populating database with manual seed data..."

# All manually defined as relevant
python -m data.populate \
  -s data/manual/studies_relevant_with_info_20240101_00-00-00.csv

# Train, test, dev splits from manual dataset
python -m data.populate \
  -p data/manual/predictions_manual_20250127_00-00-00.csv

python -m data.populate \
  -p data/manual/ner_bio_966.jsonl

# Predictions on rest of manually defined as relevant
python -m data.populate \
  -p data/manual/class_predictions_20240101_04-48-11.csv

python -m data.populate \
  -p data/manual/ner_predictions_20240101_00-13-08.csv

# Pubmed data automatically downlaoded and predicted on 2026-02-18
python -m data.populate \
  -s data/relevant_studies/studies_20260218_00-15-00.csv

python -m data.populate \
  -p data/predictions/class_predictions_20260218_45-25-00.csv

python -m data.populate \
  -p data/predictions/ner_predictions_20260218_00-04-32.csv

echo "Database initialization completed successfully."
