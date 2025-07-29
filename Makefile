home_dir = $(shell echo ~)
harbor_url = harbor.tech.inari.io
harbor_helm_path = oci://$(harbor_url)/helm
cbot_server_image_name = $(harbor_url)/kitsune/cbot-server
cbot_server_version := $(shell grep -m1 '^version *= *' pyproject.toml | sed 's/version *= *"\(.*\)"/\1/')

echo-version:
	@echo $(cbot_server_version)

# GCloud auth
gcloud-auth:
	gcloud auth application-default login

# Local usage
up:
	docker compose up -d --build --detach --remove-orphans

down:
	docker compose --profile "*" down --remove-orphans -t 5

# Redis Commands
redis-shell:
	redis-cli -h 0.0.0.0 -p 6380 -a mysecretpassword

redis-clear:
	docker exec -i redis redis-cli -p 6380 -a mysecretpassword FLUSHALL

# Postgres Commands
postgres-shell:
	psql -h localhost -p 5432 -U data_app -W -d datadb

psql-restore:
	kubectl port-forward svc/postgres-postgresql 5432 --namespace cbot & \
	sleep 5 && \
	psql postgresql://data_app:securepassword@localhost:5432/datadb < ./postgres/01_demokitsune_demo_30062025.sql
	psql postgresql://data_app:securepassword@localhost:5432/datadb < ./postgres/02_function_total_gross_premium.sql
	psql postgresql://data_app:securepassword@localhost:5432/datadb < ./postgres/03_function_get_last_endorsements_id.sql
	psql postgresql://data_app:securepassword@localhost:5432/datadb < ./postgres/04_function_get_premiums.sql

# Requirements and Dependencies
export-dependencies:
	uv export --format requirements-txt --no-dev --locked --output-file requirements.txt --prerelease=allow
	uv export --format requirements.txt --locked --output-file requirements-dev.txt --prerelease=allow
