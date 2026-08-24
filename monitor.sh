#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="$SCRIPT_DIR/log/monitor.log"
ENV_FILE="$SCRIPT_DIR/.env"

# --------- Load environment ---------
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "$(date): ERROR: .env file not found at $ENV_FILE" >> "$LOGFILE"
fi

EMAIL="$LOG_EMAIL"
ALERT=""

# --------- Check Dash app ---------
WEB_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8050/)

if [[ "$WEB_STATUS" != "200" ]]; then
    ALERT+="Dash app is down! HTTP status: $WEB_STATUS\n"
fi

# --------- Check containers ---------
for CONTAINER in webapp_web webapp_db; do
    RUNNING=$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null)

    if [[ "$RUNNING" != "true" ]]; then
        ALERT+="$CONTAINER container is not running!\n"
    fi
done

# --------- DB connectivity check ---------
# Only attempt docker exec if the DB container is actually running.
DB_RUNNING=$(docker inspect -f '{{.State.Running}}' webapp_db 2>/dev/null)

if [[ "$DB_RUNNING" == "true" ]]; then
    DB_OK=$(docker exec webapp_db \
        bash -c "PGPASSWORD='$DATABASE_PASSWORD' psql -U '$DATABASE_USER' -d '$DATABASE_NAME' -t -q -c 'SELECT 1;'" \
        2>/dev/null | tr -d '[:space:]')

    if [[ "$DB_OK" != "1" ]]; then
        ALERT+="Cannot connect to DB!\n"
    fi
fi

# --------- Log status ---------
CONTAINERS=$(docker ps --filter "name=webapp_" --format '{{.Names}}')

echo "$(date): HTTP=$WEB_STATUS, Containers=$CONTAINERS" >> "$LOGFILE"

# --------- Send email if alert ---------
if [[ -n "$ALERT" ]]; then
    echo "$(date): ALERT detected: $ALERT" >> "$LOGFILE"
    echo "$(date): EMAIL=$EMAIL" >> "$LOGFILE"

    if [[ -z "$EMAIL" ]]; then
        echo "$(date): ERROR: LOG_EMAIL is empty. Cannot send alert email." >> "$LOGFILE"
    else
        echo -e "$ALERT" | mail -s "Webapp Alert!" "$EMAIL" >> "$LOGFILE" 2>&1

        MAIL_EXIT=$?

        if [[ $MAIL_EXIT -ne 0 ]]; then
            echo "$(date): ERROR: mail command failed with exit code $MAIL_EXIT" >> "$LOGFILE"
        else
            echo "$(date): Alert email sent." >> "$LOGFILE"
        fi
    fi
fi
