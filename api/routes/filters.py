"""Advanced filtering and faceting endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from storage.graph_db import get_graph_db

router = APIRouter(prefix="/filters", tags=["filters"])


class FilterRequest(BaseModel):
    """Advanced filter request."""

    entity_types: Optional[List[str]] = None
    mention_count_min: Optional[int] = None
    mention_count_max: Optional[int] = None
    relationship_types: Optional[List[str]] = None
    search_query: Optional[str] = None


class FilteredEntity(BaseModel):
    """Filtered entity response."""

    id: str
    name: str
    type: str
    mention_count: int
    definition: Optional[str] = None


class FilterResponse(BaseModel):
    """Filter response with results and facets."""

    results: List[FilteredEntity]
    total_count: int
    facets: dict


@router.post("/entities", response_model=FilterResponse)
def filter_entities(request: FilterRequest):
    """Filter entities by type, mention count, and relationships."""
    db = get_graph_db()

    try:
        cursor = db.cursor()
        cursor.execute("SELECT id, name, type, mention_count, definition FROM entities")
        entities = [dict(row) for row in cursor.fetchall()]

        filtered = []
        for entity in entities:
            matches = True

            if request.entity_types and entity.get("type") not in request.entity_types:
                matches = False

            if request.mention_count_min is not None:
                if entity.get("mention_count", 0) < request.mention_count_min:
                    matches = False

            if request.mention_count_max is not None:
                if entity.get("mention_count", 0) > request.mention_count_max:
                    matches = False

            if request.search_query:
                query_lower = request.search_query.lower()
                name_match = query_lower in entity.get("name", "").lower()
                def_match = query_lower in entity.get("definition", "").lower()
                if not (name_match or def_match):
                    matches = False

            if matches:
                filtered.append(
                    FilteredEntity(
                        id=entity.get("id"),
                        name=entity.get("name"),
                        type=entity.get("type"),
                        mention_count=entity.get("mention_count", 0),
                        definition=entity.get("definition"),
                    )
                )

        facets = _compute_facets(filtered, request)

        return FilterResponse(
            results=filtered[:100],
            total_count=len(filtered),
            facets=facets,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Filter error: {str(e)}",
        )


@router.get("/facets")
def get_facets():
    """Get available filter facets."""
    db = get_graph_db()

    try:
        cursor = db.cursor()
        cursor.execute("SELECT id, name, type, mention_count, definition FROM entities")
        entities = [dict(row) for row in cursor.fetchall()]

        type_counts = {}
        for entity in entities:
            entity_type = entity.get("type", "Unknown")
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

        return {
            "entity_types": type_counts,
            "mention_count_ranges": {
                "0-10": sum(1 for e in entities if 0 <= e.get("mention_count", 0) <= 10),
                "11-50": sum(1 for e in entities if 11 <= e.get("mention_count", 0) <= 50),
                "51-100": sum(1 for e in entities if 51 <= e.get("mention_count", 0) <= 100),
                "100+": sum(1 for e in entities if e.get("mention_count", 0) > 100),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Facet error: {str(e)}",
        )


def _compute_facets(filtered: List[FilteredEntity], request: FilterRequest) -> dict:
    """Compute facets from filtered results."""
    type_counts = {}
    mention_ranges = {"0-10": 0, "11-50": 0, "51-100": 0, "100+": 0}

    for entity in filtered:
        type_counts[entity.type] = type_counts.get(entity.type, 0) + 1

        if 0 <= entity.mention_count <= 10:
            mention_ranges["0-10"] += 1
        elif 11 <= entity.mention_count <= 50:
            mention_ranges["11-50"] += 1
        elif 51 <= entity.mention_count <= 100:
            mention_ranges["51-100"] += 1
        else:
            mention_ranges["100+"] += 1

    return {
        "entity_types": type_counts,
        "mention_count_ranges": mention_ranges,
    }


@router.post("/search-advanced")
def advanced_search(request: FilterRequest):
    """Advanced search with multiple filters and faceting."""
    return filter_entities(request)
