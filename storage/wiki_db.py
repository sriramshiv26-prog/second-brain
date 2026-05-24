"""
Wiki Database Layer - CRUD operations for wiki pages
Handles creation, updates, linking, and retrieval of wiki pages
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import os

# Database path
DB_PATH = os.path.expanduser("~/second-brain-data/second_brain.db")


@dataclass
class WikiPage:
    id: str
    slug: str
    title: str
    content: Optional[str] = None
    entity_ids: Optional[List[str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_synthesis: Optional[str] = None
    contradiction_count: int = 0
    version: int = 1
    synthesized_content: Optional[str] = None


@dataclass
class WikiBacklink:
    from_slug: str
    to_slug: str
    context: Optional[str] = None
    created_at: Optional[str] = None


class WikiDB:
    """Database operations for wiki system"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._ensure_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self):
        """Ensure wiki tables exist"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Wiki pages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wiki_pages (
                id TEXT PRIMARY KEY,
                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_synthesis TIMESTAMP,
                entity_ids TEXT,
                contradiction_count INTEGER DEFAULT 0,
                version INTEGER DEFAULT 1,
                synthesized_content TEXT
            )
        """)

        # Backlinks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wiki_backlinks (
                from_slug TEXT NOT NULL,
                to_slug TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (from_slug, to_slug)
            )
        """)

        # Contradictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contradictions (
                id TEXT PRIMARY KEY,
                entity_id TEXT NOT NULL,
                wiki_slug TEXT NOT NULL,
                statement_a TEXT NOT NULL,
                statement_b TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at TIMESTAMP,
                resolution_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Synthesis logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS synthesis_logs (
                id TEXT PRIMARY KEY,
                entity_id TEXT NOT NULL,
                wiki_slug TEXT NOT NULL,
                synthesis_type TEXT,
                input_content TEXT,
                output_content TEXT,
                cost REAL DEFAULT 0,
                tokens_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wiki_slug ON wiki_pages(slug)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wiki_entity_ids ON wiki_pages(entity_ids)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_backlinks_from ON wiki_backlinks(from_slug)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_backlinks_to ON wiki_backlinks(to_slug)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contradictions_entity ON contradictions(entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_synthesis_logs_entity ON synthesis_logs(entity_id)")

        conn.commit()
        conn.close()

    def create_page(
        self,
        slug: str,
        title: str,
        content: str = "",
        entity_ids: Optional[List[str]] = None
    ) -> WikiPage:
        """Create new wiki page"""
        page_id = f"wiki_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO wiki_pages
                (id, slug, title, content, entity_ids, created_at, updated_at, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                page_id,
                slug,
                title,
                content,
                json.dumps(entity_ids or []),
                now,
                now
            ))
            conn.commit()

            return WikiPage(
                id=page_id,
                slug=slug,
                title=title,
                content=content,
                entity_ids=entity_ids or [],
                created_at=now,
                updated_at=now,
                version=1
            )
        finally:
            conn.close()

    def get_page(self, slug: str) -> Optional[WikiPage]:
        """Get wiki page by slug"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT * FROM wiki_pages WHERE slug = ?",
                (slug,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_page(row)
        finally:
            conn.close()

    def update_page(
        self,
        slug: str,
        content: Optional[str] = None,
        title: Optional[str] = None,
        synthesized_content: Optional[str] = None
    ) -> Optional[WikiPage]:
        """Update existing wiki page"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            now = datetime.utcnow().isoformat()

            # Get current page
            cursor.execute("SELECT * FROM wiki_pages WHERE slug = ?", (slug,))
            row = cursor.fetchone()
            if not row:
                return None

            current_version = row["version"]

            # Update fields
            updates = {"updated_at": now, "version": current_version + 1}
            if content is not None:
                updates["content"] = content
            if title is not None:
                updates["title"] = title
            if synthesized_content is not None:
                updates["synthesized_content"] = synthesized_content
                updates["last_synthesis"] = now

            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values()) + [slug]

            cursor.execute(
                f"UPDATE wiki_pages SET {set_clause} WHERE slug = ?",
                values
            )
            conn.commit()

            # Fetch updated row
            cursor.execute("SELECT * FROM wiki_pages WHERE slug = ?", (slug,))
            return self._row_to_page(cursor.fetchone())
        finally:
            conn.close()

    def delete_page(self, slug: str) -> bool:
        """Delete wiki page (soft delete via versioning)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM wiki_pages WHERE slug = ?", (slug,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def search_pages(self, query: str) -> List[WikiPage]:
        """Full-text search wiki pages"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM wiki_pages
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY updated_at DESC
            """, (f"%{query}%", f"%{query}%"))

            return [self._row_to_page(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def add_backlink(
        self,
        from_slug: str,
        to_slug: str,
        context: Optional[str] = None
    ) -> WikiBacklink:
        """Create backlink between pages"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT OR REPLACE INTO wiki_backlinks
                (from_slug, to_slug, context, created_at)
                VALUES (?, ?, ?, ?)
            """, (from_slug, to_slug, context, now))
            conn.commit()

            return WikiBacklink(from_slug, to_slug, context, now)
        finally:
            conn.close()

    def get_backlinks(self, slug: str) -> List[WikiBacklink]:
        """Get all pages linking TO this page"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM wiki_backlinks WHERE to_slug = ?
            """, (slug,))

            return [self._backlink_row_to_obj(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_related_pages(self, slug: str) -> List[WikiPage]:
        """Get pages related to this page (both directions)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get all related slugs
            cursor.execute("""
                SELECT DISTINCT to_slug FROM wiki_backlinks WHERE from_slug = ?
                UNION
                SELECT DISTINCT from_slug FROM wiki_backlinks WHERE to_slug = ?
            """, (slug, slug))

            related_slugs = [row[0] for row in cursor.fetchall()]

            # Fetch full pages
            related_pages = []
            for related_slug in related_slugs:
                page = self.get_page(related_slug)
                if page:
                    related_pages.append(page)

            return related_pages
        finally:
            conn.close()

    def get_pages_for_entity(self, entity_id: str) -> List[WikiPage]:
        """Get wiki pages associated with an entity"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM wiki_pages
                WHERE entity_ids LIKE ?
                ORDER BY updated_at DESC
            """, (f"%{entity_id}%",))

            return [self._row_to_page(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_all_pages(self, limit: int = 100, offset: int = 0) -> List[WikiPage]:
        """Get all wiki pages with pagination"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM wiki_pages
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            return [self._row_to_page(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def log_synthesis(
        self,
        entity_id: str,
        wiki_slug: str,
        synthesis_type: str,
        input_content: str,
        output_content: str,
        cost: float = 0.0,
        tokens_used: int = 0
    ) -> str:
        """Log synthesis operation"""
        log_id = f"synth_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO synthesis_logs
                (id, entity_id, wiki_slug, synthesis_type, input_content, output_content, cost, tokens_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (log_id, entity_id, wiki_slug, synthesis_type, input_content, output_content, cost, tokens_used, now))
            conn.commit()
            return log_id
        finally:
            conn.close()

    def add_contradiction(
        self,
        entity_id: str,
        wiki_slug: str,
        statement_a: str,
        statement_b: str,
        confidence: float = 0.5
    ) -> str:
        """Log contradiction"""
        contradiction_id = f"contra_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO contradictions
                (id, entity_id, wiki_slug, statement_a, statement_b, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (contradiction_id, entity_id, wiki_slug, statement_a, statement_b, confidence, now))

            # Update contradiction count
            cursor.execute(
                "UPDATE wiki_pages SET contradiction_count = contradiction_count + 1 WHERE slug = ?",
                (wiki_slug,)
            )
            conn.commit()
            return contradiction_id
        finally:
            conn.close()

    def get_unresolved_contradictions(self, wiki_slug: Optional[str] = None) -> List[Dict]:
        """Get unresolved contradictions"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if wiki_slug:
                cursor.execute("""
                    SELECT * FROM contradictions
                    WHERE wiki_slug = ? AND resolved = FALSE
                    ORDER BY confidence DESC
                """, (wiki_slug,))
            else:
                cursor.execute("""
                    SELECT * FROM contradictions
                    WHERE resolved = FALSE
                    ORDER BY confidence DESC
                """)

            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def _row_to_page(row: sqlite3.Row) -> WikiPage:
        """Convert database row to WikiPage object"""
        entity_ids = json.loads(row["entity_ids"] or "[]")

        return WikiPage(
            id=row["id"],
            slug=row["slug"],
            title=row["title"],
            content=row["content"],
            entity_ids=entity_ids,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_synthesis=row["last_synthesis"],
            contradiction_count=row["contradiction_count"],
            version=row["version"],
            synthesized_content=row["synthesized_content"]
        )

    @staticmethod
    def _backlink_row_to_obj(row: sqlite3.Row) -> WikiBacklink:
        """Convert database row to WikiBacklink object"""
        return WikiBacklink(
            from_slug=row["from_slug"],
            to_slug=row["to_slug"],
            context=row["context"],
            created_at=row["created_at"]
        )


# Global instance
_wiki_db_instance = None


def get_wiki_db() -> WikiDB:
    """Get or create global wiki database instance"""
    global _wiki_db_instance
    if _wiki_db_instance is None:
        _wiki_db_instance = WikiDB()
    return _wiki_db_instance
