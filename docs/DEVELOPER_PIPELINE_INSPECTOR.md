# Developer Diagnostic Pipeline Inspector

## Overview

The **Developer Diagnostic Pipeline Inspector** is an optional evaluation and debugging interface built into SmartGuide. It enables evaluators, judges, and developers to inspect how queries are transformed, understood, retrieved, ranked, and resolved by the underlying AI engine without cluttering or compromising the clean Samsung One UI consumer experience.

> [!NOTE]
> The Developer Pipeline Inspector is **hidden by default**. The default consumer journey remains:
> `Landing → Start Troubleshooting → Describe Issue → Loading → Clarification (if needed) → Diagnosis → Guided Fix → Resolution`.

---

## 1. How to Enable / Disable Developer Mode

### Enabling Developer Inspection
1. Navigate past the Landing screen by clicking **"Start Troubleshooting"**, selecting a **Category Card**, or picking an **Example Scenario**.
2. In the top-right header actions bar, click the **"Inspect"** button (identified with a terminal icon `Terminal`).
3. The **Diagnostic Pipeline Inspector** will immediately render below the active troubleshooting view.

### Disabling / Closing Developer Mode
- Click the **"Inspect"** button again in the top-right header actions bar, OR
- Click the **"X"** (close) icon directly in the Inspector header bar, OR
- Click **"Collapse"** to minimize the inspector content while keeping developer mode active.

---

## 2. Technical Sections & Diagnostic Telemetry

When developer mode is active, the inspector surfaces live telemetry from the backend:

### A. Multi-Turn Session Status Bar
- **Turn Counter**: Displays current turn index vs maximum allowed turns (`turn_count / max_turns`, e.g. `1 / 3` or `2 / 3`).
- **Session State**: Explicit diagnostic state machine status (`diagnosis_ready`, `clarification_required`, `insufficient_information`, `out_of_scope`, `unsupported`).
- **Session ID**: Active multi-turn UUID tracking user clarification context.

### B. Core Metrics Grid
- **Query Understanding**: Domain classification (e.g. `BATTERY`, `DISPLAY`, `CAMERA`, `PERFORMANCE`) with confidence percentage and canonical rewrite method (`domain_conditioned_canon`, `direct`, `fallback`).
- **Decision Gating**: Retrieval decision status (`MATCH`, `CLARIFY`, `REJECT`), confidence classification (`HIGH`, `MEDIUM`, `LOW`), and the active cosine similarity gating threshold (default `0.40`).
- **Inference Latency Breakdown**: End-to-end total pipeline latency in milliseconds alongside per-stage timings:
  - `QU`: Query Understanding & Intent extraction
  - `Ret`: Hybrid Retrieval (BM25 + Semantic dense vector search + RRF)
  - `Syn`: Diagnostic context assembly & Deeplink resolution

### C. Query Transformation & Canonicalization
- **Original User Query**: Verbatim colloquial input submitted by the user.
- **Canonical Symptom Formulation**: Normalized technical symptom mapping used for retrieval.
- **Extracted Signals & Reasoning Tags**: Semantic tags identified by query understanding (e.g. `[symptom:overheating]`, `[thermal:high_temp]`, `[subsystem:battery]`).

### D. Resolved Problem & Knowledge Base Match
- **Selected Problem Statement**: Official title of the matched troubleshooting entry.
- **Problem ID / Goal**: Canonical identifier matching the knowledge base schema.
- **Match Confidence**: Final composite ranking confidence score.

### E. Hybrid Retrieval Candidates Table
Displays top ranked candidate entries with comparative retrieval metrics:
- **Problem ID**: Unique record ID.
- **Problem Statement**: Diagnostic issue title.
- **Fused RRF**: Reciprocal Rank Fusion composite score combining sparse and dense ranks:
  $$\text{RRF Score} = \frac{1}{60 + \text{Rank}_{\text{BM25}}} + \frac{1}{60 + \text{Rank}_{\text{Semantic}}}$$
- **BM25 Rank**: Sparse lexical rank.
- **Semantic Rank**: Dense vector semantic rank computed using `sentence-transformers/all-MiniLM-L6-v2`.

### F. Multi-Turn Clarification History
When resolving ambiguous symptoms (such as thermal or charging ambiguity), displays the chronological sequence of clarification turns:
- Turn number
- Question presented
- Option selected or custom user description provided

### G. Collapsible Raw JSON Viewer
- Expandable raw JSON viewer displaying the complete backend `StructuredTroubleshootResponse` payload.
- One-click **"Copy JSON"** button with clipboard verification feedback.

---

## 3. Single-Turn vs Multi-Turn Behavior

| Workflow | Inspector Behavior |
|---|---|
| **Single-Turn Diagnosis** (e.g. *"My battery drains really fast"*) | Immediately presents Top-1 matched record, fused RRF score, latency breakdown, and canonical symptom mapping. |
| **Multi-Turn Clarification** (e.g. *"My phone gets really hot"*) | Turn 1 displays `clarification_required` state, decision `CLARIFY`, generated candidate questions, and active Session ID. As the user selects an option (e.g. *"While fast charging"*), Turn 2 updates with refined candidate rankings, final problem ID, and turn history. |

---

## 4. API Response Fields Used

The Inspector reads real backend data returned by the `/troubleshoot` and `/troubleshoot/continue` endpoints:

```typescript
interface DiagnosticDebugMetadata {
  query_understanding: {
    original_query: string;
    normalized_query: string;
    domain: string | null;
    canonical_symptom: string | null;
    target_problem_id: string | null;
    extracted_signals: string[];
    confidence: number;
    reasoning_tags: string[];
    rewrite_method: string;
    fallback_used: boolean;
    is_out_of_scope: boolean;
  };
  retrieval: {
    queries_executed: string[];
    similarity_threshold: number;
    total_candidates_found: number;
    top_candidates: CandidateDebugInfo[];
    decision: string;
    confidence_level: string;
  };
  latency: {
    query_understanding_ms: number;
    retrieval_ms: number;
    response_synthesis_ms: number;
    total_pipeline_ms: number;
  };
}
```

---

## 5. Security & Isolation Boundaries

- **No Secrets Exposed**: The inspector never accesses or renders API keys, tokens, environment variables, or local filesystem paths.
- **No Mock or Fabricated Data**: All metrics, rankings, and latencies displayed are dynamically parsed from the active backend API session.
- **No Performance Impact**: Debug payload generation adds negligible compute latency (< 1ms) and runs entirely in local memory.
