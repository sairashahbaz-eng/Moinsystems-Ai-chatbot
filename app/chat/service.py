from typing import Any

from app.llm.gemini_provider import GeminiProvider
from app.llm.prompt_builder import build_messages
from app.rag.context_builder import build_context
from app.rag.retriever import RAGRetriever


class ChatService:

    def __init__(self) -> None:
        self.retriever = RAGRetriever()
        self.provider = GeminiProvider()

    def chat(
        self,
        message: str,
        recent_messages: list[dict[str, str]] | None = None,
        intent: str | None = None,
        lead_state: str | None = None,
    ) -> dict[str, Any]:

        # 1. Retrieve relevant knowledge
        results = self.retriever.retrieve(
            query=message,
            conversation_context=self._conversation_context(
                recent_messages
            ),
        )

        # 2. Build deterministic knowledge context
        rag_context = build_context(results)

        # 3. Build prompt
        messages = build_messages(
            user_query=message,
            rag_context=rag_context,
            recent_messages=recent_messages,
            intent=intent,
            lead_state=lead_state,
        )

        # 4. Generate grounded response
        answer = self.provider.generate(messages)

        return {
            "answer": answer,
            "grounded": bool(results),
        }

    @staticmethod
    def _conversation_context(
        recent_messages: list[dict[str, str]] | None,
    ) -> str | None:

        if not recent_messages:
            return None

        recent = recent_messages[-6:]

        return "\n".join(
            f"{msg.get('role', '')}: {msg.get('content', '')}"
            for msg in recent
            if msg.get("content")
        )


chat_service = ChatService()