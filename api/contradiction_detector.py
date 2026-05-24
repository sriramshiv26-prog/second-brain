"""
Contradiction Detector - Task 3
Identifies logical conflicts in wiki pages using Qwen logic engine
"""

import os
import uuid
import json
from typing import List, Dict, Optional
from datetime import datetime
import httpx
from storage.wiki_db import get_wiki_db, WikiPage


class Contradiction:
    """Represents a detected contradiction"""
    def __init__(
        self,
        id: str,
        entity_id: str,
        wiki_slug: str,
        statement_a: str,
        statement_b: str,
        confidence: float = 0.5,
        reason: str = ""
    ):
        self.id = id
        self.entity_id = entity_id
        self.wiki_slug = wiki_slug
        self.statement_a = statement_a
        self.statement_b = statement_b
        self.confidence = confidence
        self.reason = reason


class ContradictionDetector:
    """Detects logical conflicts in wiki pages"""

    def __init__(self, qwen_api_key: Optional[str] = None):
        self.qwen_api_key = qwen_api_key or os.getenv("QWEN_API_KEY")
        self.wiki_db = get_wiki_db()
        self.qwen_api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    async def detect(self, entity_id: str) -> List[Contradiction]:
        """
        Detect contradictions for an entity across all wiki pages mentioning it.

        Args:
            entity_id: The entity to check for contradictions

        Returns:
            List of detected contradictions
        """
        wiki_pages = self.wiki_db.get_pages_for_entity(entity_id)

        if not wiki_pages:
            return []

        contradictions = []

        # For each wiki page, look for contradictions
        for page in wiki_pages:
            page_contradictions = await self._analyze_page_contradictions(entity_id, page)
            contradictions.extend(page_contradictions)

        return contradictions

    async def _analyze_page_contradictions(
        self,
        entity_id: str,
        page: WikiPage
    ) -> List[Contradiction]:
        """Analyze a single page for internal contradictions"""
        if not page.content:
            return []

        # Extract key statements from page content
        statements = self._extract_statements(page.content)

        if len(statements) < 2:
            return []

        contradictions = []

        # Check pairs of statements for contradictions
        for i, stmt_a in enumerate(statements):
            for stmt_b in statements[i + 1:]:
                contradiction = await self._check_contradiction(
                    stmt_a,
                    stmt_b,
                    entity_id,
                    page.slug
                )

                if contradiction:
                    contradictions.append(contradiction)

        return contradictions

    async def _check_contradiction(
        self,
        statement_a: str,
        statement_b: str,
        entity_id: str,
        wiki_slug: str
    ) -> Optional[Contradiction]:
        """
        Check if two statements contradict each other using Qwen.

        Cost: ~$0.001-0.005 per call
        """
        if not self.qwen_api_key:
            # Fallback: simple heuristic contradiction detection
            return self._heuristic_contradiction_check(
                statement_a, statement_b, entity_id, wiki_slug
            )

        try:
            prompt = f"""Analyze these two statements for logical contradictions:

Statement A: {statement_a}
Statement B: {statement_b}

Respond with JSON:
{{
    "contradicts": true/false,
    "confidence": 0.0-1.0,
    "reason": "explanation"
}}"""

            response = await self._query_qwen(prompt)

            if not response:
                return None

            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if not json_match:
                    return None
                data = json.loads(json_match.group())

            if data.get("contradicts"):
                contradiction = Contradiction(
                    id=f"contra_{uuid.uuid4().hex[:12]}",
                    entity_id=entity_id,
                    wiki_slug=wiki_slug,
                    statement_a=statement_a,
                    statement_b=statement_b,
                    confidence=data.get("confidence", 0.5),
                    reason=data.get("reason", "")
                )

                # Log to database
                self.wiki_db.add_contradiction(
                    entity_id=entity_id,
                    wiki_slug=wiki_slug,
                    statement_a=statement_a,
                    statement_b=statement_b,
                    confidence=contradiction.confidence
                )

                return contradiction

            return None

        except Exception as e:
            print(f"Error checking contradiction: {str(e)}")
            # Fall back to heuristic
            return self._heuristic_contradiction_check(
                statement_a, statement_b, entity_id, wiki_slug
            )

    def _heuristic_contradiction_check(
        self,
        statement_a: str,
        statement_b: str,
        entity_id: str,
        wiki_slug: str
    ) -> Optional[Contradiction]:
        """
        Simple heuristic contradiction detection (no API calls).
        Useful when Qwen API is not available.
        """
        # Check for contradictory keywords
        contradictory_pairs = [
            ("is", "is not"),
            ("true", "false"),
            ("always", "never"),
            ("possible", "impossible"),
            ("agree", "disagree"),
            ("increase", "decrease"),
        ]

        stmt_a_lower = statement_a.lower()
        stmt_b_lower = statement_b.lower()

        for neg, pos in contradictory_pairs:
            if f"{pos} " in stmt_a_lower and f"{neg} " in stmt_b_lower:
                contradiction = Contradiction(
                    id=f"contra_{uuid.uuid4().hex[:12]}",
                    entity_id=entity_id,
                    wiki_slug=wiki_slug,
                    statement_a=statement_a,
                    statement_b=statement_b,
                    confidence=0.6,  # Lower confidence for heuristic
                    reason=f"Heuristic detection: '{pos}' vs '{neg}'"
                )

                # Log to database
                self.wiki_db.add_contradiction(
                    entity_id=entity_id,
                    wiki_slug=wiki_slug,
                    statement_a=statement_a,
                    statement_b=statement_b,
                    confidence=contradiction.confidence
                )

                return contradiction

        return None

    async def _query_qwen(self, prompt: str) -> Optional[str]:
        """Query Qwen API for logic analysis"""
        if not self.qwen_api_key:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.qwen_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "qwen-max",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "top_p": 0.8,
                "max_tokens": 500
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.qwen_api_url,
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("output", {}).get("choices"):
                        return data["output"]["choices"][0]["message"]["content"]

            return None

        except Exception as e:
            print(f"Qwen API error: {str(e)}")
            return None

    @staticmethod
    def _extract_statements(content: str) -> List[str]:
        """Extract key statements from wiki page content"""
        # Split by sentences and filter empty ones
        sentences = content.split(".")
        statements = [
            s.strip()
            for s in sentences
            if s.strip() and len(s.strip()) > 10
        ]
        return statements[:10]  # Limit to first 10 statements


# Global instance
_detector_instance = None


def get_contradiction_detector(qwen_api_key: Optional[str] = None) -> ContradictionDetector:
    """Get or create global contradiction detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = ContradictionDetector(qwen_api_key)
    return _detector_instance
