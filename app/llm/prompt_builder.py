from typing import Any

from app.llm.prompts import SYSTEM_PROMPT


MAX_RECENT_MESSAGES = 6


def build_messages(
    user_query: str,
    rag_context: str = "",
    recent_messages: list[dict[str, str]] | None = None,
    intent: str | None = None,
    lead_state: str | None = None,
) -> list[dict[str, str]]:

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    # Only recent conversation is sent to the LLM.
    if recent_messages:
        for message in recent_messages[-MAX_RECENT_MESSAGES:]:
            role = message.get("role")
            content = message.get("content")

            if role in {"user", "assistant"} and content:
                messages.append(
                    {
                        "role": role,
                        "content": content,
                    }
                )

    # Internal state is provided separately from user-visible content.
    state_parts: list[str] = []

    if intent:
        state_parts.append(
            f"Current intent: {intent}"
        )

    if lead_state:
        state_parts.append(
            f"Current lead state: {lead_state}"
        )

    if state_parts:
        messages.append(
            {
                "role": "system",
                "content": (
                    "Application state:\n"
                    + "\n".join(state_parts)
                ),
            }
        )

    # Only retrieved RAG context enters the knowledge layer.
    if rag_context:
        messages.append(
            {
                "role": "system",
                "content": (
                    "Retrieved knowledge context:\n"
                    "<knowledge>\n"
                    f"{rag_context}\n"
                    "</knowledge>\n\n"
                    "Use this knowledge only as factual "
                    "support for the visitor's question."
                ),
            }
        )

    messages.append(
        {
            "role": "user",
            "content": user_query,
        }
    )

    return messages


if __name__ == "__main__":

    test_messages = build_messages(
        user_query="Do you provide SaaS development?",
        rag_context=(
            "Title: SaaS Development\n"
            "Category: service\n"
            "Content: MoinSystems AI provides SaaS development."
        ),
        recent_messages=[
            {
                "role": "user",
                "content": "What services do you provide?",
            },
            {
                "role": "assistant",
                "content": "We provide software development services.",
            },
        ],
        intent="service_discovery",
        lead_state="none",
    )

    for message in test_messages:
        print(
            f"\n[{message['role']}]\n"
            f"{message['content']}"
        )