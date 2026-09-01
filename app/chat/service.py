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
        print("CHAT SERVICE: initializing", flush=True)

        self.retriever: RAGRetriever | None = None
        self.provider = GeminiProvider()

        print("CHAT SERVICE: Gemini provider initialized", flush=True)

    def _get_retriever(self) -> RAGRetriever:
        print("CHAT: loading RAG retriever...", flush=True)

        if self.retriever is None:
            self.retriever = RAGRetriever()

        print("CHAT: RAG retriever ready", flush=True)

        return self.retriever

    def chat(
        self,
        db: Session,
        session_id: int,
        message: str,
        recent_messages: list[dict[str, str]] | None = None,
        lead_state: str | None = None,
    ) -> dict[str, Any]:

        print("CHAT 1: entered chat service", flush=True)

        # 1. Load existing lead
        print("CHAT 2: loading lead from database...", flush=True)

        lead = (
            db.query(LeadSubmission)
            .filter(
                LeadSubmission.session_id == session_id
            )
            .first()
        )

        print("CHAT 3: lead database query complete", flush=True)

        # 2. Determine current lead state
        if lead is not None:
            lead_data = {
                "full_name": lead.full_name,
                "email": lead.email,
                "contact_number": lead.contact_number,
            }

            current_state = get_next_state(lead_data)
            lead_state = current_state.value

        print(
            f"CHAT 4: lead state = {lead_state}",
            flush=True,
        )

        # 3. Classify intent
        print("CHAT 5: classifying intent...", flush=True)

        intent = classify_intent(message)

        print(
            f"CHAT 6: intent = {intent.value}",
            flush=True,
        )

        # 4. If lead capture is active, save expected field
        if lead is not None and lead_state != "complete":

            if lead_state == "ask_name":
                lead.full_name = message.strip()

            elif lead_state == "ask_email":
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

            lead_data = {
                "full_name": lead.full_name,
                "email": lead.email,
                "contact_number": lead.contact_number,
            }

            lead_state = get_next_state(lead_data).value

        # 5. Save visitor message
        print("CHAT 7: saving visitor message...", flush=True)

        visitor_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=message,
            intent=intent.value,
            state=lead_state,
        )

        db.add(visitor_message)
        db.flush()

        print("CHAT 8: visitor message saved", flush=True)

        # 6. Load RAG retriever
        print("CHAT 9: before RAG retriever", flush=True)

        retriever = self._get_retriever()

        print("CHAT 10: RAG retriever loaded", flush=True)

        # 7. Retrieve relevant knowledge
        print("CHAT 11: starting RAG retrieval...", flush=True)

        results = retriever.retrieve(
            query=message,
            conversation_context=self._conversation_context(
                recent_messages
            ),
        )

        print(
            f"CHAT 12: RAG retrieval complete, results={len(results)}",
            flush=True,
        )

        # 8. Build context
        print("CHAT 13: building RAG context...", flush=True)

        rag_context = build_context(results)

        print("CHAT 14: RAG context built", flush=True)

        # 9. Build prompt
        print("CHAT 15: building Gemini messages...", flush=True)

        messages = build_messages(
            user_query=message,
            rag_context=rag_context,
            recent_messages=recent_messages,
            intent=intent.value,
            lead_state=lead_state,
        )

        print(
            f"CHAT 16: Gemini messages built, count={len(messages)}",
            flush=True,
        )

        # 10. Generate response
        print("CHAT 17: BEFORE GEMINI GENERATION", flush=True)

        answer = self.provider.generate(messages)

        print("CHAT 18: GEMINI GENERATION COMPLETE", flush=True)

        if not answer:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        # 11. Start lead capture for commercial/high-intent conversations
        if intent.value in {
            "pricing_quote",
            "high_buying_intent",
        }:

            print(
                "CHAT 19: commercial/high-intent flow",
                flush=True,
            )

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

        # 12. Save assistant message
        print("CHAT 20: saving assistant message", flush=True)

        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=answer,
            intent=intent.value,
            state=lead_state,
        )

        db.add(assistant_message)

        # 13. Commit
        print("CHAT 21: committing database transaction", flush=True)

        db.commit()

        print("CHAT 22: CHAT COMPLETE", flush=True)

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