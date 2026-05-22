import pytest
from process.embed import EmbeddingPipeline
from storage.vector_db import VectorStore

@pytest.fixture
def embedding_pipeline():
    return EmbeddingPipeline()

@pytest.fixture
def vector_store():
    return VectorStore()

def test_embed_single(embedding_pipeline):
    """Test embedding a single text."""
    text = "Artificial intelligence is transforming technology."
    embedding = embedding_pipeline.embed_single(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 768  # nomic-embed-text-v1.5 is 768-dimensional

def test_embed_batch(embedding_pipeline):
    """Test batch embedding."""
    texts = [
        "Machine learning is a subset of AI.",
        "Neural networks are inspired by the brain.",
        "Deep learning uses multiple layers."
    ]
    embeddings = embedding_pipeline.embed_batch(texts)

    assert len(embeddings) == 3
    assert all(len(e) == 768 for e in embeddings)

def test_chunk_text(embedding_pipeline):
    """Test text chunking."""
    text = " ".join(["word"] * 1000)
    chunks = embedding_pipeline.chunk_text(text, chunk_size=100, overlap=10)

    assert len(chunks) > 1
    assert all(isinstance(c, str) for c in chunks)

def test_vector_store_add_and_search(vector_store, embedding_pipeline):
    """Test adding and searching documents."""
    text = "Transformers revolutionized NLP in 2017."
    embedding = embedding_pipeline.embed_single(text)

    vector_store.add_embedding(
        doc_id="test_1",
        embedding=embedding,
        document=text,
        metadata={"source": "test"}
    )

    result = vector_store.get_document("test_1")
    assert result is not None
    assert result["id"] == "test_1"
    assert result["document"] == text
