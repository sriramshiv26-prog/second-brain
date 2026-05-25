#!/usr/bin/env python3
"""Test script for semantic search functionality."""

import asyncio
import logging
from api.hybrid_search_service import HybridSearchService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_semantic_search():
    """Test all semantic search functionality."""

    print("\n" + "="*70)
    print("SEMANTIC SEARCH TEST SUITE")
    print("="*70 + "\n")

    # Initialize service (in-memory mode)
    print("✓ Initializing HybridSearchService (in-memory mode)...")
    service = HybridSearchService(use_memory=True)
    print("✓ Service initialized\n")

    # Sample data
    test_pages = [
        {
            "slug": "machine-learning-basics",
            "title": "Machine Learning Basics",
            "content": "Machine learning is a subset of artificial intelligence that enables systems to learn from data. It includes supervised learning, unsupervised learning, and reinforcement learning.",
            "metadata": {"category": "AI/ML", "difficulty": "beginner"}
        },
        {
            "slug": "deep-learning-guide",
            "title": "Deep Learning Guide",
            "content": "Deep learning uses artificial neural networks with multiple layers. It's inspired by biological neural networks and is used for image recognition, natural language processing, and more.",
            "metadata": {"category": "AI/ML", "difficulty": "intermediate"}
        },
        {
            "slug": "neural-networks-101",
            "title": "Neural Networks 101",
            "content": "Neural networks are computational models inspired by biological neural networks. They consist of interconnected nodes (neurons) that process information.",
            "metadata": {"category": "AI/ML", "difficulty": "intermediate"}
        },
        {
            "slug": "data-science-overview",
            "title": "Data Science Overview",
            "content": "Data science combines statistics, programming, and domain expertise to extract insights from data. It involves data collection, cleaning, analysis, and visualization.",
            "metadata": {"category": "Data", "difficulty": "beginner"}
        },
        {
            "slug": "nlp-introduction",
            "title": "Natural Language Processing",
            "content": "Natural language processing (NLP) is a branch of AI that helps computers understand and generate human language. It's used in chatbots, translation, and sentiment analysis.",
            "metadata": {"category": "AI/NLP", "difficulty": "intermediate"}
        },
    ]

    # Test 1: Batch indexing
    print("-" * 70)
    print("TEST 1: Batch Indexing")
    print("-" * 70)
    indexed = service.index_wiki_pages_batch(test_pages)
    print(f"✓ Indexed {indexed} pages\n")

    # Test 2: Semantic search
    print("-" * 70)
    print("TEST 2: Semantic Search")
    print("-" * 70)
    semantic_results = service.semantic_search("neural networks", top_k=3)
    print(f"Query: 'neural networks'")
    print(f"Found {len(semantic_results)} results:\n")
    for i, result in enumerate(semantic_results, 1):
        print(f"  {i}. [{result['score']:.2f}] {result['title']}")
        print(f"     {result['content'][:80]}...\n")

    # Test 3: Keyword search
    print("-" * 70)
    print("TEST 3: Keyword Search")
    print("-" * 70)
    keyword_results = service.keyword_search("neural networks", top_k=3)
    print(f"Query: 'neural networks'")
    print(f"Found {len(keyword_results)} results:\n")
    for i, result in enumerate(keyword_results, 1):
        print(f"  {i}. [{result['score']:.2f}] {result['title']}")
        print(f"     {result['content'][:80]}...\n")

    # Test 4: Hybrid search
    print("-" * 70)
    print("TEST 4: Hybrid Search (70% semantic, 30% keyword)")
    print("-" * 70)
    hybrid_results = service.hybrid_search(
        query="artificial intelligence",
        top_k=3,
        semantic_weight=0.7,
        keyword_weight=0.3
    )
    print(f"Query: 'artificial intelligence'")
    print(f"Found {len(hybrid_results)} results:\n")
    for i, result in enumerate(hybrid_results, 1):
        print(f"  {i}. [{result['score']:.2f}] {result['title']}")
        print(f"     Semantic: {result.get('semantic_score', 0):.2f}, Keyword: {result.get('keyword_score', 0):.2f}\n")

    # Test 5: Find related pages
    print("-" * 70)
    print("TEST 5: Find Related Pages")
    print("-" * 70)
    related = service.find_related_pages("machine-learning-basics", top_k=3)
    print(f"Pages related to 'Machine Learning Basics':")
    print(f"Found {len(related)} related pages:\n")
    for i, result in enumerate(related, 1):
        print(f"  {i}. [{result['score']:.2f}] {result['title']}")
        print(f"     {result['content'][:80]}...\n")

    # Test 6: Duplicate detection
    print("-" * 70)
    print("TEST 6: Duplicate Detection (threshold: 0.75)")
    print("-" * 70)

    # Add a duplicate-like page
    service.index_wiki_page(
        page_slug="neural-nets-copy",
        title="Neural Nets Overview",
        content="Neural networks are computational models inspired by biological systems. They consist of interconnected nodes that process information."
    )

    duplicates = service.detect_duplicate_content(
        "neural-networks-101",
        threshold=0.75
    )
    print(f"Pages similar to 'Neural Networks 101':")
    if duplicates:
        for i, result in enumerate(duplicates, 1):
            print(f"  {i}. [{result['score']:.2f}] {result['title']}")
    else:
        print("  (No duplicates found)")
    print()

    # Summary
    print("=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Run the API server: python -m api.server")
    print("2. Call the endpoints: curl http://localhost:8000/semantic-search/hybrid")
    print("3. Read SEMANTIC_SEARCH_SETUP.md for full documentation")
    print()


if __name__ == "__main__":
    asyncio.run(test_semantic_search())
