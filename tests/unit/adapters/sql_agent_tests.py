import pytest
from unittest.mock import AsyncMock, MagicMock
from agno.run.response import RunResponse
from app.adapters.out.sql_agent_adapter import SQLAgentAdapter

class TestSQLAgent:
    @pytest.mark.asyncio
    async def test_run(self):
      fake_logger = MagicMock()
      fake_db_tools = MagicMock()
      
      sql_agent = SQLAgentAdapter(model=MagicMock(), postgres_toolkit=fake_db_tools)
      sql_agent.logger = fake_logger
      sql_agent.agent = MagicMock()
      sql_agent.agent.arun = AsyncMock()
      sql_agent.agent.arun.return_value = RunResponse(content="sql query from agent")
      
      result = await sql_agent.run(user_question="any question", context="any context")
      
      sql_agent.agent.arun.assert_called_once_with("any question")
      fake_logger.debug.assert_called_with(
          "Generated sql from Agno: %s", "sql query from agent"
      )
      
      assert sql_agent.agent.context == "any context"
      assert result == "sql query from agent"
      
    @pytest.mark.asyncio
    async def test_run_exception(self):
      fake_logger = MagicMock()
      fake_db_tools = MagicMock()
      sql_agent = SQLAgentAdapter(model=MagicMock(), postgres_toolkit=fake_db_tools)
      
      exception = Exception("error")
      
      sql_agent.logger = fake_logger
      sql_agent.agent = MagicMock()
      sql_agent.agent.arun = AsyncMock(side_effect=exception)
      
      with pytest.raises(Exception):
        await sql_agent.run(user_question="any question", context="any context")
      
      sql_agent.agent.arun.assert_called_once_with("any question")
      
      fake_logger.exception.assert_called_once_with(
          "Error querying Agno agent for sql generation: %s", exception
      )
      