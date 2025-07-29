import logging
from typing import List

from nltk import PorterStemmer
from openai import AsyncAzureOpenAI
from pydantic import BaseModel

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
        self.client = AsyncAzureOpenAI(
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            api_key=api_key,
        )
        self.model_name = model_name
        self.allowed_topics = allowed_topics
        self.logger = logging.getLogger(self.__class__.__name__)

    async def validate_question(self, user_question: str) -> bool:
        try:
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
                f"You are an assistant that classifies questions into these topics: {', '.join(self.allowed_topics)}. "
                "Return only the topics from the list that are present in the user's question. "
                "A question is considered on-topic if it refers to insurance, policy details, claims, coverage, premiums, renewals, or any concept related to insurance products or services."
            )

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question},
                ],
                functions=function_schema,
                function_call={"name": "classify_topics"},
                temperature=0.0,
                max_tokens=100,
            )

            function_args = response.choices[0].message.function_call.arguments
            parsed = TopicClassification.model_validate_json(function_args)
            topics = parsed.topics_present
            result = has_topic_match(topics, self.allowed_topics)

            self.logger.debug(f"Validation Passed: {result}")
            if not result:
                self.logger.debug(
                    f"No matching topics found. Topics detected: {topics}"
                )

            return result

        except Exception as e:
            self.logger.warning(f"Topic validation failed: {e}")
            return False


def has_topic_match(detected_topics, allowed_topics):
    """Check if any detected topic matches the allowed topics using stemming."""
    stemmer = PorterStemmer()
    stemmed_allowed = [stemmer.stem(topic) for topic in allowed_topics]

    for detected in detected_topics:
        # Try exact match after stemming
        stemmed_detected = stemmer.stem(detected)
        if stemmed_detected in stemmed_allowed:
            return True

        # Try matching individual words in compound phrases
        words = detected.lower().split()
        for word in words:
            stemmed_word = stemmer.stem(word)
            for allowed in allowed_topics:
                allowed_lower = allowed.lower()
                # Check if the stemmed word matches any allowed topic stem
                if stemmed_word == stemmer.stem(allowed_lower):
                    return True
                # Check if word is part of any allowed topic
                if stemmed_word in allowed_lower or allowed_lower in stemmed_word:
                    return True

    return False
