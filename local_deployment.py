import os
import subprocess
import tempfile
from string import Template

# Define the YAML structure as a multi-line string
yaml_template = """
name: multi-service-deployment
runtime_env:
  working_dir: .
  pip:
    - python-dotenv
    - ray==2.46.0

applications:
  - name: KitsuneChatbot
    route_prefix: /kitsune-chatbot
    import_path: app.main:entrypoint
    runtime_env:
      env_vars:
        PYTHONPATH: "${PYTHONPATH}:."
        AZURE_OPENAI_API_KEY: "${AZURE_OPENAI_API_KEY}"
        AZURE_OPENAI_API_ENDPOINT: "${AZURE_OPENAI_API_ENDPOINT}"
        AZURE_OPENAI_LLM_DEPLOYMENT_NAME: "${AZURE_OPENAI_LLM_DEPLOYMENT_NAME}"
        AZURE_OPENAI_API_VERSION: "${AZURE_OPENAI_API_VERSION}"
        AZURE_OPENAI_LLM_MODEL: "${AZURE_OPENAI_LLM_MODEL}"
        AZURE_OPENAI_EMBEDDING_MODEL: "${AZURE_OPENAI_EMBEDDING_MODEL}"
        AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: "${AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME}"
        REDIS_ENABLE_FLAG: "${REDIS_ENABLE_FLAG}"
        REDIS_HOST: "${REDIS_HOST}"
        REDIS_PORT: "${REDIS_PORT}"
        REDIS_PASSWORD: "${REDIS_PASSWORD}"
        REDIS_DB: "${REDIS_DB}"
        POSTGRES_HOST: "${POSTGRES_HOST}"
        POSTGRES_PORT: "${POSTGRES_PORT}"
        POSTGRES_DB: "${POSTGRES_DB}"
        POSTGRES_USER: "${POSTGRES_USER}"
        POSTGRES_PASSWORD: "${POSTGRES_PASSWORD}"
        POSTGRES_SCHEMA: "${POSTGRES_SCHEMA}"
        LANCEDB_PATH: "${LANCEDB_PATH}"
        LANCEDB_TABLE_NAME: "${LANCEDB_TABLE_NAME}"
        LANCEDB_EMBEDDING_MODEL: "${LANCEDB_EMBEDDING_MODEL}"
        ALLOWED_TOPICS: "${ALLOWED_TOPICS}"
    deployments:
      - name: ChatbotAPIIngress
        num_replicas: 1
        ray_actor_options:
          num_cpus: 0.15
          num_gpus: 0
      - name: ChatbotService
        num_replicas: 2
        ray_actor_options:
          num_cpus: 0.15
          num_gpus: 0
"""


def main():
    current_dir = os.path.dirname(os.path.realpath(__file__))

    # Create a temporary file for the YAML configuration
    if not os.path.exists(f"{current_dir}/tmp"):
        os.makedirs(f"{current_dir}/tmp")
    with tempfile.NamedTemporaryFile(
        delete=False, mode="w", suffix=".yaml", dir=f"{current_dir}/tmp"
    ) as temp_file:

        # Use Template to substitute environment variables in the YAML string
        template = Template(yaml_template)

        # Substitute placeholders with actual environment variable values
        filled_yaml = template.safe_substitute(os.environ)

        # Write the filled YAML content to the temporary file
        temp_file.write(filled_yaml)

        # Get the name of the temporary file for reference
        temp_file_name = temp_file.name

    print(f"Temporary YAML file created at {temp_file_name}")

    # Execute the temporary YAML file using a shell command
    try:
        command = f"serve deploy {temp_file_name} && serve status"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error executing command:\n{result.stderr}")
        else:
            print(result.stdout)

    finally:
        # Clean up by deleting the temporary file after execution
        os.remove(temp_file_name)
        print(f"Temporary file {temp_file_name} deleted.")


if __name__ == "__main__":
    main()
