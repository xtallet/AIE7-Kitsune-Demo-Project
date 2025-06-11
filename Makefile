
gcloud-auth:
	gcloud auth application-default login

up:
	docker compose up -d

down:
	docker compose down

ray-up:
	ray start --head

ray-serve-deploy:
	python local_deployment.py

ray-serve-status:
	serve status

ray-serve-down:
	serve shutdown -y

ray-down:
	ray stop

# Other Commands
redis-shell:
	redis-cli -h 0.0.0.0 -p 6380 -a mysecretpassword

redis-clear:
	docker exec -i redis redis-cli -p 6380 -a mysecretpassword FLUSHALL

postgres-shell:
	psql -h localhost -p 5432 -U data_app -W -d datadb

export-dependencies:
	uv export --format requirements-txt --no-dev --locked --output-file requirements.txt
	uv export --format requirements.txt --locked --output-file requirements-dev.txt
