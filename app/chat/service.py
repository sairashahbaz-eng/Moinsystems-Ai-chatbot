from google import genai

from app.core.config import settings
from app.rag.search import retrieve_context


client = genai.Client(
    api_key=settings.gemini_api_key
)


def ask_chatbot(question: str) -> str:
    context = retrieve_context(question)

    prompt = f"""
You are Moinsystems AI, an AI-powered company chatbot.

Answer the user's question using the provided knowledge base.

Rules:
- Use the knowledge base as your primary source.
- Do not invent company information.
- If the answer is not available in the knowledge base, say so.
- Keep the answer clear and concise.

Knowledge Base:
{context}

User Question:
{question}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    return response.text