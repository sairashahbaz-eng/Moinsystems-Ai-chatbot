from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not configured."
            )

        self.client = OpenAI(
            api_key=settings.openai_api_key
        )

    def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:

        response = self.client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=kwargs.get(
                "temperature",
                0.2,
            ),
        )

        return response.choices[0].message.content or ""