"""Graph visualization API endpoints (D3.js/Cytoscape compatible)."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException
from storage.graph_db import GraphDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/viz", tags=["visualization"])


class VizNode:
    """D3.js/Cytoscape node representation."""
    def __init__(self, node_id: str, label: str, node_type: str, size: int = 10):
        self.id = node_id
        self.label = label
        self.type = node_type
        self.size = size

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "size": self.size,
        }


class VizEdge:
    """D3.js/Cytoscape edge representation."""
    def __init__(self, source: str, target: str, label: str):
        self.source = source
        self.target = target
        self.label = label

    def to_dict(self):
        return {
            "source": self.source,
            "target": self.target,
            "label": self.label,
        }


@router.get("/entity/{entity_id}")
async def visualize_entity(entity_id: str):
    """Return entity neighborhood for graph visualization.

    Returns nodes and edges optimized for D3.js or Cytoscape rendering.
    Node size is based on mention count (relevance).

    Response format:
    {
        "nodes": [{"id": "...", "label": "...", "type": "...", "size": 10}, ...],
        "edges": [{"source": "...", "target": "...", "label": "..."}, ...],
        "center_id": "entity_id"
    }
    """
    try:
        graph = GraphDB()

        # Get entity
        entity = graph.get_entity(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        # Create center node
        mention_count = entity.get("mention_count", 1)
        center_node = VizNode(
            node_id=entity_id,
            label=entity["name"],
            node_type=entity["type"],
            size=max(10, min(mention_count * 5, 50))  # Scale 10-50
        )

        nodes = [center_node.to_dict()]
        edges = []

        # Get relationships (neighbors)
        relationships = graph.get_entity_relationships(entity_id)
        for rel in relationships:
            target_name = rel.get("name", "Unknown")
            target_type = rel.get("type", "unknown")
            target_entity = graph.get_entity_by_name(target_name)

            if target_entity:
                target_id = target_entity["id"]
                target_mention_count = target_entity.get("mention_count", 1)

                # Add neighbor node
                neighbor_node = VizNode(
                    node_id=target_id,
                    label=target_name,
                    node_type=target_type,
                    size=max(10, min(target_mention_count * 5, 50))
                )
                nodes.append(neighbor_node.to_dict())

                # Add edge
                edge = VizEdge(
                    source=entity_id,
                    target=target_id,
                    label=rel.get("relationship_type", "relates_to")
                )
                edges.append(edge.to_dict())

        logger.info(f"Visualized entity {entity_id}: {len(nodes)} nodes, {len(edges)} edges")

        return {
            "nodes": nodes,
            "edges": edges,
            "center_id": entity_id,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to visualize entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))
