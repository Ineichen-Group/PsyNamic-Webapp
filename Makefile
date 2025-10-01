include .env
export $(shell sed -n 's/^\([^#][^=]*\)=.*/\1/p' .env)

# Load environment variables from .env
load-env:
	export $(shell grep -v '^#' .env | xargs)

# Show DB user
show-db-user: load-env
	@echo ${DATABASE_USER}

populate: load-env
	docker compose exec db psql -U ${DATABASE_USER} -d ${DATABASE_NAME} -f /data/data_dump.sql

up:
	docker compose up -d

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
