from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector

from app.core.config import settings


COLLECTION_NAME = "moinsystems_documents"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


print("1. Starting...")

with open(
    "data/documents/company_info.txt",
    "r",
    encoding="utf-8",
) as file:
    text = file.read()

print("2. File loaded")


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50,
)

texts = text_splitter.split_text(text)

documents = [
    Document(
        page_content=chunk,
        metadata={
            "title": "Moinsystems AI Company Information",
            "category": "company",
            "source": "company_info.txt",
            "dataset_version": "v1",
            "record_id": f"company_info_{index}",
        },
    )
    for index, chunk in enumerate(texts)
]

print(
    "3. Number of chunks:",
    len(documents),
)


print("4. Loading embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name=MODEL_NAME,
)

print("5. Connecting to PGVector...")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=settings.database_url,
)

print("6. Adding documents to PGVector...")

vector_store.add_documents(documents)

print("7. Documents embedded and saved successfully!")

for index, document in enumerate(documents):
    print(f"\n--- Chunk {index + 1} ---")
    print(document.page_content)

print("\n8. Done!")