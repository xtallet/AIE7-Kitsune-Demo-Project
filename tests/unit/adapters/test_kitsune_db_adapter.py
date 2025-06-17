from unittest import mock
from unittest.mock import ANY, AsyncMock, MagicMock

import faker
import pytest

from app.adapters.out.kitsune_db_adapter import KitsuneDBAdapter


class TestKitsuneDBAdapter:
    @pytest.fixture(autouse=True)
    @mock.patch("logging.getLogger")
    def setup_method(self, mock_logger):
        self.faker = faker.Faker()
        self.host = self.faker.ipv4()
        self.port = self.faker.random_int(min=1024, max=65535)
        self.user = self.faker.user_name()
        self.password = self.faker.password()
        self.db_name = self.faker.word()
        self.db_schema = self.faker.word()
        self.adapter = KitsuneDBAdapter(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db_name=self.db_name,
            db_schema=self.db_schema,
        )
        self.mock_logger = mock_logger
        self.query = self.faker.sentence()

    @pytest.mark.asyncio
    async def test_run_sql_query(self):
        mocked_id = self.faker.random_int(min=1, max=100)
        mocked_name = self.faker.word()
        mock_conn = AsyncMock()
        mock_cursor_cm = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor_cm.__aenter__.return_value = mock_cursor
        mock_cursor_cm.__aexit__.return_value = AsyncMock()
        mock_conn.cursor = MagicMock(return_value=mock_cursor_cm)
        mock_cursor.fetchall.return_value = [(mocked_id, mocked_name)]
        mock_cursor.description = [mock.Mock(), mock.Mock()]
        mock_cursor.description[0].name = "id"
        mock_cursor.description[1].name = "name"
        mock_get_client = AsyncMock(return_value=mock_conn)

        with mock.patch.object(
            KitsuneDBAdapter, "_get_kitsune_db_client", mock_get_client
        ):
            result = await self.adapter.run_sql_query(self.query)

        assert result == f"Results:\nid: {mocked_id}, name: {mocked_name}"
        self.mock_logger.return_value.debug.assert_any_call(
            f"Search path set to schema: {self.db_schema}"
        )
        self.mock_logger.return_value.debug.assert_any_call(
            f"Query results: {mock_cursor.fetchall.return_value}"
        )

    @pytest.mark.asyncio
    async def test_run_sql_query_empty_results(self):
        mock_conn = AsyncMock()
        mock_cursor_cm = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor_cm.__aenter__.return_value = mock_cursor
        mock_cursor_cm.__aexit__.return_value = AsyncMock()
        mock_conn.cursor = MagicMock(return_value=mock_cursor_cm)
        mock_cursor.fetchall.return_value = []
        mock_cursor.description = [mock.Mock(), mock.Mock()]
        mock_cursor.description[0].name = "id"
        mock_cursor.description[1].name = "name"
        mock_get_client = AsyncMock(return_value=mock_conn)

        with mock.patch.object(
            KitsuneDBAdapter, "_get_kitsune_db_client", mock_get_client
        ):
            result = await self.adapter.run_sql_query(self.query)

        assert result == "Results:"

    @pytest.mark.asyncio
    async def test_run_sql_query_raise_exception(self):
        mock_conn = AsyncMock()
        mock_cursor_cm = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor_cm.__aenter__.return_value = mock_cursor
        mock_cursor_cm.__aexit__.return_value = AsyncMock()
        mock_conn.cursor = MagicMock(return_value=mock_cursor_cm)
        mock_cursor.fetchall.side_effect = Exception
        mock_get_client = AsyncMock(return_value=mock_conn)

        with (
            mock.patch.object(
                KitsuneDBAdapter, "_get_kitsune_db_client", mock_get_client
            ),
            pytest.raises(
                RuntimeError, match="An error occurred while executing the SQL query."
            ),
        ):
            await self.adapter.run_sql_query(self.query)

        self.mock_logger.return_value.exception.assert_any_call(
            f"An error occurred while executing the SQL query: {self.query}", ANY
        )

    @pytest.mark.asyncio
    async def test_ping_returns_true_on_successful_query(self):
        mock_conn = AsyncMock()
        mock_cursor_cm = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor_cm.__aenter__.return_value = mock_cursor
        mock_cursor_cm.__aexit__.return_value = AsyncMock()
        mock_conn.cursor = MagicMock(return_value=mock_cursor_cm)
        mock_cursor.fetchone.return_value = (1,)
        mock_get_client = AsyncMock(return_value=mock_conn)

        with mock.patch.object(
            KitsuneDBAdapter, "_get_kitsune_db_client", mock_get_client
        ):
            result = await self.adapter.ping()

        assert result is True

    @pytest.mark.asyncio
    async def test_ping_raises_runtime_error_on_failure(self):
        exception_message = "error"
        mock_conn = AsyncMock()
        mock_cursor_cm = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor_cm.__aenter__.return_value = mock_cursor
        mock_conn.cursor = MagicMock(return_value=mock_cursor_cm)
        mock_cursor.fetchone.side_effect = Exception(exception_message)
        mock_get_client = AsyncMock(return_value=mock_conn)

        with (
            mock.patch.object(
                KitsuneDBAdapter, "_get_kitsune_db_client", mock_get_client
            ),
            pytest.raises(
                RuntimeError,
                match=f"Database connectivity test failed: {exception_message}",
            ),
        ):
            await self.adapter.ping()

        self.mock_logger.return_value.exception.assert_any_call(
            "Database connectivity test failed", ANY
        )
