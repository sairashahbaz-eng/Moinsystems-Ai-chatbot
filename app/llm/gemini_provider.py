from typing import Any
import time

from google import genai

from app.core.config import settings
from app.llm.base import LLMProvider


class GeminiProvider(LLMProvider):

    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

        self.model = settings.llm_model

    def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:

        system_parts = []
        conversation_parts = []

        for message in messages:
            role = message.get("role")
            content = message.get("content", "")

            if role == "system":
                system_parts.append(content)

            elif role == "user":
                conversation_parts.append(
                    f"User: {content}"
                )

            elif role == "assistant":
                conversation_parts.append(
                    f"Assistant: {content}"
                )

        system_instruction = "\n\n".join(system_parts)

        conversation = "\n\n".join(
            conversation_parts
        )

        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=conversation,
                    config={
                        "system_instruction": system_instruction,
                    },
                )

                if not response.text:
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                return response.text.strip()

            except Exception as exc:
                if attempt == max_attempts - 1:
                    raise exc

                time.sleep(2 * (attempt + 1))


if __name__ == "__main__":
    print("Gemini provider module OK")