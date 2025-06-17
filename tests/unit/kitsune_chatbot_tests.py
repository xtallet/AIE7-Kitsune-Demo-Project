from unittest.mock import AsyncMock, MagicMock

import pytest
from application.chatbot import KitsuneChatbot


class TestKitsuneChatbot:
    @pytest.mark.asyncio
    async def test_get_natural_language_answer(self):
        fake_agent = MagicMock()
        fake_agent.run = AsyncMock()
        fake_agent.run.return_value = "Response from agent"

        chatbot = KitsuneChatbot(
            chatbot_agent=fake_agent,
            sql_agent=MagicMock(),
            cache=MagicMock(),
            knowledge_base=MagicMock(),
            guardrail=MagicMock(),
            logger=MagicMock(),
        )

        result = await chatbot._get_natural_language_answer(
            question="any question", sql_answer="any answer"
        )

        assert result == "Response from agent"

    @pytest.mark.asyncio
    async def test_get_and_execute_sql_from_model(self):
        fake_sql_agent = MagicMock()
        fake_sql_agent.run = AsyncMock()
        fake_sql_agent.run.return_value = "sql result from agent"

        context_result = (
            "question: Which policy has the highest premium in our portfolio?"
            "cot: Q: Which policy has the highest premium in our portfolio? A: The primary data is provided through the custom PostgreSQL function 'get_premiums()'. This custom function internally calculates the premium of the policy and returns: policy_id : This is the policy identifier policy_reference: This is the reference of the policy is_endorsement : Boolean field which indicates if the policy is an endorsement or not status_group : which has 2 options 'written' and 'not_written' premium: the amount of the policy premium We started the query with a CTE to use a Window function \u201cROW_NUMBER() OVER (PARTITION BY status_group ORDER BY premium DESC nulls last) AS row_num\u201c to sort the premiums from highest to lowest of each status and be sure to pull the null values to the end since to return a numeric value is mandatory. Finally, we select the main fields to return \u201cpolicy_reference, status_group, premium, row_num\u201c from our CTE and select the first already-ordered result. The query SQL is: WITH ranked_premiums AS (SELECT policy_reference, status_group, premium, ROW_NUMBER() OVER (PARTITION BY status_group ORDER BY premium DESC nulls last) AS row_num FROM get_premiums()) SELECT policy_reference, status_group, premium, row_num FROM ranked_premiums WHERE row_num = 1 and policy_reference IS NOT NULL ORDER BY status_group; "
        )

        fake_lance_db = MagicMock()
        fake_lance_db.search = AsyncMock()
        fake_lance_db.search.return_value = context_result

        chatbot = KitsuneChatbot(
            chatbot_agent=MagicMock(),
            sql_agent=fake_sql_agent,
            cache=MagicMock(),
            knowledge_base=fake_lance_db,
            guardrail=MagicMock(),
            logger=MagicMock(),
        )

        result = await chatbot._get_and_execute_sql_from_model(question="any question")

        fake_lance_db.search.assert_called_once_with(query="any question")
        fake_sql_agent.run.assert_called_once_with(
            user_question="any question", context={"example": context_result}
        )

        assert result == (context_result, "sql result from agent")
