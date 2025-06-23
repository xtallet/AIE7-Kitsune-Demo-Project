from unittest.mock import AsyncMock, MagicMock

import pytest
from agno.run.response import RunResponse

from app.agents.sql_agent import SQLAgent


class TestSQLAgent:
    @pytest.mark.asyncio
    async def test_run(self):
        fake_logger = MagicMock()

        sql_agent = SQLAgent(context="any context")
        
        sql_agent.logger = fake_logger
        
        assert sql_agent.agent.context == "any context"
        
        sql_agent.agent = MagicMock()
        sql_agent.agent.arun = AsyncMock()
        sql_agent.agent.arun.return_value = RunResponse(content="sql query from agent")

        result = await sql_agent.run(
            user_question="any question"
        )

        sql_agent.agent.arun.assert_called_once_with("any question")
        fake_logger.debug.assert_called_with(
            "Generated sql from Agno: %s", "sql query from agent"
        )
        
        assert result == "sql query from agent"

    @pytest.mark.asyncio
    async def test_run_exception(self):
        fake_logger = MagicMock()
        sql_agent = SQLAgent(context="any context")

        exception = Exception("error")

        sql_agent.logger = fake_logger
        sql_agent.agent = MagicMock()
        sql_agent.agent.arun = AsyncMock(side_effect=exception)

        with pytest.raises(Exception):
            await sql_agent.run(user_question="any question")

        sql_agent.agent.arun.assert_called_once_with("any question")

        fake_logger.exception.assert_called_once_with(
            "Error querying Agno agent for sql generation: %s", exception
        )
