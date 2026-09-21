# EviBite AI — Multi-Agent Supermarket Product Intelligence Assistant

EviBite AI is a multi-agent AI assistant designed for supermarket shoppers and food consumers. It helps users query food product ingredients, allergen safety, nutrition parameters, dietary compliance, and personal uploaded food guides.

---

## Architecture Overview

EviBite AI is powered by a **4-Agent Architecture**.

```
[ User Request ]
       │
       ▼
┌─────────────────────────────────────────┐
│  Agent 1 — Triage & Routing             │
│  - Intent Extraction                    │
│  - Entity & Constraint Extraction       │
│  - Conditional Path Selection           │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  Agent 2 — Multi-Source Retrieval       │  ◄──  [ Open Food Facts API ]
│  - Searches OFF + User Knowledge Base   │  ◄──  [ User Document Collection (BM25) ]
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  Agent 3 — Safety & Analysis            │
│  - Deterministic Allergen Safety Check  │
│  - Dietary Compliance & Thresholds      │
│  - Conflict & Provenance Detection      │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  Agent 4 — Recommendation & Response    │
│  - Strict Evidence-Grounded Synthesis   │
│  - Citation & Provenance Formatting     │
└─────────────────────────────────────────┘
```

> **CRITICAL DESIGN ARCHITECTURE NOTE**
> - EviBite has **four intelligent agents** (Agent 1: Triage, Agent 2: Retrieval, Agent 3: Safety Analysis, Agent 4: Response).
> - **Uploaded user documents are NOT a fifth agent.**
> - The document system is a **persistent personal knowledge base** queried as an Information Retrieval (IR) source by **Agent 2**.
> - **Security is cross-cutting** across authentication, database queries, upload file validation, rate limiting, and prompt injection defense.

---

## The Four Intelligent Agents

### 1. Agent 1 — Triage & Routing
- **Role**: Turns natural language grocery questions into validated, structured output envelopes (`TriageOutput`).
- **Input**: Raw user query string + optional previous product context.
- **Output**: Canonical intent (`PRODUCT_SEARCH`, `ALLERGEN_CHECK`, `NUTRITION_QUERY`, etc.), product entities, category, allergens, dietary requirements, and numeric constraints (`NutrientConstraint`).
- **Resilience**: Uses Gemini 2.5 Flash with a robust deterministic heuristic fallback if the LLM times out or is unavailable.

### 2. Agent 2 — Evidence Retrieval
- **Role**: Multi-source evidence retriever combining external public food databases with the user's private knowledge base.
- **Input**: Structured `RetrievalRequest` containing product names, categories, and user ID.
- **Output**: Ranked list of `EvidenceObject` items with provenance metadata.
- **Data Sources**:
  1. `OpenFoodFactsSource`: Queries the Open Food Facts API by search query or barcode.
  2. `UserDocumentSource`: Performs rank-BM25 Information Retrieval over the authenticated user's isolated document chunks.

### 3. Agent 3 — Safety & Analysis
- **Role**: Deterministic safety and dietary verification engine written in strict Python logic.
- **Input**: `AnalysisRequest` with requested allergens, dietary rules, nutrient thresholds, and retrieved evidence.
- **Output**: `AnalysisResponse` with `safety_status` (`SUITABLE`, `UNSUITABLE`, `INSUFFICIENT_EVIDENCE`), risk level, and uncertainty warnings.
- **Safety Principle**: **Absence of evidence is NOT evidence of absence.** Gemini NEVER decides allergen safety. If ingredient data is incomplete, Agent 3 returns `INSUFFICIENT_EVIDENCE`.

### 4. Agent 4 — Recommendation & Response
- **Role**: Synthesizes verified evidence into clean, grounded user responses.
- **Input**: `ResponseRequest` with query, evidence, and `AnalysisResponse`.
- **Output**: Grounded answer text with structured citations (`📄 Document.pdf — page X` and `🌐 Open Food Facts — Barcode`).
- **Strict Grounding**: Never invents unverified ingredients, calories, or certifications absent from evidence.

---

## Persistent Knowledge Base & Information Retrieval

Authenticated users can upload food product guides, supplier spec sheets, allergen charts, and nutrition tables (`PDF`, `DOCX`, `TXT`, `MD`, `CSV` up to 10 MB) via **My Knowledge Base**.

- **No Message Attachments**: Users do **NOT** need to attach files to individual chat messages. Documents persist across sessions per authenticated user account.
- **Multi-Tenant Index Isolation**: Each user's BM25 search index is strictly isolated (`{"user_id": user_id}`). User A can **never** search, list, view, or delete User B's documents.
- **Prompt Injection Defense**: Retrieved document text is sanitized and wrapped inside `<retrieved_document_evidence>` XML tags so LLMs process it as **DATA ONLY**.

---

## Security & Privacy Safeguards

1. **Authentication & Authorization**: Password hashing (SHA-256 with salt), HS256 JWT access tokens, and strict user-id scoping on all MongoDB queries.
2. **Upload Security**: Extension validation, executable format blocking (`.exe`, `.sh`, `.py`, `.vbs`, etc.), size limit enforcement, and filename sanitization against path traversal (`../../`).
3. **Prompt Injection Mitigation**: Neutralizes adversarial prompts (e.g. *"Ignore previous instructions"*) and isolates untrusted document evidence.
4. **Secrets Management**: Credentials (`GEMINI_API_KEY`, `JWT_SECRET`, `MONGODB_URI`, `PASSWORD_SALT`) are read exclusively from environment variables.
5. **Rate Limiting & Logging**: In-memory sliding-window rate limiting on auth, chat, and document endpoints; sanitized logs omitting passwords, tokens, and raw health queries.

---

## Responsible AI Commitments

- **Deterministic Safety**: Safety decisions are governed by deterministic Python rules, not probabilistic LLM text generation.
- **Incomplete Data Protection**: Missing allergen or ingredient data produces `INSUFFICIENT_EVIDENCE`, never a false "suitable" guarantee.
- **Conflict Resolution**: Contradictory evidence between Open Food Facts and uploaded documents is explicitly highlighted to the user (`conflicting_evidence=True`).
- **Medical Disclaimer**: Standard food allergy disclaimers remind users to verify physical packaging for severe allergies.

---

## End-to-End API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/signup` | Register a new user account |
| `POST` | `/api/auth/signin` | Sign in and receive JWT bearer token |
| `GET` | `/api/auth/me` | Fetch authenticated user profile |
| `POST` | `/api/chat` | Main multi-agent assistant chat endpoint |
| `GET` | `/api/history` | List previous chat sessions for authenticated user |
| `GET` | `/api/history/{session_id}` | Load conversation turns for a session |
| `GET` | `/api/documents` | List stored documents in user's knowledge base |
| `POST` | `/api/documents/upload` | Upload PDF, DOCX, TXT, MD, or CSV document |
| `GET` | `/api/documents/{document_id}` | Fetch document metadata by ID |
| `DELETE` | `/api/documents/{document_id}` | Delete document and remove stored chunks |
| `POST` | `/api/documents/{document_id}/reindex` | Re-extract text and rebuild BM25 index |
| `GET` | `/api/commercialization/tiers` | Commercialization & pricing tier data |
| `GET` | `/health` | System health check endpoint |
| `GET` | `/docs` | Interactive Swagger OpenAPI documentation |

---

## Setup & Running Instructions

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & `npm`
- **MongoDB** (Local instance on `localhost:27017` or MongoDB Atlas URI)

### 1. Environment Setup
Copy `.env.example` to `.env` in the root directory:
```bash
cp .env.example .env
```
Fill in your configuration variables in `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET=evibite_super_secret_jwt_key_2026
PASSWORD_SALT=evibite_secure_salt_9988
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=evibite_db
```

### 2. Backend Setup & Startup
```bash
# Create and activate virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server with Uvicorn
python -m uvicorn backend.app.main:app --reload --port 8000
```
Backend will be live at: `http://localhost:8000` (OpenAPI Docs: `http://localhost:8000/docs`).

### 3. Frontend Setup & Startup
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build production bundle
npm run build
```
Frontend will be live at: `http://localhost:5173`.

---

## Testing Metrics & Validation

The complete backend test suite covers 178 unit, integration, and red-team acceptance tests across all 11 project phases.

```bash
# Run full pytest suite
python -m pytest

# Run Phase 11 acceptance scenario suite specifically
python -m pytest tests/test_phase11_acceptance.py

# Run Phase 10 security & red-team suite specifically
python -m pytest tests/test_redteam_phase10.py
```

### Test Results
- **Total Backend Tests**: **178 passed** out of 178 tests (100% pass rate).
- **Phase 11 Acceptance Scenarios**: **12 passed** out of 12 scenarios.
- **Frontend Build**: `npm run build` compiled cleanly with 0 errors.

---

## Known Limitations & Future Scope

1. **In-Memory BM25 Index Cache**: User BM25 indices are cached in memory. For enterprise deployments with millions of concurrent users, a distributed search cluster (e.g. Elasticsearch or OpenSearch) would replace local in-memory BM25 caches.
2. **Scanned PDF OCR**: PDF text extraction uses `pypdf`. Image-only scanned PDFs without embedded text layers require an external OCR pipeline (e.g., Tesseract or Cloud Vision API).

---

## Team Contributions

- **Member 1**: System Architecture, Central Orchestrator, Agent 1 (Triage & Routing), API routing, MongoDB database schemas, and conditional agent execution.
- **Member 2**: Agent 2 (Multi-Source Evidence Retrieval), Open Food Facts API integration, `UserDocumentSource` rank-BM25 document search engine.
- **Member 3**: Agent 3 (Safety & Analysis Engine), deterministic allergen normalization rules, dietary compliance verification, and conflict detection.
- **Member 4**: Agent 4 (Recommendation & Response Agent), strict grounded response synthesis, citation formatting, React frontend user interface, and user Knowledge Base UI.
