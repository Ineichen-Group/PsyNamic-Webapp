include .env
export $(shell sed -n 's/^\([^#][^=]*\)=.*/\1/p' .env)

# Load environment variables from .env
load-env:
	export $(shell grep -v '^#' .env | xargs)

# Show DB user
show-db-user: load-env
	@echo ${DATABASE_USER}

load-dump: load-env
	docker cp data/data_dump.sql db:/data/data_dump.sql
	docker compose exec db psql -U ${DATABASE_USER} -d ${DATABASE_NAME} -f /data/data_dump.sql

load-indexes:
	docker cp data/indexes.sql db:/data/indexes.sql
	docker exec -i db psql -U $(DATABASE_USER) -d $(DATABASE_NAME) < data/indexes.sql

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
	docker compose run --rm pipeline /bin/bash

run-pipeline:
	docker compose run --rm pipeline

ps:
	docker compose ps

restart:
	docker compose restart $(service)

db-dump: load-env
	DATE=$$(date +%Y%m%d_%H%M%S); \
	docker compose exec db pg_dump -U ${DATABASE_USER} -d ${DATABASE_NAME} -F c -b -v -f /data/data_dump_$${DATE}.sql