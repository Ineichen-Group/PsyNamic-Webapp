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

load-dump: load-env
	docker compose exec db psql -U ${DATABASE_USER} -d ${DATABASE_NAME} -f /docker-entrypoint-initdb.d/db_dump.sql

db-reset:
	docker compose exec db psql -U ${DATABASE_USER} -d ${DATABASE_NAME} -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	$(MAKE) db-init
	docker compose exec web python data/models.py

load-indexes:
	docker exec -i db psql -U $(DATABASE_USER) -d $(DATABASE_NAME) < /docker-entrypoint-initdb.d/indexes.sql

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

db-init: load-env
	docker compose up -d db_init

# Drop all data and recreate an empty DB schema, then recreate tables
empty-db: load-env
	@echo "Dropping public schema and recreating empty database (backup recommended)"
	docker compose exec db psql -U ${DATABASE_USER} -d ${DATABASE_NAME} -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	$(MAKE) load-datamodel

web-shell:
	docker compose exec web /bin/bash

pipeline-shell:
	docker compose exec pipeline /bin/sh

run-pipeline:
	docker compose up -d pipeline

ps:
	docker compose ps

restart:
	docker compose restart $(service)

db-dump: load-env
	DATE=$$(date +%Y%m%d_%H%M%S); \
	docker compose exec db pg_dump -U ${DATABASE_USER} -d ${DATABASE_NAME} -F c -b -v -f /data/data_dump_$${DATE}.sql

clean-containers:
	# Stop all running containers (no error if none), then remove all containers
	-@docker ps -q | xargs -r docker stop
	-@docker ps -aq | xargs -r docker rm -f