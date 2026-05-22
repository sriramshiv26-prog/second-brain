"""Second Brain FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from api.middleware import add_process_time_header, error_handler
from api.routes.health import router as health_router
from api.routes.search import router as search_router
from api.routes.graph import router as graph_router
from api.routes.auth import router as auth_router
from api.routes.filters import router as filters_router
from api.routes.citations import router as citations_router
from api.routes.documents import router as documents_router
from api.routes.ws import router as ws_router
from api.auth.models import init_auth_db
from config.chroma_config import init_chroma
from storage.graph_db import init_graph_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage FastAPI application lifecycle."""
    # Startup
    logger.info("Starting Second Brain API — initialising databases...")
    init_graph_db()
    init_chroma()
    init_auth_db()
    logger.info("Databases ready.")

    yield

    # Shutdown
    logger.info("Second Brain API shutting down.")


app = FastAPI(title="Second Brain API", version="0.1.0", lifespan=lifespan)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.middleware("http")(add_process_time_header)
app.exception_handler(Exception)(error_handler)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(health_router)
app.include_router(search_router)
app.include_router(graph_router)
app.include_router(auth_router)
app.include_router(filters_router)
app.include_router(citations_router)
app.include_router(documents_router)
app.include_router(ws_router)

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
