import json
import re
import logging
import ollama
from typing import List, Dict, Any
from config.constants import OLLAMA_BASE_URL, OLLAMA_MODEL_ENTITY

logger = logging.getLogger(__name__)

class EntityExtractor:
    """Extract entities and relationships from text using Ollama."""

    def __init__(self, model: str = OLLAMA_MODEL_ENTITY):
        self.model = model
        self.client = ollama.Client(host=OLLAMA_BASE_URL)

    def extract(self, text: str, doc_id: str = None) -> Dict[str, Any]:
        """Extract entities and relationships from text."""
        # Limit text to avoid token limits
        text_truncated = text[:5000]

        prompt = f"""Extract entities and relationships from this text.

Return ONLY valid JSON with this structure:
{{
    "entities": [
        {{"name": "...", "type": "person|concept|organization|project|location", "definition": "..."}}
    ],
    "relationships": [
        {{"source": "entity_name_1", "target": "entity_name_2", "type": "mentions|relates_to|cites|authored_by"}}
    ]
}}

Text:
{text_truncated}"""

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=False
            )

            # Parse response
            raw_text = response["response"]
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)

            if not json_match:
                logger.warning(f"Could not extract JSON from response")
                return {"entities": [], "relationships": []}

            result = json.loads(json_match.group())
            logger.info(f"Extracted {len(result.get('entities', []))} entities from document {doc_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to extract entities: {e}")
            return {"entities": [], "relationships": []}
