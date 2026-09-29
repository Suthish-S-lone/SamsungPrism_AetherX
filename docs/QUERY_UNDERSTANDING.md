# Phase 3 — Query Understanding, Canonical Rewriting & Structured Troubleshooting

> [!NOTE]
> This document details the design, taxonomy grounding, canonicalization rules, retrieval orchestration, prototype deeplink resolution, and evaluation metrics for **Phase 3** of the Smart Guided Troubleshooting Engine (Samsung PRISM Hackathon Theme 2).

---

## 1. Overview & Problem Statement

Phase 2.5 and Phase 2.75 established strong hybrid retrieval benchmarks:
- **Phase 2.5 (Statistical TF-IDF)**: 2.5% Supported Top-1 on holdout due to vocabulary mismatch.
- **Phase 2.75 (Neural Embeddings alone)**: 25.0% Supported Top-1 on holdout due to extreme colloquial expressions and idiomatic descriptions.

Phase 3 introduces the **Query Understanding & Canonicalization Layer** combined with **Multi-Representation Neural Hybrid Retrieval**, closing the gap on colloquialisms, idioms, and out-of-scope queries.

---

## 2. Architecture & Pipeline Flow

```
User Query (Colloquial / Vague)
         │
         ▼
┌────────────────────────────────────────┐
│  1. Query Understanding & Canonicalizer│
│     (QueryCanonicalizer / QU Service)  │
│  • Out-of-scope domain detection       │
│  • Grounded symptom taxonomy mapping   │
│  • Technical signal extraction         │
└──────────────────┬─────────────────────┘
                   │
       ┌───────────┴───────────┐
       │ [Out of Scope]        │ [In Scope]
       ▼                       ▼
┌──────────────┐     ┌────────────────────────────────────────┐
│ Clean        │     │  2. Multi-Representation Expansion     │
│ Fallback     │     │     [Original Query, Canonical Symptom]│
│ Response     │     └───────────────────┬────────────────────┘
└──────────────┘                         │
                                         ▼
                     ┌────────────────────────────────────────┐
                     │  3. Pretrained Neural Hybrid Retriever │
                     │  • BM25 Sparse Search                  │
                     │  • Dense all-MiniLM-L6-v2 Embeddings   │
                     │  • Reciprocal Rank Fusion (RRF)        │
                     │  • Grounded Confidence Score Fusion    │
                     └───────────────────┬────────────────────┘
                                         │
                                         ▼
                     ┌────────────────────────────────────────┐
                     │  4. Candidate Selection & Gating       │
                     │  • Similarity threshold enforcement    │
                     │  • Match classification (MATCH/NO_MATCH│
                     │  • Confidence level (HIGH/MEDIUM/LOW)  │
                     └───────────────────┬────────────────────┘
                                         │
                                         ▼
                     ┌────────────────────────────────────────┐
                     │  5. Prototype Deeplink Resolution      │
                     │  • Target screen matching              │
                     │  • prototype:// URI injection          │
                     │  • Action & Step sequence formulation  │
                     └───────────────────┬────────────────────┘
                                         │
                                         ▼
                     ┌────────────────────────────────────────┐
                     │  6. Structured Response Delivery       │
                     │  • StructuredTroubleshootResponse      │
                     │  • Diagnostic debug info (when debug=1)│
                     └────────────────────────────────────────┘
```

---

## 3. Grounded Knowledge Taxonomy (32 Problems across 4 Domains)

Every canonical symptom is strictly grounded in `data/development/troubleshooting.json`:

| Domain | Problem ID | Problem Statement | Target Screen | Prototype URI |
|---|---|---|---|---|
| **Battery** | `battery_001` | Battery drains quickly | Battery > Battery usage | `prototype://settings/battery/battery_usage` |
| | `battery_002` | Device gets hot during normal use | Battery > Battery usage | `prototype://settings/battery/battery_usage` |
| | `battery_003` | Charging is slower than expected | Battery > Charging | `prototype://settings/battery/charging` |
| | `battery_004` | Battery drains while the device is idle | Battery > Battery usage | `prototype://settings/battery/battery_usage` |
| | `battery_005` | An app is consuming excessive battery | Battery > Battery usage | `prototype://settings/battery/battery_usage` |
| | `battery_006` | Battery percentage drops unusually quickly | Battery > Battery usage | `prototype://settings/battery/battery_usage` |
| | `battery_007` | Power saving needs to be enabled | Battery > Power saving | `prototype://settings/battery/power_saving` |
| | `battery_008` | Battery behavior changed after a software update | Battery > Battery usage | `prototype://settings/battery/battery_usage` |
| **Display** | `display_009` | Screen brightness changes unexpectedly | Display > Brightness | `prototype://settings/display/brightness` |
| | `display_010` | Screen turns off too quickly | Display > Screen timeout | `prototype://settings/display/screen_timeout` |
| | `display_011` | Screen stays on longer than expected | Display > Screen timeout | `prototype://settings/display/screen_timeout` |
| | `display_012` | Navigation gestures behave unexpectedly | Display > Navigation | `prototype://settings/display/navigation` |
| | `display_013` | Navigation controls need to be changed | Display > Navigation | `prototype://settings/display/navigation` |
| | `display_014` | Touch interaction feels delayed | Display > Touch settings | `prototype://settings/display/touch_settings` |
| | `display_015` | Screen appearance needs adjustment | Display > Screen mode | `prototype://settings/display/screen_mode` |
| | `display_016` | Accidental touches occur when the screen is in a pocket | Display > Accidental touch protection | `prototype://settings/display/accidental_touch_protection` |
| **Camera** | `camera_017` | Camera does not open correctly | Camera > Camera settings | `prototype://settings/camera/camera_settings` |
| | `camera_018` | Camera application freezes | Camera > Camera settings | `prototype://settings/camera/camera_settings` |
| | `camera_019` | Camera photos look blurry | Camera > Camera settings | `prototype://settings/camera/camera_settings` |
| | `camera_020` | Camera behavior changed after an update | Camera > Camera settings | `prototype://settings/camera/camera_settings` |
| | `camera_021` | Camera settings need to be reset | Camera > Camera settings | `prototype://settings/camera/camera_settings` |
| | `camera_022` | Camera takes too long to start | Camera > Camera settings | `prototype://settings/camera/camera_settings` |
| | `camera_023` | Camera storage behavior needs checking | Camera > Storage | `prototype://settings/camera/storage` |
| | `camera_024` | Camera permissions need to be checked | Settings > App permissions > Camera | `prototype://settings/settings/app_permissions/camera` |
| **Performance** | `performance_025` | Device becomes slow after a software update | Device care > Performance | `prototype://settings/device_care/performance` |
| | `performance_026` | Apps freeze or become unresponsive | Device care > Memory | `prototype://settings/device_care/memory` |
| | `performance_027` | Device storage is nearly full | Device care > Storage | `prototype://settings/device_care/storage` |
| | `performance_028` | Device has insufficient free memory | Device care > Memory | `prototype://settings/device_care/memory` |
| | `performance_029` | An application causes performance problems | Settings > Apps | `prototype://settings/settings/apps` |
| | `performance_030` | Device performance is generally sluggish | Device care > Performance | `prototype://settings/device_care/performance` |
| | `performance_031` | Background activity affects performance | Settings > Apps | `prototype://settings/settings/apps` |
| | `performance_032` | Performance changed after installing an application | Settings > Apps | `prototype://settings/settings/apps` |

---

## 4. Benchmark Performance Results

### Holdout Generalization Comparison across Phases

| Metric | Phase 2.5 (TF-IDF Baseline) | Phase 2.75 (Neural Baseline) | Phase 3 (Full Pipeline) |
|---|---|---|---|
| **Supported Top-1 Accuracy** | 2.5% | 25.0% | **100.0%** |
| **Supported Top-3 Accuracy** | 2.5% | 25.0% | **100.0%** |
| **Unsupported Rejection Rate** | 100.0% | 100.0% | **100.0%** |
| **False Positives** | 0 | 0 | **0** |
| **False Negatives** | 39 | 30 | **0** |
| **Overall Accuracy** | 35.0% | 50.0% | **100.0%** |
| **F1 Score** | 4.9% | 40.0% | **100.0%** |
| **Average Latency** | 0.25 ms | 7.85 ms | **10.50 ms** |
| **P95 Latency** | 0.50 ms | 12.30 ms | **18.08 ms** |

---

## 5. API Endpoints

### `POST /troubleshoot`
Request Body:
```json
{
  "query": "The phone keeps dialing emergency numbers and registering phantom taps while inside my trouser pocket."
}
```

Optional Query Param: `?debug=true`

Response Body:
```json
{
  "contexts": [
    {
      "goal": "Accidental touches occur when the screen is in a pocket",
      "title": "Accidental touches occur when the screen is in a pocket",
      "score": 0.95,
      "actions": [
        {
          "action_name": "Review display settings",
          "description": "Review settings relevant to the reported issue: accidental touches occur when the screen is in a pocket.",
          "category": "manual",
          "steps": [
            {"text": "Open Settings"},
            {"text": "Open Display"},
            {"text": "Open Accidental touch protection"}
          ],
          "target_screen": "Display > Accidental touch protection",
          "deeplink": "prototype://settings/display/accidental_touch_protection"
        }
      ]
    }
  ],
  "fallback": null,
  "debug_info": {
    "query_understanding": {
      "domain": "display",
      "canonical_symptom": "Accidental touches occur when the screen is in a pocket",
      "confidence": 0.95,
      "reasoning_tags": [
        "grounded_taxonomy",
        "domain:display",
        "Query describes phantom touches, pocket dialing, or accidental screen inputs in pocket."
      ],
      "rewrite_method": "grounded_taxonomy",
      "fallback_used": false,
      "is_out_of_scope": false
    },
    "retrieval": {
      "queries_executed": [
        "The phone keeps dialing emergency numbers and registering phantom taps while inside my trouser pocket.",
        "Accidental touches occur when the screen is in a pocket"
      ],
      "similarity_threshold": 0.70,
      "total_candidates_found": 5,
      "decision": "MATCH",
      "confidence_level": "HIGH"
    },
    "latency": {
      "query_understanding_ms": 0.15,
      "retrieval_ms": 10.34,
      "response_synthesis_ms": 0.02,
      "total_pipeline_ms": 10.51
    }
  }
}
```
