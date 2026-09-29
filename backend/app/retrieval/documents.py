"""Retrieval document representations and document builder.

Constructs rich, field-weighted searchable document representations for each
troubleshooting record, merging problem statements, keywords, and semantic variations
while explicitly excluding generic action boilerplate.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.models.data_models import TroubleshootingRecord
from backend.app.retrieval.preprocessing import normalize_whitespace, tokenize


class RetrievalDocument(BaseModel):
    """Search-optimized representation of a troubleshooting problem."""

    problem_id: str = Field(..., description="Troubleshooting problem ID")
    domain: str = Field(..., description="Problem domain category")
    problem: str = Field(..., description="Canonical problem statement")
    description: str = Field(..., description="Detailed description")
    keywords: List[str] = Field(default_factory=list, description="Associated keywords")
    query_variations: List[str] = Field(default_factory=list, description="Semantic variation queries")
    searchable_text: str = Field(..., description="Consolidated natural text for semantic embeddings")
    weighted_text: str = Field(..., description="Field-weighted text for lexical/BM25 indexing")
    tokens: List[str] = Field(default_factory=list, description="Pre-tokenized weighted tokens for BM25")
    raw_record: Optional[TroubleshootingRecord] = Field(
        default=None, description="Original troubleshooting record"
    )


class DocumentBuilder:
    """Loads raw development JSON assets and builds retrieval documents."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self._documents: Dict[str, RetrievalDocument] = {}
        self._load_and_build()

    def _load_and_build(self) -> None:
        """Load troubleshooting and query variation JSON files and construct documents."""
        troubleshooting_path = self.data_dir / "troubleshooting.json"
        variations_path = self.data_dir / "query_variations.json"

        if not troubleshooting_path.exists():
            raise FileNotFoundError(f"Missing troubleshooting data: {troubleshooting_path}")

        with open(troubleshooting_path, "r", encoding="utf-8") as f:
            raw_troubleshooting = json.load(f)

        variations_by_id: Dict[str, List[str]] = {}
        if variations_path.exists():
            with open(variations_path, "r", encoding="utf-8") as f:
                raw_variations = json.load(f)
                for item in raw_variations:
                    variations_by_id[item["problem_id"]] = item.get("query_variations", [])

        for raw in raw_troubleshooting:
            tb_record = TroubleshootingRecord.model_validate(raw)
            p_id = tb_record.id
            variations = variations_by_id.get(p_id, [])

            # Construct clean searchable natural text (for dense embedding)
            # Prioritizes: Problem -> Keywords -> Variations -> Description
            kw_str = ", ".join(tb_record.keywords)
            var_str = ". ".join(variations)
            searchable_text = normalize_whitespace(
                f"{tb_record.problem}. Domain: {tb_record.domain}. "
                f"Keywords: {kw_str}. "
                f"Variations: {var_str}. "
                f"Details: {tb_record.description}"
            )

            # Construct field-weighted text for BM25 tokenization
            # Problem (weight 3x), Keywords (weight 2x), Variations (weight 2x), Description (weight 1x)
            # Boilerplate action descriptions are omitted to avoid lexical noise.
            weighted_parts = (
                [tb_record.problem] * 3
                + tb_record.keywords * 2
                + variations * 2
                + [tb_record.description]
            )
            weighted_text = normalize_whitespace(" ".join(weighted_parts))
            tokens = tokenize(weighted_text, remove_stopwords=True)

            doc = RetrievalDocument(
                problem_id=p_id,
                domain=tb_record.domain,
                problem=tb_record.problem,
                description=tb_record.description,
                keywords=tb_record.keywords,
                query_variations=variations,
                searchable_text=searchable_text,
                weighted_text=weighted_text,
                tokens=tokens,
                raw_record=tb_record,
            )
            self._documents[p_id] = doc

    @property
    def documents(self) -> List[RetrievalDocument]:
        """Return list of all built retrieval documents."""
        return list(self._documents.values())

    def get_document(self, problem_id: str) -> Optional[RetrievalDocument]:
        """Get document by problem ID."""
        return self._documents.get(problem_id)
