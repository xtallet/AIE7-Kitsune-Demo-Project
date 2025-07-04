from agno.storage.mongodb import MongoDbStorage
from config.settings import MongoDBConfig


def get_storage_db(user_id: str) -> MongoDbStorage:
    config = MongoDBConfig()
    return MongoDbStorage(
        db_url=config.connection_string,
        db_name="chat_storage_db",
        collection_name=user_id,
    )
