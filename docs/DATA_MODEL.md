# SmartGuide Data Model Documentation

> [!IMPORTANT]
> This document details every field across the **SmartGuide Development Dataset** and prototype API schemas.
> All data models represent prototype specifications for Phase 1.

---

## 1. Troubleshooting Records (`troubleshooting.json`)

File contains a JSON array of 32 troubleshooting problem records.

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | `string` | Unique problem identifier | `"battery_001"` |
| `domain` | `string` | Domain category (`battery`, `display`, `camera`, `performance`) | `"battery"` |
| `problem` | `string` | Canonical problem headline | `"Battery drains quickly"` |
| `description` | `string` | Detailed problem context and explanation | `"Development prototype record for: Battery drains quickly."` |
| `keywords` | `array[string]` | Keywords and synonyms for lexical matching | `["battery usage", "battery", "battery drains quickly"]` |
| `actions` | `array[Action]` | Step-by-step resolution actions (see Action object below) | `[...]` |
| `source` | `string` | Data provenance marker | `"development_prototype"` |

### Nested Action Object (`actions[]`)

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | `string` | Unique action identifier | `"battery_001_action_01"` |
| `name` | `string` | Action headline | `"Review battery settings"` |
| `description` | `string` | Purpose and effect of executing this action | `"Review settings relevant to the reported issue: battery drains quickly."` |
| `category` | `string` | Execution classification: `manual`, `auto`, or `critical` | `"manual"` |
| `priority` | `integer` | Recommended order of execution (1 = highest) | `1` |
| `steps` | `array[string]` | Ordered user instructions | `["Open Settings", "Open Battery", "Open Battery usage"]` |
| `target_screen` | `string` | Settings path or UI destination | `"Battery > Battery usage"` |

---

## 2. Prototype Deeplinks (`deeplinks.json`)

File contains a JSON array of 16 prototype deeplink records.

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | `string` | Unique deeplink identifier | `"prototype_dl_001"` |
| `name` | `string` | Display label for the deeplink action | `"Review battery settings"` |
| `description` | `string` | Technical description of destination screen | `"Review settings relevant to the reported issue: battery drains quickly."` |
| `message` | `string` | User-facing prompt or notification text | `"Review battery settings"` |
| `qna_description` | `string` | Q&A description corresponding to user intent | `"Review settings relevant to the reported issue: battery drains quickly."` |
| `target_screen` | `string` | Canonical UI / Settings screen path | `"Battery > Battery usage"` |
| `uri` | `string` | Prototype URI scheme (`prototype://...`) | `"prototype://settings/battery/battery_usage"` |
| `source` | `string` | Provenance marker | `"development_prototype"` |

---

## 3. Test Queries (`test_queries.json`)

File contains a JSON array of 72 benchmark evaluation queries.

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | `string` | Query test case identifier | `"q_001"` |
| `query` | `string` | Raw user complaint text | `"Battery drains quickly"` |
| `expected_domain` | `string \| null` | Expected domain if supported, or `null` if out-of-scope | `"battery"` or `null` |
| `expected_problem_id` | `string \| null` | Target problem ID if supported, or `null` if unsupported | `"battery_001"` or `null` |
| `source` | `string` | Provenance marker | `"development_prototype"` |

---

## 4. Query Variations (`query_variations.json`)

File contains a JSON array of 32 semantic variation groups.

| Field | Type | Description | Example |
|---|---|---|---|
| `problem_id` | `string` | Target troubleshooting problem ID | `"battery_001"` |
| `canonical_query` | `string` | Standard baseline reference query | `"Battery drains quickly"` |
| `query_variations` | `array[string]` | Set of semantically equivalent user phrasings | `["Battery drains quickly", "issue with battery usage", ...]` |
| `source` | `string` | Provenance marker | `"development_prototype"` |

---

## 5. API Models (`backend/app/models/`)

### Request Model: `TroubleshootRequest`
- `query` (`string`): User input complaint. Enforces length constraints (1–2000 characters) and rejects whitespace-only inputs.

### Response Model: `TroubleshootResponse`
*(Prototype schema — not official Samsung schema)*
- `contexts` (`array[Context]`): Matched troubleshooting context objects.
  - `goal` (`string`): User objective solved.
  - `title` (`string`): Title of context.
  - `score` (`float`): Confidence / similarity score between `0.0` and `1.0`.
  - `actions` (`array[Action]`):
    - `action_name` (`string`): Action title.
    - `description` (`string`): Action details.
    - `category` (`"auto" | "manual" | "critical"`): Execution mode.
    - `steps` (`array[Step]`): `text` (`string`).
    - `target_screen` (`string`): Destination screen path.
    - `deeplink` (`string | null`): Prototype URI (e.g. `prototype://...`).
- `fallback` (`string | null`): Guidance message returned when no problem matches.

### Health Model: `HealthResponse`
- `status`: `"ok"`
- `data`: `"ready"`
- `schema`: `"ready"`
- `retrieval`: `"not_initialized"`
- `cache`: `"not_initialized"`
- `llm`: `"not_initialized"`
