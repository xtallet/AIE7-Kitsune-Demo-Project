import logging

from agno.exceptions import StopAgentRun
from langgraph.graph import END, START, StateGraph

from app.adapters.adapter_factory import (
    build_guardrail_adapter,
    build_knowledge_base_adapter,
    build_llm_adapter,
)
from app.agents.chat_agent import ChatbotAgent
from app.domain.domain import CbotState
from app.toolkits.postgres_toolkit import postgres_toolkit

logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def guardrail_node(state: CbotState) -> CbotState:
    guardrail_adapter = build_guardrail_adapter()
    is_valid = await guardrail_adapter.validate_question(state.question)
    if not is_valid:
        state.answer = "I am sorry, but I cannot assist with that request as it falls outside my area of expertise."

    return state


async def retriever_node(state: CbotState) -> CbotState:
    try:
        lancedb_adapter = await build_knowledge_base_adapter()
        state.context = await lancedb_adapter.search(query=state.question)
    except Exception as e:
        logger.exception("Failed to get context from LanceDB adapter", exc_info=e)
        raise StopAgentRun(f"Failed to get context or execute SQL query: {str(e)}")

    return state


async def sql_generator_node(state: CbotState):
    llm_adapter = build_llm_adapter()
    state = await llm_adapter.generate_sql_query(state)
    if not state.sql_query:
        raise ValueError("SQL Agent did not return a valid result.")
    return state


async def sql_tool(state: CbotState) -> CbotState:
    state.sql_result = postgres_toolkit(state.sql_query)  # type: ignore[arg-type]
    return state


async def cbot_agent(state: CbotState) -> CbotState:
    agent = ChatbotAgent()
    answer, session_id = await agent.run(
        user_question=state.question,
        context={"sql_result": state.sql_result},
        user_id=state.user_id,
        session_id=state.session_id,
    )
    state.answer = answer
    state.session_id = session_id
    return state


def should_continue_after_guardrail(state: CbotState) -> str:
    if state.answer:  # Guardrail generated an answer (blocked request)
        return "END"
    else:
        return "retriever"


async def compile_graph():
    graph = StateGraph(CbotState)
    graph.add_node("guardrail", guardrail_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("sql_generator", sql_generator_node)
    graph.add_node("sql_tool", sql_tool)
    graph.add_node("cbot_agent", cbot_agent)

    graph.add_edge(START, "guardrail")
    graph.add_conditional_edges(
        "guardrail",
        should_continue_after_guardrail,
        {"END": END, "retriever": "retriever"},
    )

    graph.add_edge("retriever", "sql_generator")
    graph.add_edge("sql_generator", "sql_tool")
    graph.add_edge("sql_tool", "cbot_agent")
    graph.add_edge("cbot_agent", END)
    compiled_graph = graph.compile()

    return compiled_graph
