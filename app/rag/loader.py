from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.db.session import SessionLocal
from app.db.models import KnowledgeDocument, KnowledgeChunk


print("1. Starting")

with open("data/documents/company_info.txt", "r", encoding="utf-8") as file:
    text = file.read()

print("2. File loaded")


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50
)

texts = text_splitter.split_text(text)

chunks = [
    Document(page_content=text)
    for text in texts
]

print("3. Number of chunks:", len(chunks))


db = SessionLocal()

try:
    document = KnowledgeDocument(
        filename="company_info.txt",
        title="Moinsystems AI Company Information"
    )

    db.add(document)
    db.flush()

    for chunk in chunks:
        knowledge_chunk = KnowledgeChunk(
            document_id=document.id,
            content=chunk.page_content
        )

        db.add(knowledge_chunk)

    db.commit()

    print("4. Knowledge document and chunks saved successfully!")

finally:
    db.close()


for i, chunk in enumerate(chunks):
    print(f"\n--- Chunk {i + 1} ---")
    print(chunk.page_content)

print("5. Done")