home_dir = $(shell echo ~)
harbor_url = harbor.tech.inari.io
harbor_helm_path = oci://$(harbor_url)/helm
cbot_server_image_name = $(harbor_url)/kitsune/cbot-server
cbot_server_version := $(shell grep -m1 '^version *= *' pyproject.toml | sed 's/version *= *"\(.*\)"/\1/')

echo-version:
	@echo $(cbot_server_version)

cbot-build:
	docker buildx build \
		--build-arg GUARDRAILS_HUB_TOKEN=$(GUARDRAILS_HUB_TOKEN) \
		-t $(cbot_server_image_name):local \
		.

minikube-start:
	#minikube start --cpus=3 --memory=8192
	minikube start
# GCloud auth
gcloud-auth:
	gcloud auth application-default login

# Minikube enable gcloud auth addon
minikube-enable-gcp-auth:
	minikube addons enable gcp-auth --refresh --force

kuberay-up:
	helm repo add kuberay https://ray-project.github.io/kuberay-helm/ --force-update
	helm repo update
	helm upgrade -i kuberay-operator kuberay/kuberay-operator --version 1.2.2 --namespace cbot --create-namespace

kuberay-down:
	helm uninstall kuberay-operator --namespace cbot

# K8s deploy the submission intake server to the cluster
deploy:
	kubectl apply -f kuberay/local-secrets.yaml --namespace cbot
	helm upgrade -i redis --set auth.password="S5Wn9VaEWH" oci://registry-1.docker.io/bitnamicharts/redis --set replica.replicaCount=0 --namespace cbot --create-namespace
	helm upgrade -i postgres oci://registry-1.docker.io/bitnamicharts/postgresql \
	 --set auth.postgresPassword="securepassword" \
	 --set auth.database="datadb" \
	 --set auth.username="data_app" \
	 --set auth.password="securepassword" \
	  --namespace cbot --create-namespace
	kubectl apply -f kuberay/local-chatbot.yaml --namespace cbot

down:
	helm uninstall redis --namespace cbot
	helm uninstall postgres --namespace cbot
	kubectl delete -f kuberay/local-chatbot.yaml --namespace cbot
	kubectl delete -f kuberay/local-secrets.yaml --namespace cbot

# K8s port-forward the ray cluster and fast-api to localhost
port-forward-ray-cluster-fast-api:
	@SERVICE_NAME=$$(kubectl get svc -n cbot --no-headers -o custom-columns=":metadata.name" | grep chatbot-raycluster); \
	if [ -z "$$SERVICE_NAME" ]; then \
		echo "No matching service found!"; \
		exit 1; \
	fi; \
	echo "Found service: $$SERVICE_NAME"; \
	kubectl port-forward svc/$$SERVICE_NAME 8265 --namespace cbot & \
	kubectl port-forward svc/$$SERVICE_NAME 8000 --namespace cbot

minikube-save:
	docker save $(cbot_server_image_name):local | (eval $$(minikube docker-env) && docker load)

up:
	docker compose up -d

local-down:
	docker compose down

ray-up:
	ray start --head

ray-serve-deploy:
	python app/local_deployment.py

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

psql-restore:
	kubectl port-forward svc/postgres-postgresql 5432 --namespace cbot & \
	sleep 5 && \
	psql postgresql://data_app:securepassword@localhost:5432/datadb < ./postgres/01_redraytest_dump.sql
	psql postgresql://data_app:securepassword@localhost:5432/datadb < ./postgres/02_function_total_gross_premium.sql
	psql postgresql://data_app:securepassword@localhost:5432/datadb < ./postgres/03_function_get_last_endorsements_id.sql
	psql postgresql://data_app:securepassword@localhost:5432/datadb < ./postgres/04_function_get_premiums.sql

export-dependencies:
	uv export --format requirements-txt --no-dev --locked --output-file requirements.txt --prerelease=allow
	uv export --format requirements.txt --locked --output-file requirements-dev.txt --prerelease=allow
