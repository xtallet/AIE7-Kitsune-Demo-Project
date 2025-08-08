from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agno.exceptions import StopAgentRun
from langgraph.constants import START
from langgraph.graph import END

from app.application.graph import (
    cbot_agent,
    compile_graph,
    guardrail_node,
    retriever_node,
    sql_generator_node,
    sql_tool,
)
from app.domain.domain import CbotState


class TestGraph:
    """Unit tests for the graph module in the application."""

    @pytest.fixture(autouse=True)
    def setUp(self):
        self.state = CbotState(
            question="What is the total premium for policy XYZ123?",
            user_id="test_user_123",
            session_id="test_session_456",
        )

    @pytest.mark.asyncio
    @patch("app.application.graph.build_guardrail_adapter")
    async def test_guardrail_node_valid_question(self, mock_build_guardrail_adapter):
        mock_adapter = AsyncMock()
        mock_adapter.validate_question.return_value = True
        mock_build_guardrail_adapter.return_value = mock_adapter

        result = await guardrail_node(self.state)

        mock_adapter.validate_question.assert_awaited_once_with(self.state.question)
        assert result == self.state

    @pytest.mark.asyncio
    @patch("app.application.graph.build_guardrail_adapter")
    async def test_guardrail_node_invalid_question(self, mock_build_guardrail_adapter):
        mock_adapter = AsyncMock()
        mock_adapter.validate_question.return_value = False
        mock_build_guardrail_adapter.return_value = mock_adapter

        with pytest.raises(StopAgentRun) as excinfo:
            await guardrail_node(self.state)

        mock_adapter.validate_question.assert_awaited_once_with(self.state.question)
        assert "Question does not meet the guardrails criteria" in str(excinfo.value)

    @pytest.mark.asyncio
    @patch("app.application.graph.build_knowledge_base_adapter")
    async def test_retriever_node_success(self, mock_build_kb_adapter):
        mock_adapter = AsyncMock()
        mock_adapter.search.return_value = "Sample context data for testing"
        mock_build_kb_adapter.return_value = mock_adapter

        result = await retriever_node(self.state)

        mock_adapter.search.assert_awaited_once_with(query=self.state.question)
        assert result.context == "Sample context data for testing"
        assert result.question == self.state.question

    @pytest.mark.asyncio
    @patch("app.application.graph.build_knowledge_base_adapter")
    async def test_retriever_node_exception(self, mock_build_kb_adapter):
        mock_adapter = AsyncMock()
        mock_adapter.search.side_effect = Exception("Test search error")
        mock_build_kb_adapter.return_value = mock_adapter

        with pytest.raises(StopAgentRun) as excinfo:
            await retriever_node(self.state)

        assert "Failed to get context or execute SQL query" in str(excinfo.value)
        assert "Test search error" in str(excinfo.value)

    @pytest.mark.asyncio
    @patch("app.application.graph.build_llm_adapter")
    async def test_sql_generator_node_success(self, mock_build_llm_adapter):
        mock_adapter = AsyncMock()

        async def mock_generate_sql(state):
            state.sql_query = "SELECT * FROM policies WHERE policy_id = 'XYZ123'"
            return state

        mock_adapter.generate_sql_query = mock_generate_sql
        mock_build_llm_adapter.return_value = mock_adapter

        result = await sql_generator_node(self.state)

        assert result.sql_query == "SELECT * FROM policies WHERE policy_id = 'XYZ123'"
        assert result.question == self.state.question

    @pytest.mark.asyncio
    @patch("app.application.graph.build_llm_adapter")
    async def test_sql_generator_node_no_sql_query(self, mock_build_llm_adapter):
        mock_adapter = AsyncMock()
        mock_adapter.generate_sql_query.return_value = self.state
        mock_build_llm_adapter.return_value = mock_adapter

        with pytest.raises(ValueError) as excinfo:
            await sql_generator_node(self.state)

        assert "SQL Agent did not return a valid result" in str(excinfo.value)

    @pytest.mark.asyncio
    @patch("app.application.graph.postgres_toolkit")
    async def test_sql_tool_success(self, mock_postgres_toolkit):
        self.state.sql_query = "SELECT * FROM policies WHERE policy_id = 'XYZ123'"
        mock_postgres_toolkit.return_value = [{"policy_id": "XYZ123", "premium": 1500}]

        result = await sql_tool(self.state)

        mock_postgres_toolkit.assert_called_once_with(self.state.sql_query)
        assert result.sql_result == [{"policy_id": "XYZ123", "premium": 1500}]
        assert result.question == self.state.question

    @pytest.mark.asyncio
    @patch("app.application.graph.ChatbotAgent")
    async def test_cbot_agent_success(self, mock_chatbot_agent_class):
        self.state.sql_result = [{"policy_id": "XYZ123", "premium": 1500}]

        mock_agent = AsyncMock()
        mock_agent.run.return_value = (
            "The total premium for policy XYZ123 is $1,500.",
            "new_session_id",
        )
        mock_chatbot_agent_class.return_value = mock_agent

        result = await cbot_agent(self.state)

        mock_agent.run.assert_awaited_once_with(
            user_question=self.state.question,
            context={"sql_result": self.state.sql_result},
            user_id=self.state.user_id,
            session_id="test_session_456",
        )

        assert result.answer == "The total premium for policy XYZ123 is $1,500."
        assert result.session_id == "new_session_id"
        assert result.question == self.state.question

    @pytest.mark.asyncio
    @patch("app.application.graph.StateGraph")
    async def test_compile_graph(self, mock_state_graph):
        mock_graph = MagicMock()
        mock_state_graph.return_value = mock_graph
        mock_compiled_graph = MagicMock()
        mock_graph.compile.return_value = mock_compiled_graph

        result = await compile_graph()

        mock_state_graph.assert_called_once_with(CbotState)

        assert mock_graph.add_node.call_count == 5
        mock_graph.add_node.assert_any_call("guardrail", guardrail_node)
        mock_graph.add_node.assert_any_call("retriever", retriever_node)
        mock_graph.add_node.assert_any_call("sql_generator", sql_generator_node)
        mock_graph.add_node.assert_any_call("sql_tool", sql_tool)
        mock_graph.add_node.assert_any_call("cbot_agent", cbot_agent)

        assert mock_graph.add_edge.call_count == 6
        mock_graph.add_edge.assert_any_call(START, "guardrail")
        mock_graph.add_edge.assert_any_call("guardrail", "retriever")
        mock_graph.add_edge.assert_any_call("retriever", "sql_generator")
        mock_graph.add_edge.assert_any_call("sql_generator", "sql_tool")
        mock_graph.add_edge.assert_any_call("sql_tool", "cbot_agent")
        mock_graph.add_edge.assert_any_call("cbot_agent", END)

        mock_graph.compile.assert_called_once()
        assert result == mock_compiled_graph
