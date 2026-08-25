import json
from pathlib import Path

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector

from app.core.config import settings


DATASET_PATH = Path(
    "data/MoinSystems_AI_Public_Chatbot_RAG_Dataset_v2.jsonl"
)

COLLECTION_NAME = "moinsystems_documents"
DATASET_VERSION = "v2"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def normalize_text(value):
    if not isinstance(value, str):
        return value

    return " ".join(value.split())


def normalize_metadata(value):
    if isinstance(value, list):
        return [
            normalize_text(str(item))
            for item in value
        ]

    if isinstance(value, dict):
        return {
            str(key): normalize_metadata(item)
            for key, item in value.items()
        }

    if isinstance(value, str):
        return normalize_text(value)

    return value


def load_documents():
    documents = []
    record_ids = set()

    with DATASET_PATH.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1
        ):
            if not line.strip():
                continue

            record = json.loads(line)

            record_id = record.get("id")

            if not record_id:
                raise ValueError(
                    f"Missing id at line {line_number}"
                )

            if record_id in record_ids:
                raise ValueError(
                    f"Duplicate record ID: {record_id}"
                )

            record_ids.add(record_id)

            content = (
                record.get("content")
                or record.get("text")
            )

            if not content:
                raise ValueError(
                    f"Missing content/text for {record_id}"
                )

            metadata = {
                "record_id": record_id,
                "title": normalize_text(
                    record.get("title", "")
                ),
                "category": normalize_text(
                    record.get("category", "")
                ),
                "tags": normalize_metadata(
                    record.get("tags", [])
                ),
                "intents": normalize_metadata(
                    record.get("intents", [])
                ),
                "source": (
                    "MoinSystems_AI_Public_Chatbot_RAG_Dataset_v2.jsonl"
                ),
                "dataset_version": DATASET_VERSION,
                "metadata": normalize_metadata(
                    record.get("metadata", {})
                ),
            }

            documents.append(
                Document(
                    page_content=normalize_text(content),
                    metadata=metadata,
                )
            )

    return documents


def create_vector_store(embeddings):
    return PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=settings.database_url,
    )


if __name__ == "__main__":

    print("1. Starting vector ingestion")

    documents = load_documents()

    print(
        f"2. Dataset records loaded: {len(documents)}"
    )

    ids = [
        document.metadata["record_id"]
        for document in documents
    ]

    print(
        f"3. Unique record IDs: {len(set(ids))}"
    )

    if len(ids) != len(set(ids)):
        raise ValueError(
            "Duplicate record IDs detected."
        )

    print("4. Duplicate ID check passed.")

    print("Loading embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name=MODEL_NAME
    )

    print("Embedding model loaded.")

    vector_store = create_vector_store(embeddings)

    print("5. Removing old vector collection...")

    try:
        vector_store.delete_collection()
        print("Old vector collection removed.")
    except Exception:
        print("No previous collection found.")

    # IMPORTANT:
    # Create a fresh PGVector instance after deleting
    # the old collection.
    vector_store = create_vector_store(embeddings)

    print("6. Generating embeddings and storing vectors...")

    vector_store.add_documents(
        documents=documents,
        ids=ids,
    )

    print("7. Vector indexing completed successfully!")

    print(
        f"Indexed vectors: {len(documents)}"
    )

    print(
        f"Dataset version: {DATASET_VERSION}"
    )