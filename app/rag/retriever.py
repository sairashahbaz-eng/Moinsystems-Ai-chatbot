from typing import Any

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector

from app.core.config import settings


COLLECTION_NAME = "moinsystems_documents"
MODEL_NAME = "./models/all-MiniLM-L6-v2"


OUT_OF_SCOPE_TERMS = [
    "quantum computing",
    "quantum computer",
    "quantum physics",
    "weather",
    "temperature",
    "stock market",
    "bitcoin",
    "cryptocurrency",
    "football",
    "cricket",
    "politics",
    "recipe",
    "movie",
    "song",
    "celebrity",
    "astronomy",
]


class RAGRetriever:

    def __init__(
        self,
        top_k: int | None = None,
        threshold: float | None = None,
    ):
        self.top_k = (
            top_k
            if top_k is not None
            else settings.rag_top_k
        )

        self.threshold = (
            threshold
            if threshold is not None
            else settings.rag_score_threshold
        )

        print(
            "RAG 1: Loading embedding model...",
            flush=True,
        )

        self.embeddings = HuggingFaceEmbeddings(
            model_name=MODEL_NAME,
            model_kwargs={
                "device": "cpu",
            },
            encode_kwargs={
                "normalize_embeddings": True,
            },
        )

        print(
            "RAG 2: Embedding model loaded",
            flush=True,
        )

        print(
            "RAG 3: Connecting to PGVector...",
            flush=True,
        )

        self.vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name=COLLECTION_NAME,
            connection=settings.database_url,
            use_jsonb=True,
            engine_args={
                "pool_pre_ping": True,
                "pool_recycle": 300,
                "pool_size": 5,
                "max_overflow": 2,
            },
        )

        print(
            "RAG 4: PGVector connected",
            flush=True,
        )

    @staticmethod
    def normalize_query(query: str) -> str:
        return " ".join(query.strip().split())

    @staticmethod
    def is_follow_up_query(query: str) -> bool:
        query_lower = query.lower().strip()

        follow_up_phrases = [
            "that service",
            "this service",
            "that product",
            "this product",
            "that solution",
            "this solution",
            "tell me more",
            "more about that",
            "more about this",
            "what about that",
            "what about this",
            "how does it work",
            "how does that work",
            "how does this work",
            "can you explain that",
            "can you explain this",
        ]

        return any(
            phrase in query_lower
            for phrase in follow_up_phrases
        )

    @staticmethod
    def is_obviously_out_of_scope(query: str) -> bool:
        query_lower = query.lower()

        return any(
            term in query_lower
            for term in OUT_OF_SCOPE_TERMS
        )

    @staticmethod
    def detect_topic(query: str) -> str | None:
        query_lower = query.lower()

        topic_keywords = {
            "pricing": [
                "price",
                "pricing",
                "cost",
                "quote",
                "quotation",
                "budget",
                "how much",
                "rate",
                "charges",
            ],
            "backend": [
                "backend",
                "api",
                "authentication",
                "authorization",
                "database",
                "webhook",
            ],
            "saas": [
                "saas",
                "subscription",
                "billing",
                "multi-tenant",
                "multitenancy",
            ],
            "ai": [
                "ai",
                "artificial intelligence",
                "ai agent",
                "chatbot",
                "voice ai",
                "machine learning",
            ],
            "web": [
                "website",
                "web app",
                "web application",
                "frontend",
                "web development",
            ],
            "mobile": [
                "mobile",
                "android",
                "ios",
                "mobile app",
                "mobile application",
            ],
            "company": [
                "moinsystems",
                "company",
                "services",
                "software house",
                "what do you do",
            ],
        }

        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return topic

        return None

    @staticmethod
    def topic_matches_document(
        topic: str | None,
        metadata: dict,
        content: str,
    ) -> bool:

        if not topic:
            return True

        text = (
            content.lower()
            + " "
            + str(metadata.get("title", "")).lower()
            + " "
            + str(metadata.get("category", "")).lower()
        )

        topic_keywords = {
            "pricing": [
                "pricing",
                "price",
                "quote",
                "cost",
                "budget",
            ],
            "backend": [
                "backend",
                "api",
                "authentication",
                "database",
                "webhook",
            ],
            "saas": [
                "saas",
                "subscription",
                "billing",
                "multi-tenancy",
            ],
            "ai": [
                "ai",
                "artificial intelligence",
                "chatbot",
                "agent",
            ],
            "web": [
                "web",
                "website",
                "frontend",
            ],
            "mobile": [
                "mobile",
                "android",
                "ios",
            ],
            "company": [
                "company",
                "software house",
                "services",
                "moinsystems",
            ],
        }

        keywords = topic_keywords.get(topic, [])

        return any(
            keyword in text
            for keyword in keywords
        )

    def prepare_query(
        self,
        query: str,
        conversation_context: str | None = None,
    ) -> str:

        query = self.normalize_query(query)

        if not query:
            return ""

        if (
            conversation_context
            and self.is_follow_up_query(query)
        ):
            context = self.normalize_query(
                conversation_context
            )

            return f"{context} {query}"

        return query

    def retrieve(
        self,
        query: str,
        category: str | None = None,
        intent: str | None = None,
        conversation_context: str | None = None,
    ) -> list[dict[str, Any]]:

        query = self.normalize_query(query)

        if not query:
            print(
                "Empty query. No retrieval performed.",
                flush=True,
            )
            return []

        if self.is_obviously_out_of_scope(query):
            print(
                "Query classified as out-of-scope.",
                flush=True,
            )
            print(
                "No retrieval performed.",
                flush=True,
            )
            return []

        retrieval_query = self.prepare_query(
            query=query,
            conversation_context=conversation_context,
        )

        if not retrieval_query:
            return []

        topic = self.detect_topic(query)

        print(
            f"Retrieval query: {retrieval_query}",
            flush=True,
        )
        print(
            f"Detected topic: {topic}",
            flush=True,
        )
        print(
            f"Top-k: {self.top_k}",
            flush=True,
        )
        print(
            f"Threshold: {self.threshold}",
            flush=True,
        )
        print(
            "Retrieval trace:",
            flush=True,
        )

        try:
            results = (
                self.vector_store
                .similarity_search_with_score(
                    retrieval_query,
                    k=self.top_k,
                )
            )

        except Exception as exc:
            print(
                "RAG retrieval failed:",
                flush=True,
            )
            print(
                repr(exc),
                flush=True,
            )
            return []

        retrieved = []
        seen_content = set()

        for document, score in results:

            similarity = 1.0 - float(score)

            metadata = document.metadata or {}

            record_id = metadata.get("record_id")

            print(
                f"ID={record_id} "
                f"Score={similarity:.4f}",
                flush=True,
            )

            if similarity < self.threshold:
                continue

            if category:
                if metadata.get("category") != category:
                    continue

            if intent:
                intents = metadata.get("intents", [])

                if isinstance(intents, str):
                    intents = [intents]

                if intent not in intents:
                    continue

            if topic:
                if not self.topic_matches_document(
                    topic,
                    metadata,
                    document.page_content,
                ):
                    continue

            content_key = " ".join(
                document.page_content.lower().split()
            )

            if content_key in seen_content:
                continue

            seen_content.add(content_key)

            retrieved.append(
                {
                    "record_id": record_id,
                    "title": metadata.get("title"),
                    "category": metadata.get("category"),
                    "content": document.page_content,
                    "tags": metadata.get("tags"),
                    "intents": metadata.get("intents"),
                    "source": metadata.get("source"),
                    "dataset_version": metadata.get(
                        "dataset_version"
                    ),
                    "score": similarity,
                }
            )

        return retrieved


if __name__ == "__main__":

    print(
        "Starting RAG retriever test...",
        flush=True,
    )

    retriever = RAGRetriever()

    print(
        f"Configured top-k: {retriever.top_k}",
        flush=True,
    )

    print(
        f"Configured threshold: {retriever.threshold}",
        flush=True,
    )

    print(
        "Multi-turn retrieval test",
        flush=True,
    )

    query = input(
        "Enter follow-up query: "
    )

    conversation_context = (
        "User: What services does MoinSystems AI provide? "
        "Assistant: MoinSystems AI provides software "
        "development, SaaS, AI, web/mobile, APIs and "
        "integrations."
    )

    prepared_context = retriever.prepare_query(
        query=query,
        conversation_context=conversation_context,
    )

    print(
        "Prepared retrieval context:",
        flush=True,
    )

    print(
        prepared_context,
        flush=True,
    )

    results = retriever.retrieve(
        query=query,
        conversation_context=conversation_context,
    )

    print(
        "Retrieved results:",
        flush=True,
    )

    if not results:
        print(
            "No relevant context found.",
            flush=True,
        )

    else:
        for index, result in enumerate(
            results,
            start=1,
        ):

            print(
                f"--- Result {index} ---",
                flush=True,
            )

            print(
                f"Record ID: {result['record_id']}",
                flush=True,
            )

            print(
                f"Title: {result['title']}",
                flush=True,
            )

            print(
                f"Category: {result['category']}",
                flush=True,
            )

            print(
                f"Score: {result['score']:.4f}",
                flush=True,
            )

            print(
                f"Content: {result['content']}",
                flush=True,
            )