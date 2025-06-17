import logging
import uuid
from typing import List

from guardrails import AsyncGuard, ValidationOutcome
from guardrails.errors import ValidationError
from guardrails.hub import RestrictToTopic
from openai import AzureOpenAI
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.domain.ports.guardrail_port import GuardrailInterface

logger = logging.getLogger(__name__)


class TopicClassification(BaseModel):
    topics_present: List[str]


class GuardrailAdapter(GuardrailInterface):
    """Async-optimized GuardrailAdapter for validating user questions with concurrent execution capabilities."""

    def __init__(
        self,
        model_name: str,
        azure_deployment: str,
        azure_endpoint: str,
        api_version: str,
        api_key: str,
        allowed_topics: List[str],
    ) -> None:
        self.client = AzureOpenAI(
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            api_key=api_key,
        )
        self.model_name = model_name
        self.allowed_topics = allowed_topics
        self.guard = AsyncGuard().use(
            RestrictToTopic(
                valid_topics=self.allowed_topics,
                invalid_topics=[],
                llm_callable=self._azure_llm_callable,
                disable_classifier=True,
                disable_llm=False,
                on_fail="noop",
            )
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _azure_llm_callable(self, user_text, valid_topics):
        function_schema = [
            {
                "name": "classify_topics",
                "description": "Classifies which allowed topics are present in the question.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topics_present": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of topics present in the question.",
                        }
                    },
                    "required": ["topics_present"],
                },
            }
        ]

        system_prompt = (
            f"You are an assistant that classifies questions into these topics: {', '.join(valid_topics)}. "
            "Return only the topics from the list that are present in the user's question. "
            "A question is considered on-topic if it refers to insurance, policy details, claims, coverage, premiums, renewals, or any concept related to insurance products or services."
        )

        response = self.client.chat.completions.create(
            model="YOUR_MODEL_NAME",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            functions=function_schema,
            function_call={"name": "classify_topics"},
            temperature=0.0,
            max_tokens=100,
        )

        try:
            function_args = response.choices[0].message.function_call.arguments
            parsed = TopicClassification.model_validate_json(function_args)
            topics = parsed.topics_present
            matching_topic = next((t for t in topics if t in valid_topics), None)
        except (KeyError, PydanticValidationError) as e:
            self.logger.exception("Pydantic parsing failed", e)
            matching_topic = None

        return ValidationOutcome(
            call_id=str(uuid.uuid4()),
            raw_llm_output=user_text,
            validated_output=matching_topic or "",
            validation_passed=bool(matching_topic),
            validation_summaries=[],
            reask=None,
            error=None,
        )

    async def validate_question(self, user_question: str) -> bool:
        try:
            result: ValidationOutcome = await self.guard.validate(user_question)
            self.logger.debug(f"Validation Passed: {result.validation_passed}")
            if not result.validation_passed and result.validation_summaries:
                reason = result.validation_summaries[0].failure_reason
                self.logger.debug(f"Failure Reason: {reason}")
            return result.validation_passed
        except ValidationError as e:
            self.logger.warning(f"Invalid Question: {e}")
            if hasattr(e, "errors"):
                self.logger.warning(f"Error details: {e.errors}")
            return False

    async def ping(self) -> bool:
        """Test the connectivity and functionality of the Guardrails service.

        Returns True if the service validates a test question successfully, otherwise raises an exception.
        """
        try:
            result = await self.validate_question("What is an insurance policy?")
            if result:
                self.logger.info("Guardrails service ping successful.")
                return True
            else:
                self.logger.warning(
                    "Guardrails service ping failed: Test question validation failed."
                )
                return False
        except Exception as e:
            self.logger.exception("Guardrails service ping failed", e)
            raise RuntimeError(f"Guardrails service ping failed: {str(e)}")
