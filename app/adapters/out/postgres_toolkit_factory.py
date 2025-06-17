from agno.tools.postgres import PostgresTools

from app.config.settings import KitsuneDBConfig


class PostgresToolkitFactory:
    def __init__(self) -> None:
        self.kitsune_db_config = KitsuneDBConfig()

    def get_db_tools(self) -> PostgresTools:
        return PostgresTools(
            host=self.kitsune_db_config.POSTGRES_HOST,
            port=self.kitsune_db_config.POSTGRES_PORT,
            user=self.kitsune_db_config.POSTGRES_USER,
            password=self.kitsune_db_config.POSTGRES_PASSWORD,
            db_name=self.kitsune_db_config.POSTGRES_DB,
            table_schema=self.kitsune_db_config.POSTGRES_SCHEMA,
        )
