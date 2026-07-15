#!/bin/sh
set -e

echo "Running model / schema initialization..."
python /app/data/models.py

echo "Populating database with manual seed data..."

# All manually defined as relevant
python -m data.populate \
  -s data/manual/as_review_studies_relevant_with_info_20240101_00-00-00.csv

# Train, test, dev splits from manual dataset
python -m data.populate \
  -p data/manual/class_predictions_manual_20250127_00-00-00.csv

python -m data.populate \
  -p data/manual/ner_bio_966_manual.jsonl

# Predictions on rest of manually defined as relevant but not annotated
python -m data.populate \
  -p data/manual/class_predictions_20240101_04-48-11.csv

python -m data.populate \
  -p data/manual/ner_predictions_20240101_00-00-27.csv

# Pubmed data automatically downloaded and predicted studies up until 2026-05-30, with new search string without study type restriction
# Automatically deduplicated 

python -m data.populate \
  -s data/manual/studies_relevant_deduplicated_excluded_20260530_00-00-00.csv

python -m data.populate \
  -p data/manual/ner_predictions_20260530_00-02-38.csv

python -m data.populate \
  -p data/manual/class_predictions_20260530_00-15-50.csv


echo "Database initialization completed successfully."
