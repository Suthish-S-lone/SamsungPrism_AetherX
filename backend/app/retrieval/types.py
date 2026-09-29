"""Data types and schemas for the retrieval engine."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class RetrievalCandidate(BaseModel):
    """An intermediate candidate returned by an individual retriever (BM25 or Semantic)."""

    problem_id: str = Field(..., description="Troubleshooting problem identifier")
    domain: str = Field(..., description="Problem domain category")
    score: float = Field(..., description="Raw or normalized retrieval score")
    rank: int = Field(..., description="Rank in the individual retriever results (1-indexed)", ge=1)


class RetrievalResult(BaseModel):
    """Structured result from the Hybrid Retrieval Engine."""

    problem_id: str = Field(..., description="Matched problem ID")
    domain: str = Field(..., description="Domain category of the problem")
    problem: str = Field(..., description="Canonical problem statement")
    score: float = Field(..., description="Confidence or normalized similarity score", ge=0.0, le=1.0)
    bm25_rank: Optional[int] = Field(default=None, description="BM25 rank if present in BM25 top-k")
    semantic_rank: Optional[int] = Field(default=None, description="Semantic rank if present in vector top-k")
    fused_score: float = Field(..., description="Reciprocal rank fusion combined score")
    matched_keywords: List[str] = Field(default_factory=list, description="Keywords matching query tokens")
    retrieval_method: str = Field(default="hybrid", description="Retrieval method used ('hybrid', 'bm25', 'semantic')")
    status: Literal["MATCH", "NO_MATCH"] = Field(
        default="MATCH", description="Confidence gate status based on similarity threshold"
    )


class QueryEvaluationResult(BaseModel):
    """Evaluation result for a single benchmark query."""

    query_id: str = Field(..., description="Test query identifier")
    query: str = Field(..., description="Query text evaluated")
    expected_domain: Optional[str] = Field(default=None, description="Expected domain or None")
    expected_problem_id: Optional[str] = Field(default=None, description="Expected problem ID or None")
    predicted_problem_id: Optional[str] = Field(default=None, description="Predicted problem ID or None")
    correct: bool = Field(..., description="Whether prediction matches ground truth")
    rank: Optional[int] = Field(default=None, description="Rank where target was found")
    score: float = Field(..., description="Confidence score")
    status: Literal["MATCH", "NO_MATCH"] = Field(..., description="Retrieval match classification")
    latency_ms: float = Field(..., description="Query execution latency in milliseconds")


class EvaluationMetrics(BaseModel):
    """Aggregate benchmark evaluation metrics."""

    total_queries: int = Field(..., description="Total queries evaluated")
    supported_queries: int = Field(..., description="Supported domain queries count")
    unsupported_queries: int = Field(..., description="Unsupported / out-of-scope queries count")
    top_1_accuracy: float = Field(..., description="Top-1 accuracy percentage")
    top_3_accuracy: float = Field(..., description="Top-3 accuracy / recall percentage")
    supported_accuracy: float = Field(..., description="Accuracy on supported queries percentage")
    unsupported_rejection_rate: float = Field(..., description="Rejection rate for unsupported queries percentage")
    false_positives: int = Field(..., description="Unsupported queries falsely classified as MATCH")
    false_negatives: int = Field(..., description="Supported queries rejected as NO_MATCH or misclassified")
    average_latency_ms: float = Field(..., description="Average per-query latency in milliseconds")
    threshold: float = Field(..., description="Confidence similarity threshold applied")
    per_query_results: List[QueryEvaluationResult] = Field(default_factory=list)
