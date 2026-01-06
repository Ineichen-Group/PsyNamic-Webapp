  GNU nano 7.2                                                                             /usr/local/bin/monitor_webapp.sh
#!/bin/bash

EMAIL="vera.bernhard@unibe.ch"
LOGFILE="/var/log/webapp_monitor.log"

if [ -f "/home/sysadmin/PsyNamic-Webapp/.env" ]; then
    export $(grep -v '^#' /home/sysadmin/PsyNamic-Webapp/.env | xargs)
fi

# --------- Check Dash app ---------
WEB_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8050/)
ALERT=""

if [[ "$WEB_STATUS" != "200" ]]; then
    ALERT+="Dash app is down! HTTP status: $WEB_STATUS\n"
fi

# --------- Check containers ---------
for CONTAINER in webapp_web webapp_db; do
    RUNNING=$(docker ps --filter "name=$CONTAINER" --format '{{.Names}}')
    if [[ -z "$RUNNING" ]]; then
        ALERT+="$CONTAINER container is not running!\n"
    fi
done

# --------- Optional: DB connectivity check ---------
DB_OK=$(docker exec -i webapp_db bash -c "PGPASSWORD='$DATABASE_PASSWORD' psql -U $DATABASE_USER -d $DATABASE_NAME -t -q -c 'SELECT 1;'" | tr -d '[:space:]')
if [[ "$DB_OK" != "1" ]]; then
    ALERT+="Cannot connect to DB!\n"
fi

# --------- Log status ---------
echo "$(date): HTTP=$WEB_STATUS, Containers=$(docker ps --filter "name=webapp_" --format '{{.Names}}')" >> $LOGFILE

# --------- Send email if alert ---------
if [[ ! -z "$ALERT" ]]; then
    echo -e "$ALERT" | mail -s "Webapp Alert!" $EMAIL
fi