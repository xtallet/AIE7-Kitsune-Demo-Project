import pytest

from app.agents.sql_agent import SQLAgent


@pytest.mark.skip(
    "Skipping test for Azure OpenAI due to costs, execute manually when needed."
)
class TestSQLAgent:
    @pytest.mark.asyncio
    async def test_agent_connection_and_response(self):
        context = (
            "question: Which policy has the highest premium in our portfolio?"
            "cot: Q: Which policy has the highest premium in our portfolio? A: The primary data is provided through the custom PostgreSQL function 'get_premiums()'. This custom function internally calculates the premium of the policy and returns: policy_id : This is the policy identifier policy_reference: This is the reference of the policy is_endorsement : Boolean field which indicates if the policy is an endorsement or not status_group : which has 2 options 'written' and 'not_written' premium: the amount of the policy premium We started the query with a CTE to use a Window function \u201cROW_NUMBER() OVER (PARTITION BY status_group ORDER BY premium DESC nulls last) AS row_num\u201c to sort the premiums from highest to lowest of each status and be sure to pull the null values to the end since to return a numeric value is mandatory. Finally, we select the main fields to return \u201cpolicy_reference, status_group, premium, row_num\u201c from our CTE and select the first already-ordered result. The query SQL is: WITH ranked_premiums AS (SELECT policy_reference, status_group, premium, ROW_NUMBER() OVER (PARTITION BY status_group ORDER BY premium DESC nulls last) AS row_num FROM get_premiums()) SELECT policy_reference, status_group, premium, row_num FROM ranked_premiums WHERE row_num = 1 and policy_reference IS NOT NULL ORDER BY status_group; "
            "sql_query: WITH ranked_premiums AS (SELECT policy_reference, status_group, premium, ROW_NUMBER() OVER (PARTITION BY status_group ORDER BY premium DESC nulls last) AS row_num FROM get_premiums()) SELECT policy_reference, status_group, premium, row_num FROM ranked_premiums WHERE row_num = 1 and policy_reference IS NOT NULL ORDER BY status_group"
            "question: Which policy has the lowest premium in our portfolio?"
            "cot: CoT: Q: Which policy has the lowest premium in our portfolio? A: The primary data is provided through the custom PostgreSQL function 'get_premiums()'. This custom function internally calculates the premium of the policy and returns: policy_id : This is the policy identifier policy_reference: This is the reference of the policy is_endorsement : Boolean field which indicates if the policy is an endorsement or not status_group : which has 2 options 'written' and 'not_written' premium: the amount of the policy premium We started the query with a CTE to use a Window function 'ROW_NUMBER() OVER (PARTITION BY status_group ORDER BY premium ASC nulls last) AS row_num' to sort the premium from lowest to highest of each status and be sure to pull the null values to the end since to return a numeric value is mandatory. Finally, we select the main fields to return 'policy_reference, status_group, premium, row_num' from our CTE and select the first already-ordered result. The query SQL is: WITH ranked_premiums AS (SELECT policy_reference, status_group, premium, ROW_NUMBER() OVER (PARTITION BY status_group ORDER BY premium ASC NULLS LAST) AS row_num FROM redray.get_premiums()) SELECT policy_reference, status_group, premium, row_num FROM ranked_premiums WHERE row_num = 1 AND policy_reference IS NOT NULL ORDER BY status_group;"
            "sql_query: WITH ranked_premiums AS (SELECT policy_reference, status_group, premium, ROW_NUMBER() OVER (PARTITION BY status_group ORDER BY premium ASC NULLS LAST) AS row_num FROM redray.get_premiums()) SELECT policy_reference, status_group, premium, row_num FROM ranked_premiums WHERE row_num = 1 AND policy_reference IS NOT NULL ORDER BY status_group"
            "question: What is the average premium per policy in the portfolio?"
            "cot: CoT: Q: What is the average premium per policy in the portfolio? A: The primary data is provided through the custom PostgreSQL function 'get_premiums()'. This custom function internally calculates the premium of the policy and returns: policy_id : This is the policy identifier policy_reference: This is the reference of the policy is_endorsement : Boolean field which indicates if the policy is an endorsement or not status_group : which has 2 options 'written' and 'not_written' premium: the amount of the policy premium We started the query selecting directly the main fields 'policy_reference, premium' from our PostgreSQL custom function 'get_premiums()', calculating the premium average, grouping it by each policy_reference and sorting the results by the policy_reference ascendingly. The SQL query is: SELECT policy_reference, AVG(premium) AS premium_average FROM get_premiums() GROUP BY policy_reference ORDER BY policy_reference ASC; "
            "sql_query: SELECT policy_reference, AVG(premium) AS premium_average FROM get_premiums() GROUP BY policy_reference ORDER BY policy_reference ASC"
        )

        agent = SQLAgent(context=context)

        result = await agent.run(
            user_question="Which policy has the highest premium in our portfolio?",
        )

        assert "('RE2500008', 'not_written', Decimal('9000000.0000000'), 1)" in result
        assert "('RE2500019', 'written', Decimal('3000000.0000000'), 1)" in result
