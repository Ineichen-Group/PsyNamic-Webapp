#!/bin/sh
set -e  # stop on first error

# Create a unified log file (timezone Europe/Zurich to match predict.py naming)
LOGDIR="pipeline/log"
mkdir -p "$LOGDIR"
TS=$(TZ=Europe/Zurich date +"%Y%m%d_%H%M%S")
LOGFILE="$LOGDIR/pipeline_${TS}.log"

echo "Fetching new PubMed data..."
python -m data.get_pubmed_data -l "$LOGFILE"

echo "Running relevance prediction..."
python -m pipeline.predict -l "$LOGFILE"

echo "Populating database..."
python -m data.populate -l "$LOGFILE"
