import logging
import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.health import router as health_router
from app.api.v1.lead_capture import router as lead_capture_router
from app.api.v1.sessions import router as sessions_router
from app.chat.router import router as chat_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("moinsystems_ai")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
)

app = FastAPI(
    title=os.getenv(
        "APP_NAME",
        "Moinsystems AI Chatbot",
    ),
    debug=os.getenv(
        "DEBUG",
        "false",
    ).lower() == "true",
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)


allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://localhost:5176",
"http://127.0.0.1:5176",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


MAX_REQUEST_SIZE = 10 * 1024


@app.middleware("http")
async def request_size_middleware(
    request: Request,
    call_next,
):
    content_length = request.headers.get("content-length")

    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": "Request body is too large."
                    },
                )
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Invalid Content-Length header."
                },
            )

    return await call_next(request)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    request.state.request_id = request_id

    try:
        response = await call_next(request)

        latency_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_id=%s method=%s path=%s status=%s latency_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            latency_ms,
        )

        return response

    except Exception:
        latency_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        logger.exception(
            "request_id=%s method=%s path=%s latency_ms=%s error=request_failed",
            request_id,
            request.method,
            request.url.path,
            latency_ms,
        )

        raise


app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(lead_capture_router)


@app.get("/")
def root():
    return {
        "name": "Moinsystems AI Chatbot",
        "status": "running",
    }