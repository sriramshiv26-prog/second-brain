"""Knowledge graph query API endpoints."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException
from storage.graph_db import GraphDB
from api.models import SearchResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])


class EntityDetail(SearchResult):
    """Entity with relationships and document mentions."""
    entity_type: str
    definition: str = None
    mention_count: int = 0
    documents: List[dict] = []
    relationships: List[dict] = []


class GraphNode(SearchResult):
    """Node in graph visualization."""
    node_type: str


class GraphEdge(SearchResult):
    """Edge in graph visualization."""
    source_id: str
    target_id: str
    relationship_type: str


class EntityDetailRequest(SearchResult):
    """Request to get entity details."""
    entity_id: str


class GraphTraverseRequest(SearchResult):
    """Request to traverse graph from entity."""
    entity_id: str
    depth: int = 2
    relationship_type: str = None


@router.post("/entity")
async def get_entity_detail(entity_id: str):
    """Get entity with all related documents and relationships.

    Returns:
    - Entity metadata (id, name, type, definition)
    - All documents mentioning this entity
    - All relationships (both incoming and outgoing)
    """
    try:
        graph = GraphDB()

        # Get entity
        entity = graph.get_entity(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        # Get documents and relationships
        documents = graph.get_entity_documents(entity_id, limit=20)
        relationships = graph.get_entity_relationships(entity_id)

        logger.info(f"Retrieved entity {entity_id} with {len(documents)} documents and {len(relationships)} relationships")

        return {
            "id": entity["id"],
            "name": entity["name"],
            "type": entity["type"],
            "definition": entity.get("definition"),
            "mention_count": entity.get("mention_count", 0),
            "documents": documents,
            "relationships": relationships,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/traverse")
async def traverse_graph(entity_id: str, depth: int = 2, relationship_type: str = None):
    """Traverse knowledge graph from entity up to N hops.

    Returns:
    - List of nodes (entities) within N hops
    - List of edges (relationships) between them
    - Center entity ID for visualization

    Args:
    - entity_id: Starting entity
    - depth: Maximum number of hops (1-5)
    - relationship_type: Optional filter (e.g., 'mentions', 'relates_to')
    """
    if depth < 1 or depth > 5:
        raise HTTPException(status_code=400, detail="Depth must be between 1 and 5")

    try:
        graph = GraphDB()

        # Breadth-first traversal
        visited = set()
        queue = [(entity_id, 0)]
        nodes = {}
        edges = []

        while queue:
            current_id, current_depth = queue.pop(0)

            if current_id in visited or current_depth > depth:
                continue

            visited.add(current_id)

            # Get entity
            entity = graph.get_entity(current_id)
            if entity:
                nodes[current_id] = {
                    "id": current_id,
                    "name": entity["name"],
                    "type": entity["type"],
                    "depth": current_depth,
                }

                # Get relationships
                relationships = graph.get_entity_relationships(current_id)
                for rel in relationships:
                    # Filter by relationship type if specified
                    if relationship_type and rel.get("relationship_type") != relationship_type:
                        continue

                    # Extract target ID (relationship format may vary)
                    # For now, we store the relationship metadata
                    edges.append({
                        "source_id": current_id,
                        "target_name": rel.get("name"),
                        "relationship_type": rel.get("relationship_type"),
                    })

                    # Add to queue for further traversal
                    if current_depth < depth and rel.get("name") not in visited:
                        queue.append((rel.get("name"), current_depth + 1))

        logger.info(f"Traversed graph from {entity_id} with depth {depth}: found {len(nodes)} nodes and {len(edges)} edges")

        return {
            "root_entity_id": entity_id,
            "nodes": list(nodes.values()),
            "edges": edges,
            "depth": depth,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to traverse graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))
