# Kitsune Chatbot

This project is a chatbot that can answer questions about Kitsune platform.

The chatbot uses multiple services to enhance its capabilities:
- **FastAPI Service**: REST API endpoint for chat interactions
- **Cache Service**: Redis-based caching for improved performance
- **Vector Database**: LanceDB for vectorized questions and answers retrieval
- **LLM Service**: Azure OpenAI integration for generating SQL questions and natural language responses
- **Guardrails**: Topic validation to ensure the chatbot stays on-topic
- **Kitsune DB**: Database interactions with the Kitsune platform
- **MongoDB**: Storage for chat sessions and conversation history

## Local Development

### Environment setup
Have `Python 3.12`, `uv` and `Docker` installed.

Create the virtual environment and install the dependencies.
```
uv sync --prerelease=allow
```

Create the `.env` file with the required variables (use `.env.template` file as a template).

Authenticate with Google Cloud.

```
make gcloud-auth
```

Update the `docker-compose.yml` gcloud auth credentials path on the chatbot_service.

### Running with Docker Compose

Run the services:
```
make up
```

This will start Redis, PostgreSQL, MongoDB, MongoDB Express, and the chatbot service.

### Running FastAPI Directly in PyCharm

Create a PyCharm run configuration:


* Go to **Run → Edit Configurations**
* Click the + button and select **Python**
* Configure:
  * **Name**: FastAPI Server
  * **Script path**: `.venv/bin/uvicorn`
  * **Parameters**: `app.main:app --reload --host 0.0.0.0 --port 8000`
  * **Python interpreter**: Select from `.venv`
  * **Working directory**: Your project root

### Other useful commands
- To open a shell with redis and postgres, run: `make redis-shell` or `make postgres-shell`.
- To clear redis cache, run: `make redis-clear`.
- To check Ray Serve status: `make ray-serve-status`.
- To stop the Ray Serve deployment: `make ray-serve-down`.
- To stop the Ray cluster: `make ray-stop`.
