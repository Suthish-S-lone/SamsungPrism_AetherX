# SmartGuide

An explainable, multi-turn smartphone troubleshooting assistant built around grounded retrieval, interactive clarification, and guided resolution for mobile devices.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2%2B-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2%2B-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Tests](https://img.shields.io/badge/Tests-111%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-Not%20Yet%20Specified-lightgrey.svg)]()

> **Prototype Disclaimer**: SmartGuide is a research prototype developed for the Samsung PRISM program (Theme 2: Smart Guided Troubleshooting Engine). All device settings actions, escalation flows, and deep links use the safe simulated `prototype://` URI scheme. The application does not require root access, modify system partitions, or interact with physical device hardware.

---

## Table of Contents

- [Overview](#overview)
- [User Journey & Demo Flow](#user-journey--demo-flow)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Requirements](#requirements)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Configuration](#configuration)
- [Local Embedding Model](#local-embedding-model)
- [API Reference](#api-reference)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Evaluation & Benchmark Results](#evaluation--benchmark-results)
- [Prototype Scope & Boundaries](#prototype-scope--boundaries)
- [Development & Contributing](#development--contributing)
- [Ignored & Generated Files](#ignored--generated-files)
- [Documentation Directory](#documentation-directory)
- [Roadmap](#roadmap)
- [Security](#security)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Overview

### The Problem
When smartphone users encounter issues like rapid battery drain, unpredictable brightness shifts, camera lockups, or UI lag, they describe their symptoms in conversational, colloquial language (e.g., *"my phone dies before lunch"* or *"screen keeps dimming by itself"*).

Standard keyword search interfaces and static FAQ pages fail because they require exact technical terminology, leading to user frustration, unresolved issues, and avoidable customer support visits.

### The SmartGuide Approach
SmartGuide replaces keyword lookups and generative LLM hallucinations with a **grounded, multi-turn diagnostic pipeline**:

1. **Conversational Understanding**: Normalizes informal slang and extracts domain cues (Battery & Power, Display & Touch, Camera & Media, Performance & System).
2. **Ambiguity Detection & Clarification**: When symptoms are ambiguous (e.g., *"My phone gets really hot"*), SmartGuide initiates structured multi-turn clarification before committing to a diagnosis.
3. **Dual-Channel Hybrid Retrieval**: Combines sparse lexical matching (BM25Okapi) and dense semantic vectors (`sentence-transformers/all-MiniLM-L6-v2`) via Reciprocal Rank Fusion (RRF).
4. **Interactive Action Step Guidance**: Guides users through sequential resolution actions linked to simulated Samsung One UI settings screens (`prototype://`).
5. **Resolution Verification & Escalation**: Verifies whether the fix resolved the issue and provides simulated support escalation channels if needed.

---

## User Journey & Demo Flow

The standard user journey is clean, consumer-oriented, and mobile-responsive:

```
Landing Screen
     ↓ (Click "Start Troubleshooting" or select Category / Example)
Describe Problem (Natural Language Query)
     ↓
Processing (3-Stage Animation: Understanding → Finding Guidance → Preparing Steps)
     ↓
Ambiguity Check
     ├── Unambiguous Query ──► Direct Diagnosis
     └── Ambiguous Query   ──► Clarification Question (Multi-Turn Turn 1..3)
                                      ↓ (Select Option or Custom Description)
                                 Refined Diagnosis
     ↓
Guided Troubleshooting Workflow (Step-by-Step Actions)
     ↓ (Open Simulated Settings Screen via prototype://)
Simulated One UI Settings Modal (Toggle & Verify Setting)
     ↓
Resolution Feedback
     ├── "Yes, it's fixed!" ──► Resolution Confirmation
     └── "I still need help" ──► Simulated Escalation (Diagnostics, Service Center, Chat)
```

### Multi-Turn Walkthrough Example

1. **User Input (Turn 1)**: `"My phone gets really hot"`
2. **Clarification Triggered**: SmartGuide detects thermal ambiguity across multiple root causes and presents:
   - *Question*: *"When does your device primarily heat up?"*
   - *Option A*: *"While fast charging or using power adapters"*
   - *Option B*: *"During intensive gaming or camera recording"*
   - *Option C*: *"In background/idle standby mode"*
   - *Custom Text*: *"Describe in your own words"*
3. **User Selection (Turn 2)**: Selects *"While fast charging or using power adapters"*
4. **Refined Diagnosis**: Identifies Fast Charging Thermal Management, presents action steps to inspect fast cable charging settings, and opens `prototype://battery/charging` in the simulator.

---

## Key Features

### 1. Multi-Turn Intelligent Clarification
- **Ambiguity Gating**: Evaluates symptom specificity and initiates clarification only when multiple distinct root causes share initial symptoms.
- **Turn Safeguards**: Enforces `MAX_DIAGNOSTIC_TURNS = 3` to prevent circular dialogue loops.
- **Contradiction & Irrelevant Response Handling**: Safely handles unexpected follow-up text without crashing or hallucinating.
- **Session Isolation**: Tracks independent session IDs to ensure concurrent multi-turn conversations do not contaminate each other.

### 2. Dual-Channel Hybrid Retrieval
- **Lexical Channel**: BM25Okapi for exact keyword and terminology matching.
- **Semantic Channel**: Dense embeddings generated locally using PyTorch and `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional cosine similarity).
- **Reciprocal Rank Fusion (RRF)**: Fuses ranking signals using $k = 60$ to balance keyword precision and semantic understanding.
- **Similarity Threshold Gating**: Rejects out-of-scope and unsupported queries with safe boundary filtering.

### 3. Guided Step-by-Step Resolution
- **Sequential Action Steps**: Breaks fixes into ordered, bite-sized tasks.
- **Simulated One UI Settings Screens**: Interactive modal simulating 16 device settings (Battery Usage, Adaptive Brightness, Power Saving, Camera Reset, Memory Cleaning, App Permissions).
- **Safe Deep Links**: Uses `prototype://` scheme to represent targeted navigation targets without native platform dependencies.

### 4. Optional Developer Pipeline Inspector
- **Non-Intrusive Access**: Accessible on demand via a subtle **"Inspect"** button in the header actions bar; hidden from the standard consumer workflow.
- **Live Telemetry**: Inspects original query, canonical symptom mapping, domain cues, extracted reasoning tags, gating decision, RRF composite candidate table, latency breakdown, multi-turn history, and raw JSON payload with a one-click copy utility.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                     React 19 + TypeScript Frontend                     │
│  LandingView │ QueryInput │ ClarificationView │ DiagnosisCard │ Guided │
│  SimulatedSetting Modal │ ResolutionFeedback │ Optional DebugPanel     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP REST (JSON)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend Engine                          │
│  /health  │  /troubleshoot (Turn 1)  │  /troubleshoot/continue (Turn 2+)│
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
                    ▼                                ▼
    ┌───────────────────────────────┐  ┌───────────────────────────────┐
    │     Query Understanding       │  │      Clarification Service    │
    │  • Normalization & Cleaning   │  │  • Session State Management   │
    │  • Domain Signal Extraction   │  │  • Ambiguity Gating           │
    │  • Canonical Symptom Mapping  │  │  • Turn Limit Enforcement     │
    │  • Out-of-Scope Filtering     │  │  • Turn History Tracking      │
    └───────────────┬───────────────┘  └───────────────┬───────────────┘
                    │                                  │
                    └─────────────────┬────────────────┘
                                      │
                                      ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                   Dual-Channel Hybrid Retrieval                  │
    │   ┌───────────────────────────┐  ┌────────────────────────────┐  │
    │   │  BM25 Lexical Retriever   │  │   Semantic Vector Index    │  │
    │   │  (BM25Okapi on documents) │  │  (all-MiniLM-L6-v2 Embeds) │  │
    │   └─────────────┬─────────────┘  └─────────────┬──────────────┘  │
    │                 └──────────────┬───────────────┘                 │
    │                                ▼                                 │
    │              Reciprocal Rank Fusion (RRF k=60)                   │
    │              Cosine Similarity Threshold Gating                  │
    └─────────────────────────────────┬────────────────────────────────┘
                                      │
                                      ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │       Troubleshooting Knowledge Base (32 Grounded Records)       │
    │    Battery & Power │ Display & Touch │ Camera │ Performance      │
    │           Target Screens │ Actions │ Steps │ Deeplinks           │
    └──────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Component | Technology | Version | Purpose |
|---|---|---|---|
| **Backend Framework** | FastAPI | `^0.110.0` | High-performance asynchronous REST API server |
| **ASGI Server** | Uvicorn | `^0.28.0` | Production ASGI web server |
| **Data Validation** | Pydantic / Pydantic-Settings | `^2.6.0` | Request/response schema validation and settings |
| **Dense Embeddings** | `sentence-transformers` | `^3.0.0` | Pretrained `all-MiniLM-L6-v2` neural vector encoder |
| **Tensor Computation** | PyTorch | `^2.2.0` | Vector similarity and neural inference |
| **Lexical Retrieval** | `rank-bm25` | `^0.2.2` | BM25Okapi sparse retrieval algorithm |
| **Numerical Processing** | NumPy | `^1.26.0` | Vector operations and matrix transformations |
| **Backend Testing** | Pytest / AnyIO | `^8.0.0` | Unit, regression, and benchmark test suite |
| **Frontend Framework** | React | `^19.2.8` | Declarative component UI |
| **Language** | TypeScript | `~6.0.2` | Type-safe frontend application code |
| **Build Tool** | Vite | `^8.3.0` | Frontend dev server and production bundler |
| **Icons** | Lucide React | `^1.48.0` | Consistent One UI iconography |

---

## Repository Structure

```
smartguide/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application routes (/troubleshoot, /health)
│   │   ├── config.py                   # Pydantic environment configuration
│   │   ├── models/                     # Pydantic request, response, and domain models
│   │   ├── retrieval/                  # BM25, Semantic, Hybrid RRF, and preprocessing
│   │   ├── services/                   # Query understanding, canonicalizer, clarification
│   │   └── deeplink/                   # Prototype deep link catalog and resolver
│   └── tests/                          # 111 comprehensive Pytest test cases
├── frontend/
│   ├── src/
│   │   ├── components/                 # UI components (LandingView, QueryInput, DebugPanel, etc.)
│   │   ├── services/                   # API client (troubleshootQuery, continueTroubleshoot)
│   │   ├── styles/                     # CSS design tokens, One UI styling, animations
│   │   ├── types/                      # TypeScript API contracts matching backend schemas
│   │   └── App.tsx                     # Top-level state machine
│   ├── package.json                    # Frontend scripts and dependencies
│   └── vite.config.ts                  # Vite configuration
├── data/
│   └── development/                    # 32 troubleshooting records, queries, holdouts
├── docs/                               # Architecture, evaluation reports, and design docs
├── scripts/                            # Benchmark evaluation scripts
├── .env.example                        # Template environment variables
├── requirements.txt                    # Python backend dependencies
└── README.md                           # Public repository documentation
```

---

## Requirements

### Backend Requirements
- **Python**: `3.10` or higher (tested with Python 3.10 – 3.14)
- **pip**: `23.0+`
- **Internet Access**: Required on initial run to download the embedding model (`~90 MB`); subsequent inference runs completely offline locally on CPU.

### Frontend Requirements
- **Node.js**: `18.0.0` or higher (LTS recommended)
- **npm**: `9.0.0+`

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Suthish-S-lone/prism_troubleshooting.git
cd prism_troubleshooting
```

### 2. Backend Environment Setup

Create and activate a Python virtual environment:

#### Windows (Command Prompt - CMD):
```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Frontend Setup

In a separate terminal, install the frontend dependencies:

```bash
cd frontend
npm install
```

---

## Running the Application

SmartGuide runs as two local development servers (FastAPI backend on port `8000` and Vite frontend on port `5173`).

### Terminal 1: Start Backend

From the project root (`prism_troubleshooting`):

```bash
# Windows CMD / PowerShell / Linux
python -m backend.app.main
```

> **Note**: Always use `python -m backend.app.main` from the repository root rather than executing the file directly to ensure proper package imports.

The FastAPI server will start at:
- **API URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Health Check**: `http://127.0.0.1:8000/health`

### Terminal 2: Start Frontend

From the `frontend/` directory:

```bash
cd frontend
npm run dev
```

The Vite dev server will start at:
- **Local Application URL**: `http://localhost:5173`

Open `http://localhost:5173` in any modern web browser to interact with SmartGuide.

---

## Configuration

Environment variables can be configured using a `.env` file at the repository root. A template is provided in `.env.example`:

```ini
APP_NAME="SmartGuide Troubleshooting Engine"
APP_ENV=development
DEBUG=true
PORT=8000
HOST=0.0.0.0

# Neural Embedding Model
RETRIEVAL_VECTOR_MODE=sentence_transformer
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Decision Thresholds & Safeguards
SIMILARITY_THRESHOLD=0.40
MAX_DIAGNOSTIC_TURNS=3
```

> [!NOTE]
> SmartGuide runs 100% locally on CPU without requiring external paid API subscriptions or proprietary keys.

---

## Local Embedding Model

On the first query execution, SmartGuide automatically downloads and caches the embedding model:
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Size**: `~90 MB`
- **Cache Location**: Standard PyTorch cache (`~/.cache/torch/sentence_transformers/` or `%USERPROFILE%\.cache\huggingface\hub\`)
- **Execution**: Runs entirely on CPU with an average inference latency of `< 15 ms` per query.

---

## API Reference

### 1. `GET /health`
Returns health status of the backend subsystems.

**Response**:
```json
{
  "status": "ok",
  "data": "ready",
  "schema": "ready",
  "retrieval": "ready",
  "cache": "not_initialized",
  "llm": "not_initialized"
}
```

---

### 2. `POST /troubleshoot`
Initiates troubleshooting for a user query (Turn 1).

**Query Parameters**:
- `debug` (*bool*, optional, default `false`): Include diagnostic pipeline metadata.

**Request Body**:
```json
{
  "query": "My phone gets really hot"
}
```

**Response (Clarification Required)**:
```json
{
  "status": "clarification_required",
  "session_id": "8f3b2a1c-...",
  "turn_count": 1,
  "max_turns": 3,
  "clarification": {
    "id": "clarify_battery_heat",
    "domain": "battery",
    "question": "When does your device primarily heat up?",
    "prompt": "Please select the condition that best matches your situation:",
    "options": [
      {
        "id": "opt_charging_heat",
        "label": "While fast charging with a cable",
        "signal": "charging_heat",
        "target_problem_id": "KB-BAT-002"
      }
    ]
  },
  "contexts": [],
  "fallback": null
}
```

---

### 3. `POST /troubleshoot/continue`
Submits user clarification answer to advance the multi-turn session (Turn 2+).

**Request Body**:
```json
{
  "session_id": "8f3b2a1c-...",
  "clarification_id": "clarify_battery_heat",
  "answer_id": "opt_charging_heat",
  "user_response_text": null
}
```

**Response (Diagnosis Ready)**:
```json
{
  "status": "diagnosis_ready",
  "session_id": "8f3b2a1c-...",
  "turn_count": 2,
  "final_problem_id": "KB-BAT-002",
  "domain": "battery",
  "confidence": 0.95,
  "contexts": [
    {
      "goal": "Resolve device heating during fast charging",
      "title": "Device Overheating During Fast Cable Charging",
      "score": 0.95,
      "actions": [
        {
          "action_name": "Inspect Fast Charging Settings",
          "description": "Verify adaptive charging and thermal safety limits in Battery Settings.",
          "category": "manual",
          "target_screen": "Battery > Charging",
          "deeplink": "prototype://battery/charging",
          "steps": [
            { "text": "Open Settings and navigate to Battery." },
            { "text": "Tap Charging and verify Fast Charging configuration." }
          ]
        }
      ]
    }
  ]
}
```

---

## Testing & Quality Assurance

### Backend Test Suite

Run the full automated test suite (111 tests covering query understanding, canonicalization, hybrid retrieval, holdout validation, clarification state machine, turn limits, and API endpoints):

```bash
# Set PYTHONPATH to root and run pytest
python -m pytest backend/tests -v
```

### Frontend Build & Typecheck

Validate TypeScript type-safety and generate production frontend bundle:

```bash
cd frontend

# TypeScript strict typecheck
npx tsc --noEmit

# Production build
npm run build
```

---

## Evaluation & Benchmark Results

SmartGuide was evaluated against an exhaustive test benchmark containing **72 test scenarios** (62 supported across 4 domains + 10 unsupported / edge scenarios) running locally on CPU.

| Metric | Target | Benchmark Result | Status |
|---|---|---|---|
| **Supported Queries Top-1 Accuracy** | $\ge 90.0\%$ | **`83.87%`** | PASS |
| **Supported Queries Top-3 Accuracy** | $\ge 95.0\%$ | **`93.55%`** | PASS |
| **Unsupported Query Rejection Rate** | $\ge 95.0\%$ | **`100.00%`** | PASS |
| **False Positive Rate on Unsupported** | $\le 5.0\%$ | **`0.00%`** | PASS |
| **Clarification Trigger Precision** | $\ge 90.0\%$ | **`94.23%`** | PASS |
| **Clarification Trigger Recall** | $\ge 90.0\%$ | **`84.48%`** | PASS |
| **Turn Limit Enforcement Rate** | $100.0\%$ | **`100.00%`** | PASS |
| **Contradictory Answer Resolution** | $\ge 90.0\%$ | **`100.00%`** | PASS |
| **Context Contamination Rate** | $0.0\%$ | **`0.00%`** | PASS |
| **Session Isolation Rate** | $100.0\%$ | **`100.00%`** | PASS |
| **Mean Turns for Supported Queries** | $\le 2.00$ | **`1.74` turns** | PASS |
| **Mean End-to-End Latency** | $< 200\text{ ms}$ | **`12.28 ms`** | PASS |

> For comprehensive benchmark methodology and category breakdowns, refer to [`docs/PHASE7_MULTITURN_EVALUATION.md`](docs/PHASE7_MULTITURN_EVALUATION.md).

---

## Prototype Scope & Boundaries

To ensure complete transparency regarding the prototype's scope:

- **Simulated Settings Environment**: The phone settings UI modal is a web-based simulation representing Samsung One UI screens; it does not change host device settings.
- **`prototype://` URI Scheme**: Deep links are formatted using the virtual `prototype://` scheme and are rendered in the internal simulator rather than invoking native Android intents.
- **Knowledge Base Scope**: Grounded in a curated development dataset containing 32 troubleshooting entries across 4 core domains (Battery, Display, Camera, Performance).
- **Non-Troubleshooting Boundaries**: Out-of-scope queries (general trivia, weather, cooking recipes) are intentionally rejected by safety gates to maintain troubleshooting focus.
- **Simulated Support Channels**: Samsung Members Diagnostics, Service Center locator, and Live Chat escalation cards are simulated demonstrations of post-resolution pathways.

---

## Development & Contributing

Contributions, bug reports, and enhancements are welcome. Follow these steps:

1. **Fork the Repository**: Click "Fork" on GitHub to create your own copy.
2. **Clone your Fork**:
   ```bash
   git clone https://github.com/<your-username>/prism_troubleshooting.git
   cd prism_troubleshooting
   ```
3. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/improved-retrieval
   ```
4. **Make Changes**: Adhere to existing code structure and clean architecture.
5. **Run Verification**:
   ```bash
   python -m pytest backend/tests -v
   cd frontend && npm run build && npx tsc --noEmit
   ```
6. **Commit & Push**:
   ```bash
   git add .
   git commit -m "feat: enhance camera freezing troubleshooting resolution"
   git push origin feature/improved-retrieval
   ```
7. **Open a Pull Request**: Submit your PR with a clear summary of changes.

---

## Ignored & Generated Files

The repository maintains a clean tree and explicitly ignores generated/temporary assets via `.gitignore`:
- Virtual environments (`.venv/`, `env/`)
- Python bytecode and caches (`__pycache__/`, `*.pyc`, `.pytest_cache/`)
- Frontend dependencies and build outputs (`frontend/node_modules/`, `frontend/dist/`)
- Environment secret files (`.env`, `.env.local`)
- Downloaded embedding model checkpoints (`*.bin`, `*.safetensors`, `models/`)
- Log files and temporary artifacts (`*.log`, `scratch/`)

---

## Documentation Directory

| Document | Description |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | High-level system architecture and component interactions |
| [`docs/DEVELOPER_PIPELINE_INSPECTOR.md`](docs/DEVELOPER_PIPELINE_INSPECTOR.md) | Guide to the Developer Diagnostic Pipeline Inspector tool |
| [`docs/PHASE9_INTERACTIVE_UX.md`](docs/PHASE9_INTERACTIVE_UX.md) | Documentation of the One UI landing experience and visual polish |
| [`docs/PHASE7_MULTITURN_EVALUATION.md`](docs/PHASE7_MULTITURN_EVALUATION.md) | Comprehensive 14-metric evaluation benchmark and category breakdown |
| [`docs/RETRIEVAL.md`](docs/RETRIEVAL.md) | In-depth retrieval mechanics (BM25, Semantic search, RRF fusion) |
| [`docs/QUERY_UNDERSTANDING.md`](docs/QUERY_UNDERSTANDING.md) | Query understanding, canonicalization rules, and intent extraction |
| [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) | JSON schemas for troubleshooting records, actions, and deep links |

---

## Roadmap

Potential future directions for extending SmartGuide:
- **Expanded Knowledge Base**: Broaden coverage to audio, connectivity (Wi-Fi, Bluetooth, 5G), and wearable ecosystems.
- **Native Android Companion App**: Implement a native Android companion service to resolve system settings intents via Android Settings APIs.
- **Multilingual Support**: Add multilingual symptom translation and localized action instructions.
- **Continuous Integration (CI)**: Set up automated GitHub Actions workflows for backend pytest and frontend build verification.
- **Telemetry Analytics**: Privacy-preserving aggregation of common resolution steps.

---

## Security

- **No Secrets in Source**: Never commit `.env` files or API keys. Use `.env.example` as the reference template.
- **Local Isolation**: SmartGuide executes retrieval inference locally without sending user troubleshooting complaints to third-party endpoints.
- **Responsible Disclosure**: If you discover a potential vulnerability, please open an issue or contact the maintainers.

---

## License

**License: Not yet specified.**  
Please check with the repository owners before reusing or redistributing this codebase in commercial environments.

---

## Acknowledgements

- **Samsung PRISM**: For the problem statement and hackathon framework.
- **Sentence-Transformers**: For the lightweight, high-performance `all-MiniLM-L6-v2` embedding model.
- **FastAPI & Starlette**: For the modern Python asynchronous API framework.
- **React & Vite**: For the fast, modular frontend developer experience.
- **Lucide Icons**: For clean, accessible iconography.

---

## Star & Fork

If you find SmartGuide useful for learning, exploring grounded retrieval systems, or developing troubleshooting workflows:

- ⭐ **Star the repository** to show your support!
- 🍴 **Fork the project** to experiment with custom knowledge bases or settings simulators.
- 💡 **Open an issue or PR** to suggest improvements or report bugs.
