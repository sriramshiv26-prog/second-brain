"""API documentation generation endpoints."""

import json
from datetime import datetime
from typing import Dict, List, Any

from fastapi import APIRouter

router = APIRouter(prefix="/docs", tags=["documentation"])


def generate_markdown_docs() -> str:
    """Generate markdown documentation for all API endpoints."""
    docs = """# Second Brain API Documentation

Generated: {timestamp}

## Table of Contents
- [Authentication](#authentication)
- [Search](#search)
- [Graph](#graph)
- [Filters](#filters)
- [Citations](#citations)
- [Documents](#documents)
- [WebSocket](#websocket)

## Authentication

### Register User
```http
POST /auth/register
Content-Type: application/json

{{
  "email": "user@example.com",
  "username": "username",
  "password": "securepassword"
}}

Response 200:
{{
  "id": "uuid",
  "email": "user@example.com",
  "username": "username",
  "created_at": "2026-05-24T...",
  "updated_at": "2026-05-24T..."
}}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{{
  "username": "username",
  "password": "password"
}}

Response 200:
{{
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "token_type": "bearer",
  "expires_in": 1800
}}
```

### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{{
  "refresh_token": "refresh_token"
}}

Response 200: {{access_token, refresh_token, ...}}
```

## Search

### Semantic Search
```http
POST /search/
Content-Type: application/json

{{
  "query": "search terms",
  "top_k": 10,
  "include_metadata": true
}}

Response 200:
{{
  "query": "search terms",
  "results": [
    {{
      "doc_id": "id",
      "title": "Document Title",
      "excerpt": "...",
      "relevance_score": 0.95,
      "source_type": "web"
    }}
  ],
  "total_results": 42,
  "execution_time_ms": 123.45
}}
```

### Advanced Search
```http
POST /search/advanced
Content-Type: application/json

{{
  "query": "terms",
  "top_k": 10,
  "filters": {{"source_type": "pdf"}},
  "facets": true,
  "sort_by": "relevance"
}}
```

## Graph

### Get Entity Detail
```http
POST /graph/entity?entity_id=entity_id
Response: {{id, name, type, definition, mention_count, relationships, documents}}
```

### Traverse Graph
```http
POST /graph/traverse?entity_id=entity_id&depth=2&relationship_type=mentions
Response: {{root_entity_id, nodes, edges, depth, node_count, edge_count}}
```

### Get Visualization
```http
GET /viz/entity/entity_id
Response: {{nodes, edges, center_id, node_count, edge_count}}
```

## Filters

### Filter Entities
```http
POST /filters/entities
Content-Type: application/json

{{
  "entity_types": ["Person", "Organization"],
  "mention_count_min": 5,
  "mention_count_max": 100,
  "search_query": "search term"
}}
```

### Get Facets
```http
GET /filters/facets
Response: {{entity_types: {{}}, mention_count_ranges: {{}}}}
```

## Citations

### Create Citation
```http
POST /citations/create
Content-Type: application/json

{{
  "author": "Author Name",
  "title": "Paper Title",
  "year": 2026,
  "url": "https://...",
  "doi": "10.xxx/xxx"
}}
```

### Format Citation
```http
POST /citations/format/apa
POST /citations/format/mla
POST /citations/format/chicago
POST /citations/format/bibtex

Response: {{text: "formatted citation"}}
```

### Get Entity Citations
```http
GET /citations/entity/entity_id
Response: [{{id, entity_id, metadata, format, created_at}}]
```

## Documents

### Upload Document
```http
POST /documents/upload
Content-Type: multipart/form-data

file: (binary file - PDF, Word, PowerPoint)

Response 200:
{{
  "id": "uuid",
  "filename": "document.pdf",
  "content_type": "application/pdf",
  "size": 1024000,
  "uploaded_at": "2026-05-24T..."
}}
```

### Process Document
```http
POST /documents/process/document_id
Response: {{document_id, status, extracted_text, entities_found, chunks_created}}
```

### List Documents
```http
GET /documents/list
Response: {{documents: [...], total: 42}}
```

### Get Document Text
```http
GET /documents/document_id/text
Response: {{document_id, text: "extracted text..."}}
```

## WebSocket

### Real-time Graph Updates
```
WebSocket ws://localhost:8000/ws/graph/client_id

Subscribe to entity:
{{
  "action": "subscribe",
  "entity_id": "entity_id"
}}

Receive updates:
{{
  "type": "entity_update",
  "entity_id": "entity_id",
  "timestamp": "2026-05-24T...",
  "data": {{}}
}}

Send update:
{{
  "action": "update",
  "entity_id": "entity_id",
  "data": {{}}
}}
```

## Authentication

All protected endpoints require:
```http
Authorization: Bearer <access_token>
```

## Rate Limiting

- Search: 10 req/min
- Graph: 30 req/min
- Other: 100 req/min

## Status Codes

- 200: Success
- 400: Bad request
- 401: Unauthorized
- 404: Not found
- 500: Server error

## Version

**API Version**: 1.0.0
**Last Updated**: {timestamp}
**Base URL**: http://localhost:8000
"""
    return docs.format(timestamp=datetime.utcnow().isoformat())


@router.get("/markdown")
def get_markdown_docs() -> Dict[str, str]:
    """Get API documentation in markdown format."""
    return {
        "format": "markdown",
        "content": generate_markdown_docs(),
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/json")
def get_openapi_json() -> Dict[str, Any]:
    """Get OpenAPI/Swagger specification as JSON."""
    return {
        "format": "openapi",
        "version": "3.0.0",
        "title": "Second Brain API",
        "description": "Personal knowledge management system API",
        "contact": {
            "name": "API Support",
        },
        "license": {
            "name": "MIT",
        },
    }


@router.get("/html")
def get_html_docs() -> Dict[str, str]:
    """Get API documentation in HTML format."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Second Brain API Docs</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    </head>
    <body>
        <main class="container">
            <h1>Second Brain API Documentation</h1>
            <p>Comprehensive API reference for the Second Brain knowledge management system.</p>

            <h2>Quick Start</h2>
            <ol>
                <li>Register: <code>POST /auth/register</code></li>
                <li>Login: <code>POST /auth/login</code></li>
                <li>Search: <code>POST /search/</code></li>
                <li>Explore: <code>GET /viz/entity/{id}</code></li>
            </ol>

            <h2>Endpoints</h2>
            <ul>
                <li><strong>Authentication</strong>: /auth/</li>
                <li><strong>Search</strong>: /search/</li>
                <li><strong>Graph</strong>: /graph/</li>
                <li><strong>Filters</strong>: /filters/</li>
                <li><strong>Citations</strong>: /citations/</li>
                <li><strong>Documents</strong>: /documents/</li>
                <li><strong>WebSocket</strong>: /ws/</li>
            </ul>

            <h2>Authentication</h2>
            <p>All protected endpoints require: <code>Authorization: Bearer &lt;token&gt;</code></p>

            <p><a href="/docs/markdown">View Full Documentation (Markdown)</a></p>
        </main>
    </body>
    </html>
    """
    return {
        "format": "html",
        "content": html,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/status")
def get_docs_status() -> Dict[str, Any]:
    """Get documentation generation status."""
    return {
        "status": "ready",
        "generated_at": datetime.utcnow().isoformat(),
        "available_formats": ["markdown", "json", "html"],
        "endpoints": {
            "markdown": "/docs/markdown",
            "openapi": "/docs/json",
            "html": "/docs/html",
        },
    }
