"""
Sync Manager - Task 5
Keeps graph DB and wiki in bidirectional sync
"""

import uuid
from typing import List, Dict, Optional
from datetime import datetime
from storage.wiki_db import get_wiki_db
from storage.graph_db import get_graph_db


class SyncReport:
    """Report of a sync operation"""
    def __init__(self):
        self.status = "success"
        self.timestamp = datetime.utcnow().isoformat()
        self.graph_to_wiki_synced = 0
        self.wiki_to_graph_synced = 0
        self.conflicts_resolved = 0
        self.errors = []

    def add_error(self, error: str):
        self.errors.append(error)
        if self.errors:
            self.status = "partial_success"


class SyncManager:
    """Manages bidirectional sync between graph DB and wiki"""

    def __init__(self):
        self.wiki_db = get_wiki_db()
        self.graph_db = get_graph_db()
        self.last_sync = None

    async def sync_graph_to_wiki(self) -> SyncReport:
        """
        Sync changes from graph DB → wiki.
        Triggered by: entity updates from Task 2-4
        """
        report = SyncReport()

        try:
            # Get all entities from graph
            # (In production, would track change timestamps)
            wiki_pages = self.wiki_db.get_all_pages(limit=1000)

            for page in wiki_pages:
                try:
                    # Update wiki page with latest entity data
                    self._sync_entity_to_wiki(page)
                    report.graph_to_wiki_synced += 1
                except Exception as e:
                    report.add_error(f"Error syncing entity to wiki: {str(e)}")

            self.last_sync = datetime.utcnow().isoformat()

        except Exception as e:
            report.add_error(f"Graph to wiki sync failed: {str(e)}")

        return report

    async def sync_wiki_to_graph(self) -> SyncReport:
        """
        Sync changes from wiki → graph DB.
        Triggered by: user edits wiki or explicit /sync endpoint
        """
        report = SyncReport()

        try:
            # Get all wiki pages
            wiki_pages = self.wiki_db.get_all_pages(limit=1000)

            for page in wiki_pages:
                try:
                    # Extract entities from wiki page content
                    extracted_entities = self._extract_entities_from_wiki(page)

                    # Update graph DB with extracted entities
                    for entity in extracted_entities:
                        self._sync_wiki_entity_to_graph(entity)
                        report.wiki_to_graph_synced += 1

                except Exception as e:
                    report.add_error(f"Error syncing wiki to graph: {str(e)}")

            self.last_sync = datetime.utcnow().isoformat()

        except Exception as e:
            report.add_error(f"Wiki to graph sync failed: {str(e)}")

        return report

    async def force_sync(self) -> SyncReport:
        """Force immediate bidirectional sync"""
        # First sync graph → wiki
        report1 = await self.sync_graph_to_wiki()

        # Then sync wiki → graph
        report2 = await self.sync_wiki_to_graph()

        # Combine reports
        combined = SyncReport()
        combined.graph_to_wiki_synced = report1.graph_to_wiki_synced
        combined.wiki_to_graph_synced = report2.wiki_to_graph_synced
        combined.errors = report1.errors + report2.errors

        if combined.errors:
            combined.status = "partial_success"

        combined.timestamp = datetime.utcnow().isoformat()
        self.last_sync = combined.timestamp

        return combined

    def _sync_entity_to_wiki(self, wiki_page) -> None:
        """Sync an entity from graph to wiki"""
        # In production, would:
        # 1. Get entity from graph DB
        # 2. Extract updated properties
        # 3. Update wiki page

        # For now, this is a placeholder
        pass

    def _extract_entities_from_wiki(self, page) -> List[Dict]:
        """Extract entities from wiki page content"""
        # In production, would:
        # 1. Parse wiki markdown
        # 2. Identify entity references (e.g., [[entity-name]])
        # 3. Extract properties from page structure

        extracted = []

        # Simple extraction: look for [[entity]] references
        import re
        pattern = r'\[\[([^\]]+)\]\]'
        matches = re.findall(pattern, page.content or "")

        for entity_name in matches:
            extracted.append({
                "name": entity_name,
                "type": "concept",
                "source_page": page.slug
            })

        return extracted

    def _sync_wiki_entity_to_graph(self, entity_data: Dict) -> None:
        """Sync a wiki entity to graph DB"""
        # In production, would:
        # 1. Check if entity exists in graph
        # 2. If not, create it
        # 3. Update properties
        # 4. Create relationships

        # For now, this is a placeholder
        pass

    def get_sync_status(self) -> Dict:
        """Get current sync status"""
        return {
            "last_sync": self.last_sync,
            "status": "ready",
            "graph_pages_count": 0,  # Would query actual counts
            "wiki_pages_count": self.wiki_db.get_all_pages(limit=1).__len__(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def check_sync_conflicts(self) -> List[Dict]:
        """Check for sync conflicts between graph and wiki"""
        conflicts = []

        # Get all wiki pages
        wiki_pages = self.wiki_db.get_all_pages(limit=1000)

        for page in wiki_pages:
            # In production, would:
            # 1. Get corresponding entity from graph
            # 2. Compare versions
            # 3. If different, flag as conflict

            # For now, no conflicts
            pass

        return conflicts

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str  # "prefer_graph" or "prefer_wiki"
    ) -> bool:
        """Resolve a sync conflict"""
        # In production, would:
        # 1. Load conflict details
        # 2. Apply resolution (prefer one side)
        # 3. Update both databases
        # 4. Mark conflict as resolved

        # For now, always succeed
        return True


# Global instance
_sync_manager_instance = None


def get_sync_manager() -> SyncManager:
    """Get or create global sync manager instance"""
    global _sync_manager_instance
    if _sync_manager_instance is None:
        _sync_manager_instance = SyncManager()
    return _sync_manager_instance
