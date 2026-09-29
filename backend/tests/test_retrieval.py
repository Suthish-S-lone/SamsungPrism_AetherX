"""Unit tests for Phase 2: Hybrid Retrieval & Indexing.

Tests cover:
- Query preprocessing and conversational wrapper removal
- BM25 lexical indexing and retrieval
- Dense semantic vector indexing and cosine similarity search
- Hybrid retrieval with Reciprocal Rank Fusion (RRF)
- Confidence gating and NO_MATCH detection for unsupported queries
- Benchmark evaluator and threshold sweep
"""

import pytest
import numpy as np

from backend.app.retrieval.bm25_retriever import BM25Retriever
from backend.app.retrieval.documents import DocumentBuilder, RetrievalDocument
from backend.app.retrieval.evaluator import RetrievalEvaluator
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.retrieval.preprocessing import (
    normalize_whitespace,
    preprocess_query,
    strip_conversational_wrappers,
    tokenize,
)
from backend.app.retrieval.scoring import ReciprocalRankFusion
from backend.app.retrieval.semantic_retriever import (
    LocalDenseEmbeddingProvider,
    SemanticRetriever,
    VectorIndex,
)
from backend.app.retrieval.types import RetrievalCandidate


@pytest.fixture(scope="module")
def documents():
    """Build and provide all development retrieval documents."""
    builder = DocumentBuilder()
    return builder.documents


@pytest.fixture(scope="module")
def hybrid_retriever(documents):
    """Provide initialized hybrid retriever instance."""
    return HybridRetriever(documents=documents, similarity_threshold=0.70)


# ==============================================================================
# 1. Preprocessing Tests
# ==============================================================================

def test_preprocessing_whitespace_normalization():
    """Test whitespace normalization cleans tabs, newlines, and multiple spaces."""
    raw = "   battery   \n\t  drains    fast   "
    cleaned = normalize_whitespace(raw)
    assert cleaned == "battery drains fast"


def test_preprocessing_case_normalization():
    """Test query preprocessing lowercases input text."""
    raw = "BATTERY Drains Quickly"
    cleaned = preprocess_query(raw)
    assert cleaned == "battery drains quickly"


def test_preprocessing_conversational_wrapper_handling():
    """Test conversational wrapper removal retains core troubleshooting terms."""
    queries = [
        ("Why is my phone having this problem: battery drains quickly?", "battery drains quickly"),
        ("Why does my phone screen turn off too quickly?", "screen turn off too quickly"),
        ("How to fix camera app crashing when zooming", "camera app crashing when zooming"),
        ("Help with slow charging on device", "slow charging on device"),
        ("Troubleshoot overheating during gaming", "overheating during gaming"),
    ]
    for raw, expected in queries:
        processed = preprocess_query(raw)
        assert processed == expected, f"Failed for raw query: {raw}"


def test_preprocessing_protected_terms_preserved():
    """Ensure key device terms are not discarded during tokenization."""
    text = "Battery charging and screen brightness issue with slow memory lag"
    tokens = tokenize(text, remove_stopwords=True)
    for term in ["battery", "charging", "screen", "brightness", "slow", "memory", "lag"]:
        assert term in tokens, f"Expected protected term '{term}' in tokens"


# ==============================================================================
# 2. Document Representation Tests
# ==============================================================================

def test_document_builder_builds_all_records(documents):
    """Test that all 32 troubleshooting problems are converted into retrieval documents."""
    assert len(documents) == 32
    problem_ids = {doc.problem_id for doc in documents}
    assert "battery_001" in problem_ids
    assert "performance_032" in problem_ids

    for doc in documents:
        assert len(doc.searchable_text) > 20
        assert len(doc.tokens) > 5
        assert len(doc.keywords) >= 1
        assert len(doc.query_variations) >= 1


# ==============================================================================
# 3. BM25 Retriever Tests
# ==============================================================================

def test_bm25_index_and_retrieval(documents):
    """Test BM25 index builds, retrieves top candidates, and returns valid problem IDs."""
    bm25 = BM25Retriever(documents)
    results = bm25.retrieve("battery drains quickly", top_k=5)

    assert len(results) > 0
    top_cand, matched_kw = results[0]
    assert top_cand.problem_id == "battery_001"
    assert top_cand.domain == "battery"
    assert top_cand.rank == 1
    assert top_cand.score > 0
    assert len(matched_kw) > 0


def test_bm25_top_k_configurable(documents):
    """Test BM25 respects configurable top_k parameter."""
    bm25 = BM25Retriever(documents)
    results_3 = bm25.retrieve("camera focus blurry", top_k=3)
    results_7 = bm25.retrieve("camera focus blurry", top_k=7)

    assert len(results_3) == 3
    assert len(results_7) <= 7


# ==============================================================================
# 4. Dense Semantic Retriever Tests
# ==============================================================================

def test_semantic_embedding_generation(documents):
    """Test local embedding provider produces normalized 1D and 2D vectors."""
    texts = [doc.searchable_text for doc in documents]
    provider = LocalDenseEmbeddingProvider(corpus=texts)

    vec = provider.embed_text("battery drains quickly")
    assert isinstance(vec, np.ndarray)
    assert vec.ndim == 1
    assert vec.shape[0] == provider.dimension
    # L2 norm should be 1.0 (or 0.0 if empty)
    assert np.isclose(np.linalg.norm(vec), 1.0, atol=1e-4)

    matrix = provider.embed_documents(texts[:5])
    assert matrix.shape == (5, provider.dimension)


def test_sentence_transformer_embedding_provider():
    """Test pretrained SentenceTransformer embedding provider loads and embeds."""
    from backend.app.retrieval.semantic_retriever import (
        SentenceTransformerEmbeddingProvider,
        get_embedding_provider,
    )

    provider = get_embedding_provider(mode="sentence_transformer")
    assert isinstance(provider, SentenceTransformerEmbeddingProvider)
    assert provider.dimension == 384
    assert "MiniLM" in provider.model_name

    vec = provider.embed_text("Phone battery drains quickly during gaming")
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (384,)
    assert np.isclose(np.linalg.norm(vec), 1.0, atol=1e-3)

    texts = [
        "Battery drains quickly",
        "Device gets hot during normal use",
        "Charging is slower than expected",
    ]
    matrix = provider.embed_documents(texts)
    assert matrix.shape == (3, 384)


def test_sentence_transformer_cosine_similarity(documents):
    """Test semantic vector index with SentenceTransformer embeddings."""
    from backend.app.retrieval.semantic_retriever import (
        SentenceTransformerEmbeddingProvider,
    )

    provider = SentenceTransformerEmbeddingProvider()
    index = VectorIndex(provider)
    index.build(documents)

    q_vec = provider.embed_text("I have to charge my phone several times a day")
    matches = index.search(q_vec, top_k=5)

    assert len(matches) == 5
    top_id, top_score = matches[0]
    # Expected semantic match: battery_001 (Battery drains quickly) or related battery issue
    assert top_id.startswith("battery_")
    assert top_score > 0.40


def test_vector_index_search(documents):
    """Test vector index builds, calculates cosine similarities, and returns top results."""
    provider = LocalDenseEmbeddingProvider(corpus=[doc.searchable_text for doc in documents])
    index = VectorIndex(provider)
    index.build(documents)

    q_vec = provider.embed_text("Device gets hot during normal use")
    matches = index.search(q_vec, top_k=5)

    assert len(matches) == 5
    top_id, top_score = matches[0]
    assert top_id == "battery_002"
    assert 0.0 <= top_score <= 1.0


def test_semantic_retriever_execution(documents):
    """Test SemanticRetriever end-to-end retrieval."""
    sem_retriever = SemanticRetriever(documents)
    results = sem_retriever.retrieve("camera app takes blurry photos in low light", top_k=3)

    assert len(results) == 3
    assert results[0].domain == "camera"
    assert results[0].rank == 1


# ==============================================================================
# 5. Hybrid Retrieval & RRF Fusion Tests
# ==============================================================================

def test_reciprocal_rank_fusion(documents):
    """Test RRF fusion combines dual channels and handles duplicate candidates cleanly."""
    doc_map = {doc.problem_id: doc for doc in documents}
    fusion = ReciprocalRankFusion(rrf_k=60)

    bm25_res = [
        (RetrievalCandidate(problem_id="battery_001", domain="battery", score=12.5, rank=1), ["battery"]),
        (RetrievalCandidate(problem_id="battery_002", domain="battery", score=8.0, rank=2), ["battery"]),
    ]
    sem_res = [
        RetrievalCandidate(problem_id="battery_001", domain="battery", score=0.92, rank=1),
        RetrievalCandidate(problem_id="battery_003", domain="battery", score=0.75, rank=2),
    ]

    fused = fusion.fuse(bm25_res, sem_res, doc_map=doc_map, similarity_threshold=0.70, top_k=5)
    assert len(fused) == 3
    # battery_001 ranked #1 in both channels should be top candidate
    assert fused[0].problem_id == "battery_001"
    assert fused[0].bm25_rank == 1
    assert fused[0].semantic_rank == 1
    assert fused[0].retrieval_method == "hybrid"


def test_hybrid_retriever_end_to_end(hybrid_retriever):
    """Test HybridRetriever executes dual search and returns structured results."""
    results = hybrid_retriever.retrieve("Battery drains quickly while gaming", top_k=3)
    assert len(results) == 3
    top = results[0]
    assert top.domain == "battery"
    assert top.problem_id in ["battery_001", "battery_002"]
    assert 0.0 <= top.score <= 1.0
    assert top.status in ["MATCH", "NO_MATCH"]


# ==============================================================================
# 6. Confidence Gating & NO_MATCH Tests
# ==============================================================================

def test_supported_query_returns_match(hybrid_retriever):
    """Test valid supported complaint returns MATCH status."""
    res = hybrid_retriever.retrieve_best("Screen brightness changes unexpectedly")
    assert res is not None
    assert res.status == "MATCH"
    assert res.domain == "display"


def test_unsupported_query_returns_no_match(hybrid_retriever):
    """Test absurd / out-of-scope query produces NO_MATCH."""
    unsupported_query = "The device should automatically cook my food."
    res = hybrid_retriever.retrieve_best(unsupported_query, threshold=0.70)
    assert res is not None
    assert res.status == "NO_MATCH"


def test_threshold_enforcement(hybrid_retriever):
    """Test that adjusting threshold changes MATCH / NO_MATCH classification."""
    query = "Somewhat vague issue with phone"
    # Under strict threshold, should be NO_MATCH
    res_strict = hybrid_retriever.retrieve_best(query, threshold=0.95)
    assert res_strict is None or res_strict.status == "NO_MATCH"


# ==============================================================================
# 7. Benchmark Evaluator Tests
# ==============================================================================

def test_evaluator_runs_and_calculates_metrics(hybrid_retriever):
    """Test RetrievalEvaluator computes complete benchmark metrics."""
    evaluator = RetrievalEvaluator(retriever=hybrid_retriever)
    metrics = evaluator.evaluate(threshold=0.70)

    assert metrics.total_queries == 72
    assert metrics.supported_queries == 64
    assert metrics.unsupported_queries == 8
    assert metrics.top_1_accuracy >= 95.0
    assert metrics.top_3_accuracy >= 95.0
    assert metrics.supported_accuracy >= 95.0
    assert metrics.unsupported_rejection_rate >= 90.0
    assert metrics.average_latency_ms < 100.0  # sub-100ms requirement


def test_evaluator_threshold_experiment(hybrid_retriever):
    """Test evaluator threshold sweep produces comparison metrics across thresholds."""
    evaluator = RetrievalEvaluator(retriever=hybrid_retriever)
    sweep = evaluator.run_threshold_experiment([0.50, 0.70, 0.90])

    assert len(sweep) == 3
    threshold_vals = [s["threshold"] for s in sweep]
    assert threshold_vals == [0.50, 0.70, 0.90]

    # Strictest threshold should have lowest false positives
    assert sweep[2]["false_positives"] <= sweep[0]["false_positives"]
