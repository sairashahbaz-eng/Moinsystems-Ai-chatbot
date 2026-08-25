from sqlalchemy import text

from app.db.session import engine


with engine.begin() as connection:
    connection.execute(
        text(
            """
            DELETE FROM knowledge_chunk
            WHERE document_id IN (
                SELECT id
                FROM knowledge_document
                WHERE record_id = :record_id
            )
            """
        ),
        {"record_id": "company_info.txt"},
    )

    connection.execute(
        text(
            """
            DELETE FROM knowledge_document
            WHERE record_id = :record_id
            """
        ),
        {"record_id": "company_info.txt"},
    )

print("Old company_info.txt record and chunks removed.")