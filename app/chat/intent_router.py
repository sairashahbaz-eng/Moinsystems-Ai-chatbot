from enum import Enum


class Intent(str, Enum):
    NORMAL_QUERY = "normal_query"
    SERVICE_PROJECT_INQUIRY = "service_project_inquiry"
    PRICING_QUOTE = "pricing_quote"
    HIGH_BUYING_INTENT = "high_buying_intent"
    FALLBACK = "fallback"


def classify_intent(message: str) -> Intent:
    text = message.lower().strip()

    if not text:
        return Intent.FALLBACK

    pricing_keywords = [
        "price",
        "pricing",
        "cost",
        "quote",
        "quotation",
        "budget",
        "how much",
        "rate",
        "charges",
    ]

    high_buying_keywords = [
        "hire",
        "book",
        "start project",
        "get started",
        "let's start",
        "want to build",
        "need a developer",
        "need developers",
        "work with you",
        "contact your team",
    ]

    service_keywords = [
        "service",
        "services",
        "website",
        "web app",
        "web application",
        "mobile app",
        "mobile application",
        "saas",
        "software development",
        "ai solution",
        "chatbot",
        "automation",
        "ecommerce",
        "api",
        "cloud",
        "devops",
        "ui/ux",
        "data solution",
        "project",
        "development",
    ]

    if any(keyword in text for keyword in high_buying_keywords):
        return Intent.HIGH_BUYING_INTENT

    if any(keyword in text for keyword in pricing_keywords):
        return Intent.PRICING_QUOTE

    if any(keyword in text for keyword in service_keywords):
        return Intent.SERVICE_PROJECT_INQUIRY

    normal_keywords = [
        "what",
        "who",
        "how",
        "where",
        "when",
        "can you",
        "do you",
        "tell me",
    ]

    if any(keyword in text for keyword in normal_keywords):
        return Intent.NORMAL_QUERY

    return Intent.FALLBACK