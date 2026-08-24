from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector

from app.rag.loader import chunks
from app.core.config import settings


embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


vector_store = PGVector.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="moinsystems_documents",
    connection=settings.database_url,
)


print("PostgreSQL vector database created successfully!")
print(f"Number of chunks stored: {len(chunks)}")