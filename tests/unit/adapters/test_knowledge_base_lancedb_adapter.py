from unittest import mock
from unittest.mock import ANY, AsyncMock, MagicMock

import faker
import pandas as pd
import pytest

from app.adapters.out.knowledge_lancedb_adapter import KnowledgeLanceDBAdapter


class TestKnowledgeLanceDBAdapter:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.faker = faker.Faker()

    @pytest.mark.asyncio
    @mock.patch("logging.info")
    async def test_knowledge_lancedb_adapter_create(self, mock_logging):
        db_mock = AsyncMock()
        table_name = self.faker.word()
        embedding_model_name = self.faker.word()
        embedding_client = MagicMock()

        with mock.patch(
            "app.adapters.out.knowledge_lancedb_adapter.connect_async",
            new_callable=AsyncMock,
            return_value=db_mock,
        ):
            result = await KnowledgeLanceDBAdapter.create(
                db_path=self.faker.uri_path(),
                table_name=table_name,
                embedding_model_name=embedding_model_name,
                embedding_client=embedding_client,
            )

        db_mock.open_table.assert_called_once_with(table_name)
        mock_logging.assert_called_once_with(
            f"Successfully connected to LanceDB and opened table: {table_name}"
        )
        assert result.db == db_mock
        assert result.table == db_mock.open_table.return_value
        assert result.embedding_model_name == embedding_model_name
        assert result.embedding_client == embedding_client

    @pytest.mark.asyncio
    @mock.patch("logging.exception")
    async def test_knowledge_lancedb_adapter_create_raise_exception(self, mock_logging):
        table_name = self.faker.word()
        embedding_model_name = self.faker.word()
        embedding_client = MagicMock()

        with (
            mock.patch(
                "app.adapters.out.knowledge_lancedb_adapter.connect_async",
                new_callable=AsyncMock,
                side_effect=Exception,
            ),
            pytest.raises(Exception),
        ):
            await KnowledgeLanceDBAdapter.create(
                db_path=self.faker.uri_path(),
                table_name=table_name,
                embedding_model_name=embedding_model_name,
                embedding_client=embedding_client,
            )

        mock_logging.assert_called_once_with(
            "Failed to initialize LanceDB adapter", ANY
        )

    @pytest.mark.asyncio
    async def test_knowledge_lancedb_adapter_create_embedding(self):
        mock_embedding_client = AsyncMock()
        embedding_model_name = self.faker.word()
        text = self.faker.sentence()

        with mock.patch("logging.getLogger") as mock_logger:
            adapter = KnowledgeLanceDBAdapter(
                db=AsyncMock(),
                table=AsyncMock(),
                embedding_model_name=embedding_model_name,
                embedding_client=mock_embedding_client,
            )

        await adapter.create_embedding(text)

        mock_embedding_client.embeddings.create.assert_called_once_with(
            input=[text], model=embedding_model_name
        )
        mock_logger.return_value.debug.assert_called_once_with(
            f"Generated embedding: {mock_embedding_client.embeddings.create.return_value.data[0].embedding}"
        )

    @pytest.mark.asyncio
    async def test_knowledge_lancedb_adapter_create_embedding_raise_exception(self):
        mock_embedding_client = MagicMock()
        mock_embedding_client.embeddings.create = AsyncMock()
        mock_embedding_client.embeddings.create.side_effect = Exception
        embedding_model_name = self.faker.word()
        text = self.faker.sentence()

        with (
            mock.patch("logging.getLogger") as mock_logger,
            pytest.raises(RuntimeError),
        ):
            adapter = KnowledgeLanceDBAdapter(
                db=AsyncMock(),
                table=AsyncMock(),
                embedding_model_name=embedding_model_name,
                embedding_client=mock_embedding_client,
            )
            await adapter.create_embedding(text)

        mock_embedding_client.embeddings.create.assert_called_once_with(
            input=[text], model=embedding_model_name
        )
        mock_logger.return_value.exception.assert_called_once_with(
            f"Failed to create embedding for text: {text}", ANY
        )

    @pytest.mark.asyncio
    async def test_knowledge_lancedb_adapter_ping_True(self):
        mock_db = MagicMock()
        mock_db.is_open = MagicMock(return_value=True)

        with mock.patch("logging.getLogger") as mock_logger:
            adapter = KnowledgeLanceDBAdapter(
                db=mock_db,
                table=AsyncMock(),
                embedding_model_name=self.faker.word(),
                embedding_client=AsyncMock(),
            )

        await adapter.ping()

        mock_db.is_open.assert_called_once()
        mock_logger.return_value.debug.assert_called_once_with(
            "Knowledge base ping successful."
        )

    @pytest.mark.asyncio
    async def test_knowledge_lancedb_adapter_ping_False(self):
        mock_db = MagicMock()
        mock_db.is_open = MagicMock(return_value=False)

        with (
            mock.patch("logging.getLogger") as mock_logger,
            pytest.raises(RuntimeError) as exception_raised,
        ):
            adapter = KnowledgeLanceDBAdapter(
                db=mock_db,
                table=AsyncMock(),
                embedding_model_name=self.faker.word(),
                embedding_client=AsyncMock(),
            )
            await adapter.ping()

        mock_db.is_open.assert_called_once()
        mock_logger.return_value.exception.assert_called_once_with(
            "Knowledge base connectivity test failed", ANY
        )
        assert (
            str(exception_raised.value)
            == "Knowledge base connectivity test failed: Knowledge base connection is not open."
        )

    @pytest.mark.asyncio
    async def test_knowledge_lancedb_adapter_ping_raise_exception(self):
        mock_db = MagicMock()
        mock_db.is_open.side_effect = Exception

        with (
            mock.patch("logging.getLogger") as mock_logger,
            pytest.raises(RuntimeError) as exception_raised,
        ):
            adapter = KnowledgeLanceDBAdapter(
                db=mock_db,
                table=AsyncMock(),
                embedding_model_name=self.faker.word(),
                embedding_client=AsyncMock(),
            )
            await adapter.ping()

        mock_db.is_open.assert_called_once()
        mock_logger.return_value.exception.assert_called_once_with(
            "Knowledge base connectivity test failed", ANY
        )
        assert (
            str(exception_raised.value) == "Knowledge base connectivity test failed: "
        )

    @pytest.mark.asyncio
    async def test_knowledge_lancedb_adapter_search(self):
        mock_table = AsyncMock()
        mock_create_embedding = AsyncMock()
        mock_data = [
            {
                "question": "What is X?",
                "cot": "Reasoning",
                "sql_query": "SELECT * from Y",
                "vector": [0.1],  # Include columns to be dropped
                "chunk_id": 1,
                "_distance": 0.5,
            }
        ]
        mock_df = pd.DataFrame(mock_data)
        mock_search_result = MagicMock()
        mock_limited = MagicMock()
        mock_table.search.return_value = mock_search_result
        mock_search_result.limit.return_value = mock_limited
        mock_limited.to_pandas = AsyncMock(return_value=mock_df)

        with mock.patch("logging.getLogger") as mock_logger:
            adapter = KnowledgeLanceDBAdapter(
                db=MagicMock(),
                table=mock_table,
                embedding_model_name=self.faker.word(),
                embedding_client=AsyncMock(),
            )

        with mock.patch.object(
            adapter,
            "create_embedding",
            new_callable=AsyncMock,
            return_value=mock_create_embedding,
        ):
            result = await adapter.search(query="test query")

        expected = (
            "question: What is X?\n" "cot: Reasoning\n" "sql_query: SELECT * from Y"
        )
        assert expected in result
        mock_table.search.assert_called_once_with(mock_create_embedding)
        mock_limited.to_pandas.assert_awaited_once()
        mock_logger.return_value.debug.assert_any_call(
            f"Query embedding: {mock_create_embedding}"
        )
        mock_logger.return_value.debug.assert_any_call(
            f"Search results dataframe: {mock_df}"
        )

    @pytest.mark.asyncio
    async def test_knowledge_lancedb_adapter_search_raise_exception(self):
        mock_table = AsyncMock()

        with mock.patch("logging.getLogger") as mock_logger:
            adapter = KnowledgeLanceDBAdapter(
                db=MagicMock(),
                table=mock_table,
                embedding_model_name=self.faker.word(),
                embedding_client=AsyncMock(),
            )

        with (
            mock.patch.object(adapter, "create_embedding", side_effect=Exception),
            pytest.raises(RuntimeError) as exception_raised,
        ):
            await adapter.search(query="test query")

        mock_logger.return_value.exception.assert_called_once_with(
            "Failed to search knowledge base for query: test query", ANY
        )
        assert str(exception_raised.value) == "Failed to search knowledge base."
