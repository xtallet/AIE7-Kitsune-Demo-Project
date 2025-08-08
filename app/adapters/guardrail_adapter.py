import logging
from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from nltk import PorterStemmer
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TopicClassification(BaseModel):
    topics_present: List[str]


class GuardrailAdapter:
    """Async-optimized GuardrailAdapter for validating user questions with concurrent execution capabilities."""

    def __init__(
        self,
        model_name: str,
        azure_deployment: str,
        azure_endpoint: str,
        api_version: str,
        allowed_topics: List[str],
    ) -> None:
        self.llm = AzureChatOpenAI(
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
        )
        self.model_name = model_name
        self.allowed_topics = allowed_topics
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an assistant that classifies questions into these topics: {allowed_topics}. "
                    "Return only the topics from the list that are present in the user's question. "
                    "A question is considered on-topic if it refers to insurance, policy details, claims, coverage, premiums, renewals, or any concept related to insurance products or services.",
                ),
                (
                    "user",
                    "{question}",
                ),
            ]
        )

    async def validate_question(self, user_question: str) -> bool:
        try:
            chain = self.prompt_template | self.llm
            response = await chain.ainvoke(
                {
                    "allowed_topics": ", ".join(self.allowed_topics),
                    "question": user_question,
                }
            )

            parsed = TopicClassification(topics_present=response.content.split(","))
            topics = parsed.topics_present
            result = has_topic_match(topics, self.allowed_topics)

            logger.info(f"Validation Passed: {result}")
            if not result:
                logger.info(f"No matching topics found. Topics detected: {topics}")

            return result

        except Exception as e:
            logger.warning(f"Topic validation failed: {e}")
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
