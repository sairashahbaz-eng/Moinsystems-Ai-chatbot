"""add knowledge metadata fields

Revision ID: 7325a156b7b0
Revises: cee9a9c2373e
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7325a156b7b0"
down_revision: Union[str, Sequence[str], None] = "cee9a9c2373e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new metadata columns as nullable first
    # so existing records do not cause migration failure.

    op.add_column(
        "knowledge_document",
        sa.Column("record_id", sa.String(length=255), nullable=True),
    )

    op.add_column(
        "knowledge_document",
        sa.Column("category", sa.String(length=255), nullable=True),
    )

    op.add_column(
        "knowledge_document",
        sa.Column("tags", sa.Text(), nullable=True),
    )

    op.add_column(
        "knowledge_document",
        sa.Column("intents", sa.Text(), nullable=True),
    )

    op.add_column(
        "knowledge_document",
        sa.Column("source", sa.String(length=500), nullable=True),
    )

    op.add_column(
        "knowledge_document",
        sa.Column("dataset_version", sa.String(length=100), nullable=True),
    )

    op.add_column(
        "knowledge_document",
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )

    # Populate metadata for the existing knowledge record.
    op.execute(
        """
        UPDATE knowledge_document
        SET
            record_id = filename,
            source = 'MoinSystems_AI_Public_Chatbot_RAG_Dataset_v2.jsonl',
            dataset_version = 'v2'
        WHERE record_id IS NULL
        """
    )

    # Now make required fields non-null.
    op.alter_column(
        "knowledge_document",
        "record_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    op.alter_column(
        "knowledge_document",
        "source",
        existing_type=sa.String(length=500),
        nullable=False,
    )

    op.alter_column(
        "knowledge_document",
        "dataset_version",
        existing_type=sa.String(length=100),
        nullable=False,
    )

    # Stable IDs must be unique.
    op.create_unique_constraint(
        "uq_knowledge_document_record_id",
        "knowledge_document",
        ["record_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_knowledge_document_record_id",
        "knowledge_document",
        type_="unique",
    )

    op.drop_column("knowledge_document", "metadata_json")
    op.drop_column("knowledge_document", "dataset_version")
    op.drop_column("knowledge_document", "source")
    op.drop_column("knowledge_document", "intents")
    op.drop_column("knowledge_document", "tags")
    op.drop_column("knowledge_document", "category")
    op.drop_column("knowledge_document", "record_id")