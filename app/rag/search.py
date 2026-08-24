from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector

from app.core.config import settings


embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


vector_store = PGVector(
    embeddings=embeddings,
    collection_name="moinsystems_documents",
    connection=settings.database_url,
)


def retrieve_context(query: str, k: int = 3) -> str:
    results = vector_store.similarity_search(
        query,
        k=k
    )

    if not results:
        return "No relevant information was found in the knowledge base."

    context = "\n\n".join(
        result.page_content
        for result in results
    )

    return context


if __name__ == "__main__":
    query = "What is Moinsystems AI?"

    context = retrieve_context(query)

    print("\nFound relevant chunks:\n")
    print(context)