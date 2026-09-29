# SmartGuide Retrieval & Indexing Engine (Phase 2)

> [!NOTE]
> This document details the design, mathematical formulation, components, and evaluation of the **Phase 2 Hybrid Retrieval Engine** implemented for Samsung PRISM Hackathon Theme 2.

---

## 1. Retrieval Pipeline Architecture

```
                 User Natural Language Query
                             │
                             ▼
                 ┌───────────────────────┐
                 │  Query Preprocessing  │
                 │ (Clean, Unwrap, Case) │
                 └───────────┬───────────┘
                             │
             ┌───────────────┴───────────────┐
             │                               │
             ▼                               ▼
  ┌─────────────────────┐         ┌─────────────────────┐
  │   BM25 Lexical      │         │   Dense Semantic    │
  │   Search Index      │         │   Vector Index      │
  │ (Field-Weighted TF) │         │ (Cosine Similarity) │
  └──────────┬──────────┘         └──────────┬──────────┘
             │                               │
             └───────────────┬───────────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │ Reciprocal Rank       │
                 │ Fusion (RRF) & Scoring│
                 └───────────┬───────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │  Confidence Gate &    │
                 │  Threshold Filter     │
                 └───────────┬───────────┘
                             │
                  /─────────────────────\
                 /                       \
           [Score >= θ]             [Score < θ]
               /                           \
              ▼                             ▼
    ┌───────────────────┐         ┌───────────────────┐
    │ MATCH Candidate   │         │ NO_MATCH Fallback │
    │ (Problem Record)  │         │ (Out-of-Scope)    │
    └───────────────────┘         └───────────────────┘
```

---

## 2. Document Construction & Weighting Strategy

Each troubleshooting issue from `data/development/troubleshooting.json` is enriched with its semantic variation cluster from `query_variations.json` to build a `RetrievalDocument`:

### Field Weighting
1. **Canonical Problem Statement** (Weight: `3x`): Direct match anchor.
2. **Keywords** (Weight: `2x`): Core technical terms.
3. **Semantic Query Variations** (Weight: `2x`): Paraphrases, colloquialisms, and common user wording.
4. **Detailed Description** (Weight: `1x`): Problem background context.
5. **Action Metadata Exclusion**: Generic boilerplate (`"Review battery settings"`) is explicitly excluded from the retrieval text to prevent lexical noise and term-frequency distortion across problems sharing target screens.

---

## 3. Query Preprocessing

Implemented in [`backend/app/retrieval/preprocessing.py`](file:///c:/samsung/backend/app/retrieval/preprocessing.py):

- **Whitespace Normalization**: Collapses irregular spacing, tabs, and newlines.
- **Case Normalization**: Converts to standard lowercase representation.
- **Conversational Wrapper Stripping**: Removes non-informative query introductory frames (e.g. `"Why is my phone having this problem:"`, `"Help with"`, `"Troubleshoot"`, `"How to fix"`) using regex patterns without stripping the underlying problem description.
- **Protected Term Guard**: Safeguards core device terminology (`battery`, `charging`, `screen`, `brightness`, `camera`, `freeze`, `slow`, `storage`, `memory`, `navigation`, `gesture`, `lag`, `overheating`, `app`, `crash`) from accidental stop-word filtering.

---

## 4. BM25 Lexical Retriever

Implemented in [`backend/app/retrieval/bm25_retriever.py`](file:///c:/samsung/backend/app/retrieval/bm25_retriever.py):

- Uses `rank_bm25` (BM25Okapi) over the tokenized, field-weighted corpus.
- Ranks candidate documents according to inverse document frequency (IDF) and term frequencies:
  $$\text{Score}(D, Q) = \sum_{q \in Q} \text{IDF}(q) \cdot \frac{f(q, D) \cdot (k_1 + 1)}{f(q, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$
- Returns top-$k$ candidates with corresponding matched keywords.

---

## 5. Pretrained Neural Dense Semantic Retriever & Vector Index (Phase 2.75)

Implemented in [`backend/app/retrieval/semantic_retriever.py`](file:///c:/samsung/backend/app/retrieval/semantic_retriever.py):

- **`EmbeddingProvider` Abstraction**: Clean, decoupled abstract interface enabling seamless swapping between neural and statistical embedding models.
- **`SentenceTransformerEmbeddingProvider` (Default / Active)**:
  - Model: `sentence-transformers/all-MiniLM-L6-v2`
  - Embedding Dimension: `384`
  - Normalization: L2 normalization ($\|\mathbf{v}\|_2 = 1.0$)
  - Operation: Runs 100% locally on CPU via PyTorch with no external API keys or network latency during inference.
  - Per-Query Latency: ~7.5 ms ($P_{50} = 7.28\text{ ms}$, $P_{95} = 8.77\text{ ms}$).
- **`LocalDenseEmbeddingProvider` (Preserved Baseline)**:
  - Deterministic sublinear TF-IDF + word & character n-gram (1–4 gram) statistical vectorizer preserved for backward compatibility and benchmarking.
- **`VectorIndex`**: Stores normalized embedding matrices and metadata, computing cosine similarity via matrix dot product:
  $$\text{CosineSimilarity}(\mathbf{u}, \mathbf{v}) = \mathbf{u} \cdot \mathbf{v}$$
- Supports disk caching (`save()` and `load()`) for instant startup.

---

## 6. Score Fusion: Reciprocal Rank Fusion (RRF)

Implemented in [`backend/app/retrieval/scoring.py`](file:///c:/samsung/backend/app/retrieval/scoring.py):

To combine lexical and semantic rankings without scale bias:
$$\text{RRF}(d) = \frac{w_{\text{bm25}}}{k_{\text{rrf}} + \text{rank}_{\text{bm25}}(d)} + \frac{w_{\text{semantic}}}{k_{\text{rrf}} + \text{rank}_{\text{semantic}}(d)}$$

Where:
- $k_{\text{rrf}} = 60$ (smoothing constant)
- $w_{\text{bm25}} = 1.0$, $w_{\text{semantic}} = 1.0$

### Confidence Score Calibration
A normalized confidence score $\in [0.0, 1.0]$ is computed:
- For candidates appearing in both channels: $\text{Confidence} = 0.5 \cdot \text{NormRRF} + 0.5 \cdot \text{CosineSim}$
- Single-channel candidates receive calibrated penalties.

---

## 7. Confidence Gating & Out-of-Scope Detection (`NO_MATCH`)

- When $\text{Confidence} \ge \theta$, the candidate is returned as `status: "MATCH"`.
- When $\text{Confidence} < \theta$, the candidate is marked as `status: "NO_MATCH"`, signaling the downstream system to invoke fallback handling for out-of-scope or absurd queries (e.g. `"The device should automatically cook my food"`).

---

## 8. Development Benchmark Evaluation & Threshold Sweep

Evaluated against all 72 queries in `data/development/test_queries.json`:

| Threshold ($\theta$) | Top-1 Acc | Top-3 Acc | Supp. Acc (64 Qs) | Unsupp. Rej (8 Qs) | False Pos | False Neg | F1 Score | Latency |
|---|---|---|---|---|---|---|---|---|
| `0.50` | 91.7% | 91.7% | 100.0% | 25.0% | 6 | 0 | 95.5% | 0.32 ms |
| `0.55` | 95.8% | 95.8% | 100.0% | 62.5% | 3 | 0 | 97.7% | 0.26 ms |
| `0.60` | 98.6% | 98.6% | 100.0% | 87.5% | 1 | 0 | 99.2% | 0.23 ms |
| **`0.65`** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **0** | **0** | **100.0%** | **0.27 ms** |
| **`0.70`** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **0** | **0** | **100.0%** | **0.25 ms** |
| **`0.75`** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **0** | **0** | **100.0%** | **0.28 ms** |
| `0.80` | 100.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 100.0% | 0.25 ms |
| `0.85` | 97.2% | 97.2% | 96.9% | 100.0% | 0 | 2 | 98.4% | 0.25 ms |
| `0.90` | 50.0% | 50.0% | 43.8% | 100.0% | 0 | 36 | 60.9% | 0.25 ms |

> [!IMPORTANT]
> **Threshold Calibration Notice**:
> The chosen default threshold ($\theta = 0.70$) yields 100% accuracy and 100% rejection on the development dataset. This threshold is **calibrated specifically on the development dataset** and will be re-calibrated when official Samsung assets are provided.

---

## 9. Current Limitations

1. **Development Dataset Size**: Calibrated on 32 issues across 4 domains. Larger corpora may introduce ambiguity among sub-symptoms requiring cross-encoder re-ranking.
2. **Local Embedding vs Pre-trained Transformers**: The local dense n-gram vectorizer is fast and self-contained; when neural transformer weights (e.g. `all-MiniLM-L6-v2`) are loaded via `EmbeddingProvider`, domain fine-tuning may further enhance nuanced synonym matching.
