include .env
export $(shell sed -n 's/^\([^#][^=]*\)=.*/\1/p' .env)

# Load environment variables from .env
load-env:
	export $(shell grep -v '^#' .env | xargs)

# Show DB user
show-db-user: load-env
	@echo ${DATABASE_USER}

load-datamodel: load-env
	docker compose exec web python data/models.py

load-indexes:
	docker exec -i db psql -U $(DATABASE_USER) -d $(DATABASE_NAME) < /docker-entrypoint-initdb.d/indexes.sql

db-init: load-env
	docker compose up db_init

db-dump: load-env
	DATE=$$(date +%Y%m%d_%H%M%S); \
	docker compose exec db pg_dump -U ${DATABASE_USER} -d ${DATABASE_NAME} -F c -b -v -f /data/data_dump_$${DATE}.sql

# Drop all data and recreate an empty DB schema, then recreate tables
db-empty: load-env
	@echo "Dropping public schema and recreating empty database (backup recommended)"
	docker compose exec db psql -U ${DATABASE_USER} -d ${DATABASE_NAME} -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	$(MAKE) load-datamodel

db-populate: load-env
	docker compose exec web python -m data.populate

up:
	docker compose up -d db web

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

db-shell: load-env
	docker compose exec db psql -U ${DATABASE_USER} -d ${DATABASE_NAME}

web-shell:
	docker compose exec web /bin/bash

pipeline-shell:
	docker compose exec pipeline /bin/sh

run-pipeline:
	docker compose up -d pipeline

ps:
	docker compose ps

restart:
	docker compose down
	docker compose up -d db web

clean-containers:
	# Stop all running containers (no error if none), then remove all containers
	-@docker ps -q | xargs -r docker stop
	-@docker ps -aq | xargs -r docker rm -f

cronjobs:
	sudo crontab -l


cronlog:
	@echo "===== ROOT CRONTAB (last 10 cron entries) ====="
	@grep CRON /var/log/syslog | tail -n 10
	@echo ""
	@echo "===== GENERAL PIPELINE LOG (last 10 lines) ====="
	@tail -n 10 /home/sysadmin/PsyNamic-Webapp/pipeline.log 2>/dev/null || echo "No general pipeline log found"
	@echo ""
	@echo "===== LATEST PIPELINE LOG (last 10 lines) ====="
	@latest_log=$$(ls -1t /home/sysadmin/PsyNamic-Webapp/pipeline/log/pipeline_*.log 2>/dev/null | head -n 1); \
	if [ -n "$$latest_log" ]; then \
		echo "Tailing latest log: $$latest_log"; \
		tail -n 10 "$$latest_log"; \
	else \
		echo "No pipeline logs found"; \
	fi
