"""
Synthesis Service - Orchestrates wiki integration when documents are processed
Auto-creates/updates wiki pages for extracted entities
"""

import re
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from storage.wiki_db import get_wiki_db, WikiPage
from storage.graph_db import get_graph_db


class Entity:
    """Represents an entity from the graph database"""
    def __init__(self, entity_id: str, name: str, type_: str, definition: str = "", relationships: Optional[List] = None):
        self.id = entity_id
        self.name = name
        self.type = type_
        self.definition = definition
        self.relationships = relationships or []


class SynthesisService:
    """Service for integrating documents into the wiki system"""

    def __init__(self):
        self.wiki_db = get_wiki_db()
        self.graph_db = get_graph_db()

    async def integrate_document(
        self,
        doc_id: str,
        entities: List[Dict],
        doc_title: str = ""
    ) -> Dict[str, str]:
        """
        Main integration hook called after document processing.
        Creates/updates wiki pages for entities and establishes backlinks.

        Returns:
            Mapping of entity_id → wiki_slug
        """
        entity_mapping = {}

        if not entities:
            return entity_mapping

        # Create or update wiki page for each entity
        for entity in entities:
            try:
                slug = self._create_entity_slug(entity["name"])
                existing_page = self.wiki_db.get_page(slug)

                if existing_page:
                    # Update existing page with new document reference
                    context = f"Referenced in document: {doc_title or doc_id}"
                    self.wiki_db.update_page(
                        slug,
                        content=self._enhance_page_content(existing_page.content, entity)
                    )
                else:
                    # Create new page for this entity
                    page = self.wiki_db.create_page(
                        slug=slug,
                        title=entity["name"],
                        content=self._generate_page_content(entity, doc_title),
                        entity_ids=[entity["id"]]
                    )

                entity_mapping[entity["id"]] = slug

            except Exception as e:
                print(f"Error integrating entity {entity.get('name', 'unknown')}: {str(e)}")
                continue

        # Create backlinks between related entities
        self._create_entity_backlinks(entity_mapping)

        return entity_mapping

    def _create_entity_slug(self, entity_name: str) -> str:
        """Generate URL-safe slug from entity name"""
        # Convert to lowercase and replace spaces/special chars
        slug = re.sub(r'[^\w\s-]', '', entity_name.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        return slug[:50]  # Truncate to reasonable length

    def _generate_page_content(self, entity: Dict, doc_title: str = "") -> str:
        """Generate initial wiki page content from entity"""
        content_parts = []

        # Title section
        content_parts.append(f"# {entity.get('name', 'Untitled')}\n")

        # Entity type
        content_parts.append(f"**Type:** {entity.get('type', 'unknown')}\n")

        # Definition if available
        if entity.get('definition'):
            content_parts.append(f"\n## Definition\n\n{entity['definition']}\n")

        # Document context
        if doc_title:
            content_parts.append(f"\n## First Mentioned\n\n")
            content_parts.append(f"Document: {doc_title}\n")

        # Section for relationships to be filled in
        content_parts.append(f"\n## Related Concepts\n\n")
        content_parts.append("(Relationships to be populated by synthesis)\n")

        # Metadata
        content_parts.append(f"\n---\n")
        content_parts.append(f"*Created: {datetime.utcnow().isoformat()}*\n")
        content_parts.append(f"*Entity ID: {entity.get('id', 'N/A')}*\n")

        return "".join(content_parts)

    def _enhance_page_content(self, existing_content: str, entity: Dict) -> str:
        """Enhance existing page with new entity information"""
        # For now, just return existing content
        # In Task 4 (Periodic Synthesis), this will be more sophisticated
        return existing_content

    def _create_entity_backlinks(self, entity_mapping: Dict[str, str]) -> None:
        """Create backlinks between related entities"""
        # For each entity, find related entities in the graph
        try:
            for entity_id, from_slug in entity_mapping.items():
                # Get relationships for this entity from graph DB
                related_entities = self.graph_db.get_related_entities(entity_id)

                # Create backlinks to related entities
                for related in related_entities:
                    related_slug = self._create_entity_slug(related.get("name", ""))

                    # Check if related wiki page exists
                    if self.wiki_db.get_page(related_slug):
                        try:
                            self.wiki_db.add_backlink(
                                from_slug=from_slug,
                                to_slug=related_slug,
                                context=f"Related via: {related.get('relationship_type', 'connection')}"
                            )
                        except Exception as e:
                            print(f"Error creating backlink {from_slug} → {related_slug}: {str(e)}")

        except Exception as e:
            print(f"Error creating backlinks: {str(e)}")

    def get_entity_context(self, entity_id: str) -> Dict:
        """Get full context for an entity from graph DB"""
        try:
            entity = self.graph_db.get_entity(entity_id)
            relationships = self.graph_db.get_relationships_for_entity(entity_id)

            return {
                "entity": entity,
                "relationships": relationships,
                "related_count": len(relationships)
            }
        except Exception as e:
            print(f"Error getting entity context: {str(e)}")
            return {}

    async def bulk_integrate_documents(
        self,
        documents: List[Tuple[str, List[Dict], str]]
    ) -> Dict[str, Dict[str, str]]:
        """
        Integrate multiple documents at once.
        documents: List of (doc_id, entities, doc_title) tuples
        """
        results = {}

        for doc_id, entities, doc_title in documents:
            mapping = await self.integrate_document(doc_id, entities, doc_title)
            results[doc_id] = mapping

        return results


# Global instance
_synthesis_service_instance = None


def get_synthesis_service() -> SynthesisService:
    """Get or create global synthesis service instance"""
    global _synthesis_service_instance
    if _synthesis_service_instance is None:
        _synthesis_service_instance = SynthesisService()
    return _synthesis_service_instance
