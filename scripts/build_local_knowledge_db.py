import json
import os
import sys

import lancedb
from dotenv import load_dotenv

# from utils.embeddings import embed_text
from lancedb.pydantic import LanceModel, Vector
from openai import AzureOpenAI

env_vars = load_dotenv()

os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["AZURE_OPENAI_API_ENDPOINT"] = os.getenv("AZURE_OPENAI_API_ENDPOINT")
os.environ["AZURE_OPENAI_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION")
os.environ["LANCEDB_PATH"] = os.getenv("LANCEDB_PATH")

# Add the project root directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Define the data model with LanceModel
class SyntheticData(LanceModel):
    question: str
    cot: str
    sql_query: str
    chunk_id: str
    vector: Vector(1536)  # Ensures a fixed length of 1536


# Load environment variables from the .env file
load_dotenv()

# Initialize the OpenAI client with the API key
client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_endpoint=os.environ["AZURE_OPENAI_API_ENDPOINT"],
)


def embed_text(text: str, model: str = "text-embedding-ada-002") -> list[float]:
    """Generates an embedding for the provided text using the specified OpenAI model.

    :param text: Text to be processed.
    :param model: Embedding model to be used.
    :return: List of float values representing the embedding.
    """
    model = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


def build_knowledge_base():
    # Path to the dataset

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # /app/scripts
    dataset_path = os.path.join(SCRIPT_DIR, "..", "data", "dataset.json")
    dataset_path = os.path.abspath(dataset_path)  # ruta absoluta

    # dataset_path = os.path.join("../", "data", "dataset.json")

    # Load the dataset
    with open(dataset_path, encoding="utf-8") as f:
        data = json.load(f)

    # Prepare records with embeddings
    records = []
    for entry in data:
        vector = embed_text(entry["sql_query"])
        records.append(
            {
                "question": entry["question"],
                "cot": entry["cot"],
                "sql_query": entry["sql_query"],
                "chunk_id": entry["chunk_id"],
                "vector": vector,
            }
        )

    # Connect to LanceDB and create the table
    db = lancedb.connect(os.environ["LANCEDB_PATH"])
    table_name = "synthetic_data"

    # Check if the table already exists
    if table_name in db.table_names():
        print(f"The table '{table_name}' already exists. It will be overwritten.")
        db.drop_table(table_name)

    # Create the table with the schema defined by Synthetic Data
    db.create_table(table_name, data=records, schema=SyntheticData, mode="overwrite")
    print(f"Table {table_name} created with {len(records)} records.")
    print(f"✅ Knowledge base successfully created in LanceDB: {table_name}")


if __name__ == "__main__":
    build_knowledge_base()
