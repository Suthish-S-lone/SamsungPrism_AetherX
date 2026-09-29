# SmartGuide Development Dataset

> [!IMPORTANT]
> **DEVELOPMENT / PROTOTYPE ASSETS ONLY**
> This dataset was created solely for building and testing the Phase 1 architectural foundation. It is **NOT** official Samsung data, and the `prototype://` URIs are not real Samsung deeplinks. Do not claim this is Samsung data or replace the URI schemes with vendor schemes.

---

## 1. Overview & Purpose

In developing the **Smart Guided Troubleshooting Engine** for Samsung PRISM Hackathon Theme 2, development begins before the arrival of the official Samsung starter assets. 

To establish robust schemas, testable contracts, and validation pipelines, this synthetic development dataset was created. It provides a concrete foundation for:
- Developing Pydantic data models
- Verifying cross-referencing between problems, actions, deeplinks, and queries
- Benchmarking query parsing and category detection
- Establishing end-to-end integration tests

When official Samsung starter assets are provided, they will drop in and replace the files located under `data/development/` without requiring structural rework of the engine foundation.

---

## 2. Supported Domains

The development dataset covers **4 core device operational domains**:

1. **`battery`** (8 troubleshooting records):
   - Battery drain, overheating during use, slow charging, idle drain, app battery consumption, charging temperature limits, power saving modes, and wireless charging.
2. **`display`** (8 troubleshooting records):
   - Unintended brightness shifts, screen timeout issues, gesture navigation glitches, refresh rate anomalies, blue light filter / Eye Comfort Shield behavior, touch sensitivity, accidental touch protection, and dark mode scheduling.
3. **`camera`** (8 troubleshooting records):
   - Camera app lag, focus failure, blurry photos, flash synchronization, video stabilization jitter, night mode exposure, switching between lenses, and camera cache corruption.
4. **`performance`** (8 troubleshooting records):
   - General system lag, app crashes, RAM management / background app termination, storage space exhaustion, keyboard stutter, animation lag, thermal throttling, and post-update performance anomalies.

---

## 3. Dataset Files Breakdown

Located in `data/development/`:

| File | Count | Description |
|---|---|---|
| `troubleshooting.json` | 32 records | Master database of troubleshooting records, domain mappings, symptoms, keywords, and categorized resolution action steps. |
| `deeplinks.json` | 16 records | Prototype deeplink registry defining UI paths, descriptions, user prompts, and prototype navigation URIs. |
| `test_queries.json` | 72 queries | Benchmark evaluation queries (64 domain-supported queries covering all 32 problems + 8 unsupported/out-of-scope queries). |
| `query_variations.json` | 32 groups | Semantic variation bundles mapping each canonical problem to multiple phrasing and colloquial variations. |

---

## 4. Why `prototype://` URIs Are Used

- **No Fabrication**: We do not speculate or fabricate official Samsung URI schemes (such as `bixby://`, `samsungapps://`, `sec://`, etc.).
- **Safe Sandboxing**: The `prototype://` prefix guarantees that mocked navigation actions are explicitly isolated during prototyping and testing.
- **Contract Adherence**: The engine's resolution layer is built to resolve target screens into URIs regardless of the underlying scheme prefix, enabling drop-in compatibility once official URIs are introduced.

---

## 5. Transition to Official Samsung Assets

When official Samsung assets are released:
1. The JSON records in `data/` will be updated to match the official dataset.
2. The schema definitions in `backend/app/models/` will be adjusted to the final `schema.py`.
3. Validation rules in `scripts/inspect_data.py` will verify official dataset compliance.
4. All test suites in `backend/tests/` will execute against the official data bundle.
