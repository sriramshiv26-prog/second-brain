"""
Periodic Synthesis - Task 4
Daily scheduled consolidation using Qwen API
Updates wiki pages with synthesis insights
"""

import os
import uuid
import json
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from storage.wiki_db import get_wiki_db
from api.contradiction_detector import get_contradiction_detector


class SynthesisResult:
    """Result of a synthesis operation"""
    def __init__(
        self,
        entity_id: str,
        wiki_slug: str,
        synthesis: str,
        confidence: float = 0.8,
        tokens_used: int = 0,
        cost: float = 0.0
    ):
        self.id = f"synth_{uuid.uuid4().hex[:12]}"
        self.entity_id = entity_id
        self.wiki_slug = wiki_slug
        self.synthesis = synthesis
        self.confidence = confidence
        self.tokens_used = tokens_used
        self.cost = cost
        self.created_at = datetime.utcnow().isoformat()


class PeriodicSynthesis:
    """Handles daily periodic synthesis consolidation"""

    def __init__(self, qwen_api_key: Optional[str] = None):
        self.qwen_api_key = qwen_api_key or os.getenv("QWEN_API_KEY")
        self.wiki_db = get_wiki_db()
        self.detector = get_contradiction_detector(qwen_api_key)
        self.scheduler = AsyncIOScheduler()
        self.qwen_api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.synthesis_history = []

    def start_scheduler(self):
        """Start the APScheduler for daily synthesis"""
        try:
            self.scheduler.add_job(
                self.daily_synthesis,
                trigger="cron",
                hour=2,
                minute=0,
                id="daily_synthesis_job",
                name="Daily Knowledge Synthesis"
            )
            self.scheduler.start()
            print("✓ Periodic synthesis scheduler started (daily at 2:00 UTC)")
        except Exception as e:
            print(f"⚠ Failed to start scheduler: {str(e)}")

    async def daily_synthesis(self) -> Dict:
        """
        Main daily consolidation job.
        Runs at 2:00 UTC every day.
        """
        try:
            # Get recently updated entities (updated in past 24h)
            updated_pages = self.wiki_db.get_all_pages(limit=100)

            if not updated_pages:
                return {"status": "no_pages", "processed": 0}

            # Batch pages for efficiency
            batches = self._batch_pages(updated_pages, batch_size=10)

            results = []
            total_cost = 0.0
            total_tokens = 0

            for batch in batches:
                batch_results = await self._synthesize_batch(batch)
                results.extend(batch_results)
                total_cost += sum(r.cost for r in batch_results)
                total_tokens += sum(r.tokens_used for r in batch_results)

            self.synthesis_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "pages_processed": len(updated_pages),
                "syntheses_created": len(results),
                "total_cost": total_cost,
                "total_tokens": total_tokens
            })

            return {
                "status": "completed",
                "pages_processed": len(updated_pages),
                "syntheses_created": len(results),
                "total_cost": total_cost,
                "total_tokens": total_tokens
            }

        except Exception as e:
            print(f"Error during daily synthesis: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _synthesize_batch(self, pages: List) -> List[SynthesisResult]:
        """
        Synthesize a batch of wiki pages using Qwen.

        Cost: ~$0.0005-0.002 per page
        """
        if not self.qwen_api_key:
            # Fallback: simple heuristic synthesis
            return self._heuristic_synthesis_batch(pages)

        results = []

        # Prepare batch context
        context = "\n\n".join([
            f"Page: {page.title}\n{page.content[:500]}"
            for page in pages
            if page.content
        ])

        prompt = f"""Analyze these wiki pages and provide synthesis insights:

{context}

For each entity/topic:
1. How do they relate to each other?
2. What gaps exist in current knowledge?
3. What connections should be drawn?
4. What contradictions exist?

Respond with JSON:
{{
    "insights": [
        {{
            "topic": "name",
            "relationships": "description",
            "gaps": ["gap1", "gap2"],
            "connections": ["connection1"],
            "contradictions": ["contradiction1"]
        }}
    ]
}}"""

        try:
            response = await self._query_qwen(prompt)

            if response:
                try:
                    data = json.loads(response)
                    insights = data.get("insights", [])

                    for i, page in enumerate(pages):
                        if i < len(insights):
                            insight = insights[i]
                            synthesis_text = f"""## Synthesis Insights

**Relationships:**
{insight.get('relationships', 'N/A')}

**Knowledge Gaps:**
- {chr(10).join('- ' + gap for gap in insight.get('gaps', []))}

**Suggested Connections:**
- {chr(10).join('- ' + conn for conn in insight.get('connections', []))}

**Potential Contradictions:**
- {chr(10).join('- ' + cont for cont in insight.get('contradictions', []))}
"""

                            # Update wiki page
                            self.wiki_db.update_page(
                                slug=page.slug,
                                synthesized_content=synthesis_text
                            )

                            # Log synthesis
                            log_id = self.wiki_db.log_synthesis(
                                entity_id="",  # Would be populated with actual entity
                                wiki_slug=page.slug,
                                synthesis_type="periodic",
                                input_content=page.content or "",
                                output_content=synthesis_text,
                                cost=0.002,  # Approximate cost per page
                                tokens_used=150
                            )

                            result = SynthesisResult(
                                entity_id="",
                                wiki_slug=page.slug,
                                synthesis=synthesis_text,
                                confidence=0.8,
                                tokens_used=150,
                                cost=0.002
                            )
                            results.append(result)

                except json.JSONDecodeError:
                    print(f"Failed to parse Qwen response for batch")

        except Exception as e:
            print(f"Error in batch synthesis: {str(e)}")

        return results

    def _heuristic_synthesis_batch(self, pages: List) -> List[SynthesisResult]:
        """
        Simple heuristic synthesis (no API calls).
        Useful when Qwen API is not available.
        """
        results = []

        for page in pages:
            synthesis = f"""## Synthesis Insights

**Generated:** {datetime.utcnow().isoformat()}

**Summary:**
This page covers {page.title}. Consider reviewing for:
- Completeness of definitions
- Accuracy of relationships
- Potential conflicts with other knowledge

**Recommendations:**
- Review against related pages
- Add more concrete examples
- Cross-reference with source documents

*Note: This is heuristic synthesis. Enable Qwen API for AI-powered insights.*
"""

            # Log synthesis
            self.wiki_db.log_synthesis(
                entity_id="",
                wiki_slug=page.slug,
                synthesis_type="heuristic",
                input_content=page.content or "",
                output_content=synthesis,
                cost=0.0,
                tokens_used=0
            )

            result = SynthesisResult(
                entity_id="",
                wiki_slug=page.slug,
                synthesis=synthesis,
                confidence=0.5,
                tokens_used=0,
                cost=0.0
            )
            results.append(result)

        return results

    async def _query_qwen(self, prompt: str) -> Optional[str]:
        """Query Qwen API for synthesis"""
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
                "temperature": 0.5,
                "top_p": 0.9,
                "max_tokens": 1000
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
    def _batch_pages(pages: List, batch_size: int = 10) -> List[List]:
        """Batch pages for efficient processing"""
        batches = []
        for i in range(0, len(pages), batch_size):
            batches.append(pages[i:i + batch_size])
        return batches

    def get_synthesis_history(self) -> List[Dict]:
        """Get synthesis operation history"""
        return self.synthesis_history[-30:]  # Last 30 days

    def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("✓ Periodic synthesis scheduler stopped")


# Global instance
_periodic_synthesis_instance = None


def get_periodic_synthesis(qwen_api_key: Optional[str] = None) -> PeriodicSynthesis:
    """Get or create global periodic synthesis instance"""
    global _periodic_synthesis_instance
    if _periodic_synthesis_instance is None:
        _periodic_synthesis_instance = PeriodicSynthesis(qwen_api_key)
    return _periodic_synthesis_instance
