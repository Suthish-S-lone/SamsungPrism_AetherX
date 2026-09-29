# SmartGuide Engine Architecture

> [!NOTE]
> This document details the architectural layout of the **Smart Guided Troubleshooting Engine** (Samsung PRISM Hackathon Theme 2). 
> **Phase 1** (Foundation & Schemas), **Phase 2** (Hybrid Retrieval & Indexing), **Phase 2.75** (Pretrained Neural Semantic Embeddings Upgrade), and **Phase 3** (Query Understanding, Canonical Rewriting & Structured Troubleshooting) are fully implemented and verified.

---

## 1. End-to-End Pipeline Architecture

```
User Complaint / Query
         │
         ▼
┌─────────────────────────────────────────┐
│ 1. Query Understanding & Canonicalizer  │  [Implemented - Phase 3]
│    (backend/app/services/canonicalizer) │  • Out-of-scope domain detection
│    (backend/app/services/query_under...)│  • Knowledge-base grounded taxonomy
│                                         │  • Signal extraction & canonical rewriting
└────────────────────┬────────────────────┘
                     │
       ┌─────────────┴─────────────┐
       │ [Out of Scope]            │ [In Scope]
       ▼                           ▼
┌──────────────┐     ┌─────────────────────────────────────────┐
│ Rejection /  │     │ 2. Multi-Representation Expansion       │  [Implemented - Phase 3]
│ Fallback     │     │    [Original Query, Canonical Symptom]  │
│ Response     │     └────────────────────┬────────────────────┘
└──────────────┘                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │ 3. Pretrained Neural Hybrid Retriever   │  [Implemented - Phase 2 & 2.75]
                     │    (backend/app/retrieval/)             │  • BM25 Sparse Search (Field-weighted)
                     │                                         │  • Pretrained Neural Dense Search (all-MiniLM-L6-v2)
                     │                                         │  • Reciprocal Rank Fusion (RRF, k=60)
                     │                                         │  • Confidence Gating (MATCH / NO_MATCH)
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │ 4. Prototype Deeplink Resolution Engine │  [Implemented - Phase 3]
                     │    (backend/app/services/troubleshoot.) │  • Target screen matching (deeplinks.json)
                     │                                         │  • prototype:// URI resolution
                     │                                         │  • Action & Step sequence formulation
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │ 5. Structured Response Synthesis        │  [Implemented - Phase 3]
                     │    (StructuredTroubleshootResponse)     │  • Contexts, Actions, Steps, Deeplinks
                     │                                         │  • Diagnostic Transparency Payload (debug=True)
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │ 6. REST API Delivery                    │  [FastAPI POST /troubleshoot]
                     │    (FastAPI / Uvicorn)                  │  [FastAPI GET /health]
                     └─────────────────────────────────────────┘
```

---

## 2. Phase Implementation Status

| Stage | Module | Status | Description |
|---|---|---|---|
| **Schemas & Models** | `backend/app/models/` | **Done (Phase 1)** | Pydantic data models, request validation, prototype response schema. |
| **Data Inspection** | `scripts/inspect_data.py` | **Done (Phase 1)** | Automated schema and referential integrity validator. |
| **Query Preprocessing** | `backend/app/retrieval/preprocessing.py` | **Done (Phase 2)** | Whitespace, case, conversational wrapper removal, protected term preservation. |
| **BM25 Retriever** | `backend/app/retrieval/bm25_retriever.py` | **Done (Phase 2)** | Lexical BM25Okapi search over field-weighted corpus. |
| **Neural Dense Retriever** | `backend/app/retrieval/semantic_retriever.py` | **Done (Phase 2.75)** | Pretrained `sentence-transformers/all-MiniLM-L6-v2` local embedding provider. |
| **Score Fusion & Gating** | `backend/app/retrieval/scoring.py` | **Done (Phase 2)** | Reciprocal Rank Fusion (RRF), calibrated confidence scoring, MATCH/NO_MATCH gating. |
| **Query Understanding** | `backend/app/services/canonicalizer.py` | **Done (Phase 3)** | Taxonomy grounding, colloquial symptom canonicalization, out-of-scope filtering. |
| **Troubleshooting Engine** | `backend/app/services/troubleshooting_service.py` | **Done (Phase 3)** | Multi-representation retrieval, prototype deeplink resolution, and transparency debug metadata. |
| **REST API Engine** | `backend/app/main.py` | **Done (Phase 3)** | `POST /troubleshoot` and `GET /health` FastAPI endpoints. |
| **Benchmark Evaluators** | `scripts/evaluate_phase3.py` | **Done (Phase 3)** | Full pipeline benchmark across development (72) and holdout (60) datasets. |
