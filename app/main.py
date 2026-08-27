from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.lead_capture import router as lead_capture_router
from app.chat.router import router as chat_router


app = FastAPI(
    title="MoinSystems AI Chatbot",
    version="0.1.0",
)


app.include_router(
    health_router,
    prefix="/api/v1",
)


app.include_router(
    sessions_router,
)


app.include_router(
    lead_capture_router,
)


app.include_router(
    chat_router,
)


@app.get("/")
def root():
    return {
        "message": "MoinSystems AI Chatbot API"
    }