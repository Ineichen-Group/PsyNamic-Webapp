#!/usr/bin/env bash

set -Eeuo pipefail

DATA_DIR="/home/sysadmin/PsyNamic-Webapp/data"
BACKUP_DIR="/mnt/research_storage/psynamic_data_backup"

echo "=================================================="
echo "$(date) Starting PsyNamic backup"

# Mount the Research Storage if necessary
if ! mountpoint -q /mnt/research_storage; then
    mount /mnt/research_storage
fi

if ! mountpoint -q /mnt/research_storage; then
    echo "ERROR: Could not mount Research Storage."
    exit 1
fi

for folder in \
    pubmed_fetch_results \
    predictions \
    relevant_studies
do
    echo ""
    echo "Backing up $folder..."

    rsync \
        -avh \
        --stats \
        "$DATA_DIR/$folder/" \
        "$BACKUP_DIR/$folder/"
done

echo ""
echo "$(date) Backup completed successfully."
echo "=================================================="
