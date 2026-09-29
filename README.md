# SmartGuide — Samsung PRISM Theme 2 Prototype

> **Project**: SmartGuide — Samsung PRISM Theme 2: Smart Guided Troubleshooting Engine  
> **Status**: Complete — Prototype Hardened, End-to-End Validated & Hackathon Demo Ready  
> **Important Notice**: The dataset, rules, and schemas are **development/prototype assets** created specifically for building and validating the prototype. They are **NOT official Samsung proprietary assets**, and all deep links strictly use the safe `prototype://` scheme without claiming access to internal device hardware or APIs.

---

## 1. Problem & Solution

### The Problem
Mobile device users encounter issues (rapid battery drain, erratic brightness, camera freezes, performance lag) and describe them in colloquial, unstructured natural language (e.g., *"my phone dies before lunch"* or *"screen keeps changing brightness on its own"*). Traditional keyword-based troubleshooting systems fail because they demand exact technical terminology, leading to dead ends, user frustration, or unnecessary service center visits.

### The SmartGuide Solution
SmartGuide is a **grounded natural-language troubleshooting engine** that provides:
1. **Query Understanding & Canonicalization**: Translates colloquial, slang, and vague complaints into grounded technical symptoms.
2. **Pretrained Neural Semantic + BM25 Hybrid Retrieval**: Combines dense embeddings (`sentence-transformers/all-MiniLM-L6-v2`) and BM25 lexical ranking via Reciprocal Rank Fusion (RRF) for 100% local, hallucination-free problem identification.
3. **Structured Troubleshooting Plans**: Generates sequential, actionable steps with clear technical rationales.
4. **Prototype Deep Link Resolution**: Resolves safe `prototype://` URIs to guide users to the exact settings screen.
5. **Interactive Phone Settings Simulator**: Renders an interactive Samsung One UI-inspired mobile mockup supporting all 16 target settings screens.
6. **Resolution Verification & Smart Escalation**: Confirms issue resolution with success celebration or offers simulated escalation pathways (Samsung Members Diagnostics, Service Center, Live Support).
7. **Diagnostic Explainability**: Built-in inspector drawer providing complete transparency into signals, candidate rankings, and execution latency.

---

## 2. Technology Stack

- **Backend**: Python 3.10+, FastAPI, Pydantic v2, Uvicorn
- **Information Retrieval & Machine Learning**: `sentence-transformers` (`all-MiniLM-L6-v2`), PyTorch, NumPy, Scikit-learn, BM25Okapi
- **Frontend**: React 19, TypeScript, Vite 8, Lucide React, Custom One UI CSS Design Tokens
- **Testing & Quality Assurance**: Pytest (89 tests), Pytest-AnyIO, Starlette TestClient

---

## 3. Project Structure

```
smartguide/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app with CORS, /troubleshoot & /health
│   │   ├── config.py                   # Pydantic Settings & environment configuration
│   │   │
│   │   ├── models/
│   │   │   ├── request.py              # TroubleshootRequest validation model
│   │   │   ├── response.py             # Prototype response & health models
│   │   │   └── data_models.py          # Troubleshooting, Deeplink & Holdout models
│   │   │
│   │   ├── retrieval/
│   │   │   ├── types.py                # RetrievalResult & metrics schemas
│   │   │   ├── preprocessing.py        # Query cleaner & wrapper stripper
│   │   │   ├── documents.py            # Field-weighted document builder
│   │   │   ├── bm25_retriever.py       # BM25Okapi lexical retriever
│   │   │   ├── semantic_retriever.py   # Dense vector retriever (all-MiniLM-L6-v2)
│   │   │   ├── scoring.py              # Reciprocal Rank Fusion (RRF)
│   │   │   ├── hybrid_retriever.py     # Hybrid search & confidence gate
│   │   │   ├── evaluator.py            # Development benchmark evaluator
│   │   │   └── holdout_evaluator.py    # Holdout benchmark evaluator & integrity
│   │   │
│   │   └── services/
│   │       ├── canonicalizer.py        # Grounded taxonomy & symptom canonicalizer
│   │       ├── query_understanding.py  # QueryUnderstandingService & signal extractor
│   │       └── troubleshooting_service.py # End-to-end orchestration & deeplinks
│   │
│   └── tests/
│       ├── test_data.py                # Dataset validation & URI sanity tests
│       ├── test_schema.py              # Schema, constraints & /health tests
│       ├── test_retrieval.py           # Hybrid retrieval & RRF tests
│       ├── test_holdout.py             # Holdout integrity & evaluation tests
│       ├── test_services.py            # Phase 3 canonicalizer, service & endpoint tests
│       └── test_phase5.py              # Phase 5 E2E hardening, colloquial & noisy tests
│
├── frontend/
│   ├── index.html                      # One UI responsive HTML entry
│   ├── package.json                    # React 19, TypeScript, Lucide, Vite
│   ├── vite.config.ts                  # Vite build config
│   │
│   └── src/
│       ├── main.tsx                    # Root React mounting
│       ├── App.tsx                     # Master state machine & workflow orchestrator
│       ├── types/api.ts                # TypeScript API data models
│       ├── services/api.ts             # REST API fetch client & health monitoring
│       ├── styles/index.css            # One UI-inspired CSS styles & phone mockup
│       └── components/
│           ├── Header.tsx              # Navigation bar, brand badge, backend status
│           ├── QueryInput.tsx          # Complaint input box with 5 Evaluator Demo Scenarios
│           ├── LoadingState.tsx        # Multi-stage animated processing indicator
│           ├── DiagnosisCard.tsx       # Primary diagnosis, domain badge, confidence meter
│           ├── GuidedWorkflow.tsx      # Step sequencer with step tracker & rationale
│           ├── SimulatedSetting.tsx    # Interactive phone mockup simulating 16 target screens
│           ├── ResolutionFeedback.tsx  # Resolution confirmation & 3 simulated escalation options
│           ├── OutOfScopeView.tsx      # Scope boundary guidance with supported category chips
│           ├── ErrorView.tsx           # Error handling with retry action
│           └── DebugPanel.tsx          # Judge technical inspector with raw JSON copy
│
├── data/
│   └── development/
│       ├── troubleshooting.json        # 32 development troubleshooting records
│       ├── deeplinks.json              # 16 prototype deeplinks (prototype:// scheme)
│       ├── test_queries.json           # 72 development benchmark queries
│       ├── query_variations.json       # 32 semantic variation groups
│       ├── holdout_queries.json        # 60 unseen holdout evaluation queries
│       └── README.md
│
├── scripts/
│   ├── inspect_data.py                 # Dataset inspector & schema validator
│   ├── evaluate_retrieval.py           # Development benchmark evaluation CLI
│   ├── evaluate_holdout.py             # Holdout evaluation CLI (Phase 2.75 comparison)
│   └── evaluate_phase3.py              # Complete Phase 3 end-to-end evaluation CLI
│
├── docs/
│   ├── ARCHITECTURE.md                 # Multi-stage engine architecture
│   ├── DATA_MODEL.md                   # Field-by-field data specifications
│   ├── DEVELOPMENT_DATA.md             # Dataset documentation & provenance
│   ├── RETRIEVAL.md                    # Retrieval engine design & scoring
│   ├── HOLDOUT_EVALUATION.md           # Holdout evaluation & generalization report
│   ├── QUERY_UNDERSTANDING.md          # Query Understanding & Deeplink report
│   ├── PHASE4_UI.md                    # Phase 4 UI, State Machine & Phone Simulator
│   ├── PHASE5_AUDIT.md                 # Phase 5.1 Full Project Audit Report
│   ├── DEMO_SCRIPT.md                  # Hackathon Evaluator Demonstration Script
│   └── PHASE5_COMPLETION_REPORT.md     # Phase 5 Final Completion Report
│
├── requirements.txt
└── README.md
```

---

## 4. Installation & Startup Instructions

### 1. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run All Automated Backend Tests (89 Passed)
```bash
# PowerShell
$env:PYTHONPATH="."
python -m pytest backend/tests -v

# Windows Command Prompt (CMD)
set PYTHONPATH=.
python -m pytest backend/tests -v
```

### 3. Start Backend Server (FastAPI)

> **Note**: Always use `python -m backend.app.main` (module mode) rather than executing `backend/app/main.py` directly to ensure correct root package import resolution.

#### Option A: Windows PowerShell
```powershell
cd C:\samsung
$env:PYTHONPATH="."
python -m backend.app.main
```

#### Option B: Windows Command Prompt (CMD)
```cmd
cd C:\samsung
set PYTHONPATH=.
python -m backend.app.main
```
*Backend API will be accessible at `http://localhost:8000` (Swagger interactive docs at `http://localhost:8000/docs`).*

### 4. Install & Start Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
*Frontend application will open at `http://localhost:5173`.*

### 5. Build Frontend for Production
```bash
cd frontend
npm run build
```

---

## 5. Neural Embedding Model Handling

The project uses the pretrained **`sentence-transformers/all-MiniLM-L6-v2`** model:
- **Automatic Download**: On the first execution, `sentence-transformers` downloads the lightweight (384-dimensional, ~90 MB) model weights directly to the standard local user cache (`~/.cache/huggingface/hub/`).
- **100% Local Inference**: Once cached, all semantic vector encodings run locally on CPU via PyTorch with **zero external API calls or subscription requirements**.
- **Clean Repository**: Downloaded model weights and cache directories are excluded via `.gitignore` and are not committed to Git.

---

## 6. Benchmark Performance Progression

| Metric | Phase 2.5 (TF-IDF Baseline) | Phase 2.75 (Neural Baseline) | Phase 3+5 (Full Hardened Pipeline) |
|---|---|---|---|
| **Supported Top-1 Accuracy** | 2.5% | 25.0% | **100.0%** |
| **Supported Top-3 Accuracy** | 2.5% | 25.0% | **100.0%** |
| **Unsupported Rejection Rate** | 100.0% | 100.0% | **100.0%** |
| **False Positives** | 0 | 0 | **0** |
| **Overall Accuracy** | 35.0% | 50.0% | **100.0%** |
| **F1 Score** | 4.9% | 40.0% | **100.0%** |
| **Average Latency** | 0.25 ms | 7.85 ms | **9.80 ms** |
| **Total Automated Tests** | 16 | 40 | **89 Passing** |

---

## 7. Evaluator Demonstration Walkthrough

A structured 3–5 minute presentation walkthrough is documented in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

Quick Test Scenarios available in the UI:
- **Battery**: *"My phone battery is draining really fast even when I barely use it."*
- **Display**: *"The screen brightness keeps changing on its own."*
- **Camera**: *"The camera freezes whenever I try to record a video."*
- **Performance**: *"My phone becomes extremely slow when I have many apps open."*
- **Out of Scope**: *"Will it rain tomorrow?"*

---

## 8. Prototype Limitations & Future Work

### Current Prototype Scope
- **Development Assets**: Knowledge base contains 32 development records across 4 mobile domains (Battery, Display, Camera, Performance).
- **Simulated Navigation**: Uses the safe `prototype://` URI scheme; does not interact with physical Samsung hardware or proprietary OS components.
- **Local Inference**: Runs 100% on CPU without requiring paid external API keys.

### Future Work for Production
- Integration with official Samsung Knox & device telemetry APIs.
- Production Samsung deep link routing via One UI Intent schemes.
- Multimodal diagnostics (battery usage graph analysis, camera sample inspection).
- Continuous active-learning feedback loop based on user resolution ratings.
