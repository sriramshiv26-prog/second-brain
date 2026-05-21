"""Global constants for the Second Brain system."""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

SECOND_BRAIN_DATA_DIR = Path(
    os.environ.get("SECOND_BRAIN_DATA_DIR", "~/second-brain-data")
).expanduser()

SOURCES_DIR = SECOND_BRAIN_DATA_DIR / "sources"
GRAPH_DB_PATH = Path(
    os.environ.get("GRAPH_DB_PATH", str(SECOND_BRAIN_DATA_DIR / "graph.db"))
).expanduser()
CHROMA_DB_PATH = Path(
    os.environ.get("CHROMA_DB_PATH", str(SECOND_BRAIN_DATA_DIR / "vectors"))
).expanduser()
ENTITIES_DIR = SECOND_BRAIN_DATA_DIR / "entities"

# Ensure directories exist on import
for _dir in (SECOND_BRAIN_DATA_DIR, SOURCES_DIR, CHROMA_DB_PATH, ENTITIES_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# MODELS
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL_ENTITY = os.environ.get("OLLAMA_MODEL_ENTITY", "qwen2.5-coder")
OLLAMA_MODEL_INTENT = os.environ.get("OLLAMA_MODEL_INTENT", "mistral")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text-v1.5")

# ---------------------------------------------------------------------------
# INGESTION
# ---------------------------------------------------------------------------

MAX_FILE_SIZE_MB = 100
SUPPORTED_FORMATS = {"pdf", "docx", "xlsx", "txt", "md", "json", "html", "csv"}
VOICE_FORMATS = {"mp3", "wav", "m4a", "ogg", "flac"}

# ---------------------------------------------------------------------------
# EMBEDDING
# ---------------------------------------------------------------------------

EMBEDDING_DIMENSION = 768
EMBEDDING_BATCH_SIZE = 32

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", 5000))
API_WORKERS = int(os.environ.get("API_WORKERS", 1))

# ---------------------------------------------------------------------------
# KNOWLEDGE GRAPH
# ---------------------------------------------------------------------------

ENTITY_TYPES = {"person", "concept", "organization", "project", "location"}
RELATIONSHIP_TYPES = {"mentions", "cites", "relates_to", "authored_by", "tags"}
