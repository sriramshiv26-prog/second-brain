"""Second Brain FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from api.middleware import add_process_time_header, error_handler
from api.routes.health import router as health_router
from config.chroma_config import init_chroma
from storage.graph_db import init_graph_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Second Brain API", version="0.1.0")

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(add_process_time_header)
app.exception_handler(Exception)(error_handler)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(health_router)

# ---------------------------------------------------------------------------
# Lifecycle events
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def startup():
    """Initialize databases on server startup."""
    logger.info("Starting Second Brain API — initialising databases...")
    init_graph_db()
    init_chroma()
    logger.info("Databases ready.")


@app.on_event("shutdown")
async def shutdown():
    """Log clean shutdown."""
    logger.info("Second Brain API shutting down.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    from config.constants import API_HOST, API_PORT

    uvicorn.run(
        "api.server:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        workers=1,
    )
