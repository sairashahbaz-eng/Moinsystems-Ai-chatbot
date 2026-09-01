from typing import Any

from sqlalchemy.orm import Session

from app.chat.intent_router import classify_intent
from app.db.models import ChatMessage, LeadSubmission
from app.leads.state_machine import get_next_state
from app.llm.gemini_provider import GeminiProvider
from app.llm.prompt_builder import build_messages
from app.rag.context_builder import build_context
from app.rag.retriever import RAGRetriever


class ChatService:

    def __init__(self) -> None:
        # Lazy-load the RAG retriever.
        # This prevents the HuggingFace embedding model
        # from loading during application startup.
        self.retriever: RAGRetriever | None = None
        self.provider = GeminiProvider()

    def _get_retriever(self) -> RAGRetriever:
        if self.retriever is None:
            self.retriever = RAGRetriever()

        return self.retriever

    def chat(
        self,
        db: Session,
        session_id: int,
        message: str,
        recent_messages: list[dict[str, str]] | None = None,
        lead_state: str | None = None,
    ) -> dict[str, Any]:

        # 1. Load existing lead for this session
        lead = (
            db.query(LeadSubmission)
            .filter(
                LeadSubmission.session_id == session_id
            )
            .first()
        )

        # 2. Determine current lead state
        if lead is not None:
            lead_data = {
                "full_name": lead.full_name,
                "email": lead.email,
                "contact_number": lead.contact_number,
            }

            current_state = get_next_state(lead_data)
            lead_state = current_state.value

        # 3. Classify intent on the server
        intent = classify_intent(message)

        # 4. If lead capture is active, save the expected field
        if lead is not None and lead_state != "complete":

            if lead_state == "ask_name":
                lead.full_name = message.strip()

            elif lead_state == "ask_email":
                # Only save if this looks like an email.
                # Otherwise treat it as a normal user question.
                if "@" in message and "." in message:
                    lead.email = message.strip()

            elif lead_state == "ask_phone":
                cleaned_phone = (
                    message.replace(" ", "")
                    .replace("-", "")
                    .replace("(", "")
                    .replace(")", "")
                )

                if cleaned_phone.isdigit():
                    lead.contact_number = message.strip()

            # Recalculate state after possible field update
            lead_data = {
                "full_name": lead.full_name,
                "email": lead.email,
                "contact_number": lead.contact_number,
            }

            lead_state = get_next_state(lead_data).value

        # 5. Save visitor message
        visitor_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=message,
            intent=intent.value,
            state=lead_state,
        )

        db.add(visitor_message)
        db.flush()

        # 6. Retrieve relevant knowledge
        retriever = self._get_retriever()

        results = retriever.retrieve(
            query=message,
            conversation_context=self._conversation_context(
                recent_messages
            ),
        )

        # 7. Build deterministic knowledge context
        rag_context = build_context(results)

        # 8. Build prompt
        messages = build_messages(
            user_query=message,
            rag_context=rag_context,
            recent_messages=recent_messages,
            intent=intent.value,
            lead_state=lead_state,
        )

        # 9. Generate grounded response
        answer = self.provider.generate(messages)

        # 10. Start lead capture for commercial/high-intent conversations
        if intent.value in {
            "pricing_quote",
            "high_buying_intent",
        }:

            if lead is None:
                lead = LeadSubmission(
                    session_id=session_id,
                    full_name="",
                    email="",
                    contact_number="",
                )

                db.add(lead)
                db.flush()

            lead_data = {
                "full_name": lead.full_name,
                "email": lead.email,
                "contact_number": lead.contact_number,
            }

            lead_state = get_next_state(lead_data).value

        # 11. Save assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=answer,
            intent=intent.value,
            state=lead_state,
        )

        db.add(assistant_message)

        # 12. Save everything
        db.commit()

        return {
            "answer": answer,
            "grounded": bool(results),
            "intent": intent.value,
            "lead_state": lead_state,
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