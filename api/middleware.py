"""FastAPI middleware for the Second Brain API."""

import logging
import time

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def add_process_time_header(request: Request, call_next):
    """Middleware that adds an X-Process-Time header to every response."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}"
    return response


async def error_handler(request: Request, exc: Exception):
    """Global exception handler — logs the error and returns a generic JSON 500."""
    logger.error("Unhandled exception for %s %s: %s", request.method, request.url, exc, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
