import random
from unittest import mock
from unittest.mock import ANY, AsyncMock, MagicMock

import faker
import pytest
from guardrails import ValidationOutcome
from guardrails.errors import ValidationError
from pydantic import ValidationError as PydanticValidationError

from app.adapters.out.guardrail_adapter import GuardrailAdapter


class TestGuardrailAdapter:
    @pytest.fixture(autouse=True)
    @mock.patch("logging.getLogger")
    @mock.patch("app.adapters.out.guardrail_adapter.AsyncGuard")
    @mock.patch("app.adapters.out.guardrail_adapter.AzureOpenAI")
    def setup_method(self, mock_azure, mock_guard, mock_logger):
        self.faker = faker.Faker()
        self.allowed_topics = [self.faker.word() for _ in range(3)]
        self.adapter = GuardrailAdapter(
            model_name=self.faker.word(),
            azure_deployment=self.faker.word(),
            azure_endpoint=self.faker.url(),
            api_version=self.faker.word(),
            api_key=self.faker.password(),
            allowed_topics=self.allowed_topics,
        )
        self.mock_logger = mock_logger
        self.mock_client = mock_azure
        self.mock_guard = mock_guard

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "validation_passed, validation_summaries",
        [
            (True, []),
            (False, [MagicMock(failure_reason="failure reason")]),
        ],
    )
    @mock.patch("app.adapters.out.guardrail_adapter.AsyncGuard")
    @mock.patch("app.adapters.out.guardrail_adapter.AzureOpenAI")
    async def test_validate_question(
        self, _, mock_guard, validation_passed, validation_summaries
    ):
        user_text = self.faker.word()
        allowed_topics = [self.faker.word() for _ in range(3)]

        # Mocks needed to create before instantiating GuardrailAdapter, otherwise it will use the real AsyncGuard
        validation_result = mock.Mock(
            validation_passed=validation_passed,
            validation_summaries=validation_summaries,
        )
        mock_guard_instance = MagicMock()
        mock_guard_instance.use.return_value = mock_guard_instance
        mock_guard_instance.validate = AsyncMock(return_value=validation_result)
        mock_guard.return_value = mock_guard_instance

        adapter = GuardrailAdapter(
            model_name=self.faker.word(),
            azure_deployment=self.faker.word(),
            azure_endpoint=self.faker.url(),
            api_version=self.faker.word(),
            api_key=self.faker.password(),
            allowed_topics=allowed_topics,
        )

        result = await adapter.validate_question(user_text)

        assert result is validation_passed

    @pytest.mark.asyncio
    @mock.patch("app.adapters.out.guardrail_adapter.AsyncGuard")
    @mock.patch("app.adapters.out.guardrail_adapter.AzureOpenAI")
    async def test_validate_question_raises_exception(self, _, mock_guard):
        user_text = self.faker.word()
        allowed_topics = [self.faker.word() for _ in range(3)]

        # Mocks needed to create before instantiating GuardrailAdapter, otherwise it will use the real AsyncGuard
        mock_guard_instance = MagicMock()
        mock_guard_instance.use.return_value = mock_guard_instance
        mock_guard_instance.validate.side_effect = ValidationError("Validation failed")
        mock_guard.return_value = mock_guard_instance

        adapter = GuardrailAdapter(
            model_name=self.faker.word(),
            azure_deployment=self.faker.word(),
            azure_endpoint=self.faker.url(),
            api_version=self.faker.word(),
            api_key=self.faker.password(),
            allowed_topics=allowed_topics,
        )

        result = await adapter.validate_question(user_text)

        assert result is False

    def test_azure_llm_callable_same_topics(self):
        user_text = self.faker.sentence()

        with mock.patch(
            "pydantic.main.BaseModel.model_validate_json",
            return_value=MagicMock(topics_present=self.allowed_topics),
        ):
            result = self.adapter._azure_llm_callable(user_text, self.allowed_topics)

        assert isinstance(result, ValidationOutcome)
        assert result.raw_llm_output == user_text
        assert result.validated_output == self.allowed_topics[0]
        assert result.validation_passed is True
        assert result.validation_summaries == []

    def test_azure_llm_callable_different_topics(self):
        user_text = self.faker.sentence()
        topics = [self.faker.word() for _ in range(3)]

        with mock.patch(
            "pydantic.main.BaseModel.model_validate_json",
            return_value=MagicMock(topics_present=topics),
        ):
            result = self.adapter._azure_llm_callable(user_text, self.allowed_topics)

        assert isinstance(result, ValidationOutcome)
        assert result.raw_llm_output == user_text
        assert result.validated_output == ""
        assert result.validation_passed is False
        assert result.validation_summaries == []

    def test_azure_llm_callable_exception_raised(self):
        user_text = self.faker.sentence()
        exception = random.choices(
            [KeyError(), PydanticValidationError("Validation error", [])],
        )

        with mock.patch(
            "pydantic.main.BaseModel.model_validate_json", side_effect=exception
        ):
            result = self.adapter._azure_llm_callable(user_text, self.allowed_topics)

        assert isinstance(result, ValidationOutcome)
        assert result.raw_llm_output == user_text
        assert result.validated_output == ""
        assert result.validation_passed is False
        assert result.validation_summaries == []
        self.mock_logger.return_value.exception.assert_called_once_with(
            "Pydantic parsing failed", ANY
        )

    @pytest.mark.asyncio
    async def test_ping_returns_True(self):
        with mock.patch.object(
            self.adapter, "validate_question", return_value=self.faker.word()
        ):
            result = await self.adapter.ping()

        assert result is True

    @pytest.mark.asyncio
    async def test_ping_returns_False(self):
        with mock.patch.object(self.adapter, "validate_question", return_value=None):
            result = await self.adapter.ping()

        assert result is False

    @pytest.mark.asyncio
    async def test_ping_raises_exception(self):
        with (
            mock.patch.object(self.adapter, "validate_question", side_effect=Exception),
            pytest.raises(RuntimeError, match="Guardrails service ping failed: "),
        ):
            await self.adapter.ping()

        self.mock_logger.return_value.exception.assert_any_call(
            "Guardrails service ping failed", ANY
        )
