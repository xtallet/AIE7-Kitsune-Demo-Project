import os

import lancedb
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

client = AzureChatOpenAI(
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_endpoint=os.environ["AZURE_OPENAI_API_ENDPOINT"],
    azure_deployment=os.environ["AZURE_OPENAI_LLM_DEPLOYMENT_NAME"],
)


def embed_text(text: str, model: str = "text-embedding-ada-002") -> list[float]:
    """Generates an embedding for the provided text using the specified OpenAI model.

    :param text: Text to be processed.
    :param model: Embedding model to be used.
    :return: List of float values representing the embedding.
    """
    model = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"]
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


env_vars = load_dotenv()

print(f'LANCEDB_PATH: {os.getenv("LANCEDB_PATH")}')
db = lancedb.connect(os.getenv("LANCEDB_PATH"))
print("Tables available:", db.table_names())
print("Tables after creation:", db.table_names())
table = db.open_table("synthetic_data")
print(table)
print(f"table schema : {table.schema}")

# Get a vector from the table
sample_vector = table.to_pandas().iloc[0]["vector"]
print(f"Vector dimension in table: {len(sample_vector)}")

# Get the query vector
query_embedding = embed_text("How many policies are there ?")
print(f"Dimension of the query vector: {len(query_embedding)}")


df = table.to_pandas()
print(f"Number of records in the table: {len(df)}")
print(f"First records:\n{df.head()}")

print(table.schema.field("vector").type)

# Check if the index exists
print(table.list_indices())

# Create an index on the 'vector' column using the cosine similarity metric
# table.create_index(metric="cosine", vector_column_name="vector") # TODO review per default L2
# print(table.list_indices())
