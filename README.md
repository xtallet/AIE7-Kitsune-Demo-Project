# Kitsune Chatbot

This project is a chatbot that can answer questions about Kitsune platform.

It uses multiple services to enhance and improve the chatbot's capabilities, such as:
- Cache service using Redis. Retrieves cached answers if available, otherwise it will query the database.
- Vector database using LanceDB. It stores the vectorized questions and answers, and retrieves similar vectors to answer user questions.
- LLM service using Azure OpenAI. It generates the SQL questions and once they are executed in the Kitsune DB, it summarizes the SQL answers to provide a natural language response to the user.
- Guardrails service using Guardrails-ai. It restricts the chatbot to answer only questions related to Kitsune platform and its policies.
- Kitsune DB service. It holds all the SQL operations and interactions with the Kitsune platform database.

The chatbot it deployed and scaled with Ray framework. Some notes:
- It is deployed with Ray Serve, that serves a FastAPI app that handles the user requests. Endpoint name is `/chat`.
- Dual deploy: one for the Ingress (FastAPI) and one for the workers (where the chatbot is running). This way we can scale the workers independently of the Ingress.

The chatbot can run locally:
- Raw console application (without any FastAPI served or Ray deployment) by executing the `main_console.py` file. Interesting for debugging and testing purposes.
- With Ray Serve in the local environment, by having a Ray cluster running and deploying the `local_deployment.py` yaml file into it.

## Local Deployment with Ray Serve (No k8s)

### Steps
0. Have `Python 3.11` installed, `uv` and Docker too.
1. Create the virtual environment and install the dependencies: `uv sync`.
2. Create the `.env` file with the required variables (use `.env.template` file as a template).
3. Install Guardrail Restrict To Topic Validator (it will generate a token): `guardrails hub install hub://tryolabs/restricttotopic`.
4. Configure the token to use Guardrail: `guardrails configure --token <YOUR_TOKEN>`. Verify the installation: `guardrails hub list`, output should be "Installed Validators: RestrictToTopic".
5. Start the Redis and PostgrSQL services using Docker Compose: `make up`.
6. Start the Ray cluster: `make ray-up`. You can stop the cluster anytime with `make ray-down`.
7. Export all the environment variables from the `.env` file: `set -a; source .env; set +a`. You can unset them anytime with: `source ./unset_env_vars.sh`
8. Authenticate with Google Cloud with: `make gcloud-auth`.
9. Deploy the Chatbot to Ray Serve: `make ray-serve-deploy`. You can verify the ray serve status with `make ray-serve-status`. You can delete the Ray Serve deployment anytime with: `make ray-serve-down`.
10. Go to http://localhost:8000/kitsune-chatbot/docs to see the FastAPI documentation and test the chatbot. You can also test it with `curl` or any HTTP client. Checkout the scripts/chatbot_endpoint_test.py file for an example of how to use the chatbot endpoint over aiohttp.

### Other useful commands
- To open a shell with redis and postgres, run: `make redis-shell` or `make postgres-shell`.
- To clear redis cache, run: `make redis-clear`.
- To check Ray Serve status: `make ray-serve-status`.
- To stop the Ray Serve deployment: `make ray-serve-down`.
- To stop the Ray cluster: `make ray-stop`.

## TODO TASKS YOU SHOULD REVIEW
- Review Elvin's analysis on the best settings to use. For example, on the embedding model, we are using the already deployed to our Inari's azure openai account `text-embedding-ada-002`, but from his tests, the embedding model `small embeddings text 3` has better performance and more accuracy.
- Cache service is implemented, but debate and think if it is really needed and what to store in it. For now we store all questions and its answers, but many computed answers should not be stored. Discussion example: What if a user asks for the number of Bound policies, then adds some more Bound policies to the platform and finally asks the same question? He'll get an outdated answer.
- Guardrails RestrictToTopic method `_azure_llm_callable` is synchronous, so it can't be called async. You'll need to revise it deeper to see if it can be implemented in an async way.
- Refactor Guardrails adapter. Take out of the adapter the LLM Prompts. Set as env variables the ability to use the Classifier or the LLM (or both) in the `RestrictToTopic` class. Add invalid topics to the `RestrictToTopic` class. Refine the allowed topics by adding more context and example to its definition in the llm prompt.
- Refactor current tests and add more tests for all adapters.
- Take out of the LLM adapter the Prompts (Same as Guardrails adapter).
- Refactor the main.py file. All adapters are initialized twice: one as the chatbot parameter and one as the Fastapi Lifespan event for testing (pinging) the adapters services and make sure they are all OK before finishing the ray serve deployment. May be instanciating them outside the Lifespan and outside the ray deployment class should work. But not sure if its best practices to do so.
- Revise class `ChatbotService` in main.py file. This class must be async and the methods too. The chatbot instance `agent` that is saved as a class attribute is initialized in a side method `_async_init`. Revise if there is a better option to do so.
- Wipe out all the spammy logger.info messages that are not really needed. I've left some of them to help the execution comprehension, but they are not really needed.
- Implement memory in the chatbot so it makes more fluent the conversation with the user and will be able to answer follow up questions.
- Implement a way to save the conversation history in the database, so it can be used later to improve the chatbot's performance.
- Implement reasoning before any chatbot decision. For example, right after the user asks a question, use the LLM to reason what action should be done. In most cases will be to generate the SQL query and execute it. But what if the user asks `How many policies are in the platform?` And then he asks `And how many are Drafts?`. The chatbot should be able to reason that the first question is about the number of policies in the platform and the second question is about the number of Draft policies, so it should proceed accordingly. To implement this, you should first have the chatbot session memory implemented before so it can take the chatbot history as the context to send to the LLM with the new user question.
- Make some performance tests to find the sweet spot for the number of Ray workers, how much CPU do they need and how many concurrent requests (a.k.a questions) can handle each worker.
- Get feedback from the user and store it somewhere. Use it to improve the chatbot's performance and take some metrics from it.
- Implement real time answering once the summarized answer outputs the first words.
- Deploy the chatbot to a k8s cluster. You'll need to do it with KubeRay k8s Operator, take Submission Intake as an example. It should work the exact same way: a k8s yaml definition with the kuberay Operator, have the redis running in the k8s cluster, inject all env vars and make sure the GCS is reachable too.



##########################
##########################
##### Redis Shell Commands
```bash
    SET {key} value                                     # Add a new key value to cache
    SET {key} value EX {expiration_time_seconds}    # Add a new key value to cache and set an expiration time (in seconds)
    GET {key}                                       # Get the value for the specified key
    DEL {key}                                       # Delete the key

    KEYS *              # return all keys that match the pattern. This commands blocks the redis server. Use SCAN instead.
    EXISTS {key}        # returns 1 or 0
    TTL {key}           # returns remaining TTL seconds of that key
    FLUSHDB             # Deletes all keys from the connection's current database.
```
