import json
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import faker
import pytest

from app.adapters.out.guardrail_adapter import GuardrailAdapter, has_topic_match


class TestGuardrailAdapter:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.faker = faker.Faker()
        self.allowed_topics = ["insurance policies", "claims", "coverage"]

        self.mock_azure_client = MagicMock()
        self.mock_completions = AsyncMock()
        self.mock_azure_client.chat.completions.create = self.mock_completions

        # Create the adapter with mock client
        with mock.patch(
            "app.adapters.out.guardrail_adapter.AzureOpenAI",
            return_value=self.mock_azure_client,
        ):
            self.adapter = GuardrailAdapter(
                model_name=self.faker.word(),
                azure_deployment=self.faker.word(),
                azure_endpoint=self.faker.url(),
                api_version=self.faker.word(),
                api_key=self.faker.password(),
                allowed_topics=self.allowed_topics,
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "topics_in_response, expected_result",
        [
            (["insurance policies"], True),
            (["unrelated topic"], False),
            ([], False),
        ],
    )
    async def test_validate_question(self, topics_in_response, expected_result):
        user_text = "What is an insurance policy?"

        mock_function_call = MagicMock()
        mock_function_call.arguments = json.dumps(
            {"topics_present": topics_in_response}
        )

        mock_message = MagicMock()
        mock_message.function_call = mock_function_call

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        self.mock_completions.return_value = mock_response

        result = await self.adapter.validate_question(user_text)

        assert result is expected_result
        self.mock_completions.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_question_exception(self):
        user_text = "What is an insurance policy?"
        self.mock_completions.side_effect = Exception("API Error")

        result = await self.adapter.validate_question(user_text)

        assert result is False
        self.mock_completions.assert_called_once()

    @pytest.mark.parametrize(
        "detected_topics, allowed_topics, expected_result",
        [
            # Exact matches
            (["insurance policies"], ["insurance policies", "claims"], True),
            (["claims"], ["insurance policies", "claims"], True),
            # Singular/plural variations
            (["policy"], ["policies", "claims"], True),
            (["policies"], ["policy", "claims"], True),
            (["claim"], ["claims", "coverage"], True),
            # Stemmed variations
            (["insuring"], ["insurance", "claims"], True),
            (["insured"], ["insurance", "claims"], True),
            (["claiming"], ["claim", "coverage"], True),
            (["coverages"], ["coverage", "policies"], True),
            # Compound words
            (["life insurance"], ["insurance", "claims"], True),
            (["auto policy"], ["policy", "coverage"], True),
            # No matches
            (["banking"], ["insurance", "claims", "coverage"], False),
            (["loans"], ["policy", "claims", "coverage"], False),
            ([], ["policy", "claims"], False),
        ],
    )
    def test_has_topic_match(
        self, monkeypatch, detected_topics, allowed_topics, expected_result
    ):
        result = has_topic_match(detected_topics, allowed_topics)
        assert result == expected_result
