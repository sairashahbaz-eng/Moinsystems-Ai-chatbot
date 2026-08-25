import json
from pathlib import Path

from sqlalchemy import select

from app.db.models import KnowledgeDocument, KnowledgeChunk
from app.db.session import SessionLocal


DATASET_PATH = Path(
    "data/MoinSystems_AI_Public_Chatbot_RAG_Dataset_v2.jsonl"
)

DATASET_VERSION = "v2"
DATASET_SOURCE = DATASET_PATH.name


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


def load_dataset():
    records = []
    seen_ids = set()

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

            if record_id in seen_ids:
                raise ValueError(
                    f"Duplicate id '{record_id}' "
                    f"at line {line_number}"
                )

            seen_ids.add(record_id)

            content = (
                record.get("content")
                or record.get("text")
            )

            if not content:
                raise ValueError(
                    f"Missing content/text "
                    f"at line {line_number}"
                )

            record["title"] = normalize_text(
                record.get("title", "")
            )

            record["category"] = normalize_text(
                record.get("category", "")
            )

            record["tags"] = normalize_metadata(
                record.get("tags", [])
            )

            record["intents"] = normalize_metadata(
                record.get("intents", [])
            )

            record["metadata"] = normalize_metadata(
                record.get("metadata", {})
            )

            record["content"] = normalize_text(
                content
            )

            record["_dataset_version"] = DATASET_VERSION

            records.append(record)

    return records


def save_to_database(records):
    db = SessionLocal()

    try:
        inserted = 0
        updated = 0

        for record in records:

            existing = db.execute(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.record_id
                    == record["id"]
                )
            ).scalar_one_or_none()

            metadata_json = json.dumps(
                record["metadata"],
                ensure_ascii=False,
            )

            tags_json = json.dumps(
                record["tags"],
                ensure_ascii=False,
            )

            intents_json = json.dumps(
                record["intents"],
                ensure_ascii=False,
            )

            if existing:
                document = existing
                updated += 1

                document.filename = record["id"]
                document.title = record["title"]
                document.category = record["category"]
                document.tags = tags_json
                document.intents = intents_json
                document.source = DATASET_SOURCE
                document.dataset_version = DATASET_VERSION
                document.metadata_json = metadata_json

            else:
                document = KnowledgeDocument(
                    filename=record["id"],
                    title=record["title"],
                    record_id=record["id"],
                    category=record["category"],
                    tags=tags_json,
                    intents=intents_json,
                    source=DATASET_SOURCE,
                    dataset_version=DATASET_VERSION,
                    metadata_json=metadata_json,
                )

                db.add(document)
                db.flush()

                inserted += 1

            existing_chunk = db.execute(
                select(KnowledgeChunk).where(
                    KnowledgeChunk.document_id
                    == document.id
                )
            ).scalar_one_or_none()

            if existing_chunk:
                existing_chunk.content = record["content"]

            else:
                db.add(
                    KnowledgeChunk(
                        document_id=document.id,
                        content=record["content"],
                    )
                )

        db.commit()

        print(f"Inserted documents: {inserted}")
        print(f"Updated documents: {updated}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":

    records = load_dataset()

    print(
        f"Dataset loaded successfully: "
        f"{len(records)} records"
    )

    print(
        f"Dataset version: {DATASET_VERSION}"
    )

    print(
        "Duplicate ID check passed."
    )

    print(
        "Normalization completed successfully."
    )

    save_to_database(records)

    print(
        "Knowledge documents and chunks saved successfully!"
    )