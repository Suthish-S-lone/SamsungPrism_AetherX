# SmartGuide — Hackathon Evaluator Demonstration Script (3–5 Minutes)

> **Theme**: Samsung PRISM Hackathon Theme 2 — Smart Guided Troubleshooting Engine  
> **Target Audience**: PRISM Mentors, Hackathon Judges & Technical Evaluators  
> **Demonstration Goal**: Showcase natural language understanding, grounded neural semantic retrieval, interactive One UI settings simulation, and transparent diagnostic explainability.

---

## 1. Introduction (30 Seconds)

**Presenter**:
> *"Good morning judges and mentors! We are presenting **SmartGuide**, our prototype for Samsung PRISM Theme 2: Smart Guided Troubleshooting Engine.*
> 
> *When mobile users experience issues—like high battery drain or camera lag—they describe symptoms in colloquial, vague terms like 'my phone dies before lunch' or 'camera freezes when recording'. Traditional help systems fail because they rely on exact keyword matches.*
> 
> *SmartGuide bridges this gap using a **multi-stage query understanding and pretrained neural hybrid retrieval pipeline**. It extracts domain signals, canonicalizes symptoms, identifies grounded technical resolutions from our troubleshooting knowledge base, generates structured step-by-step action plans, and resolves prototype deep links to simulate real Samsung mobile settings."*

---

## 2. Live Demo Flow

### Step 1: Battery Domain — Natural Language & Idle Drain (1 Minute)

1. **Action**: Open the SmartGuide web app at `http://localhost:5173`.
2. **Action**: Click the **"Battery Drain"** Demo Scenario chip (or type: *"My phone battery is draining really fast even when I barely use it."*).
3. **Observation**:
   - The animated multi-stage radar spins through Query Analysis $\to$ Neural Retrieval $\to$ Response Synthesis.
   - **Diagnosis Card** appears:
     - Domain Badge: `BATTERY` (Confidence: 95%).
     - Identified Issue: `Battery drains while the device is idle`.
     - Grounded Reasoning: Explains why background app activity during sleep was identified.
4. **Action**: Click **"Start Guided Troubleshooting"**.
5. **Action**: View **Action 1 of 2**: `Review background usage limits`.
6. **Action**: Click **"Open Simulated Setting"**.
7. **Observation**:
   - The interactive phone mockup slides in displaying the simulated **Battery > Background Usage Limits** One UI screen (`prototype://settings/battery/background_limits`).
   - Toggle **"Put unused apps to sleep"** or restrict active apps.
8. **Action**: Click **"Apply & Return to Steps"**.
9. **Action**: Click **"Next Step"** $\to$ **"Complete & Verify"**.
10. **Action**: On the Resolution Feedback screen, click **"Yes, it's fixed!"** to show the resolution summary celebration.

---

### Step 2: Camera Domain — Colloquial Video Freezing (45 Seconds)

1. **Action**: Click **"New Diagnosis"** or use the Evaluator Demo Scenarios.
2. **Action**: Click **"Camera Freezing"** (or type: *"The camera freezes whenever I try to record a video."*).
3. **Observation**:
   - Domain detected: `CAMERA`.
   - Matched Problem: `Camera application freezes` (`camera_018`).
4. **Action**: Click **"Start Guided Troubleshooting"** $\to$ Click **"Open Simulated Setting"**.
5. **Observation**:
   - Interactive camera settings simulation appears (`prototype://settings/camera/reset`).
   - Click **"Reset Camera Settings"** with instant simulated confirmation toast.
6. **Action**: Click **"I Checked This"** $\to$ Click **"Complete & Verify"**.

---

### Step 3: Out-of-Scope Safety & Fallback (30 Seconds)

1. **Action**: Click the **"Non-Troubleshooting Query"** Demo Scenario: *"Will it rain tomorrow?"* (or enter a cooking/travel query).
2. **Observation**:
   - SmartGuide safely detects the out-of-scope boundary.
   - Shows a clean, helpful fallback message explaining supported domains (Battery, Display, Camera, Performance) without generating hallucinated device instructions.
   - Evaluator can click any supported domain card to instantly return to supported troubleshooting.

---

### Step 4: Technical Diagnostics Inspector (45 Seconds)

1. **Action**: Click the **"Diagnostics"** toggle button in the header (or expand the bottom drawer).
2. **Point out to Judges**:
   - **Domain & Confidence**: Shows classified domain and confidence percentage.
   - **Canonical Rewrite**: Demonstrates colloquial $\to$ canonical technical mapping.
   - **Top Retrieval Candidates Table**: Shows hybrid scoring combining **Dense Neural Embeddings (`all-MiniLM-L6-v2`)**, **BM25 Lexical Ranking**, and **Reciprocal Rank Fusion (RRF)**.
   - **Latency Telemetry**: Show local CPU inference latency (~8–15 ms) with zero external paid API dependencies.
   - **Raw JSON**: Show one-click structured JSON payload matching the prototype schema.

---

## 3. Conclusion & Key Takeaways (30 Seconds)

**Presenter**:
> *"To summarize our Theme 2 prototype:*
> 1. *100% Local Inference: No external paid API dependencies, powered by pretrained SentenceTransformers.*
> 2. *Grounded & Hallucination-Free: All diagnoses map directly to verified knowledge base records and `prototype://` URIs.*
> 3. *High Performance: 89 passing automated tests, sub-20ms latency, and 100% rejection of out-of-scope complaints.*
> 4. *Evaluator-Ready: Full end-to-end interactive workflow from freeform complaint to simulated settings resolution.*
> 
> *Thank you! We are happy to take any questions."*
