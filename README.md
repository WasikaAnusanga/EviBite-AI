# EviBite AI

**Multi-Agent Supermarket Product Intelligence Assistant**  
IT3041 – Information Retrieval & Web Analytics

EviBite AI is a multi-agent supermarket product intelligence system that helps users ask natural-language questions about packaged food products and receive evidence-grounded answers about product information, nutrition, allergens, dietary suitability, comparisons, and recommendations.

The core prototype uses **Open Food Facts** as its main product-information source. The system is designed as four cooperating agents connected through a shared backend, standardized JSON contracts, and HTTP/REST communication.

> **Current repository stage:** Project structure and shared contracts are being initialized first. Each member will implement their own assigned agent inside the prepared folder structure.

---

## 1. Project Objectives

EviBite AI is designed to demonstrate:

- Multi-agent AI behaviour
- Large Language Model integration
- Natural Language Processing
- Information Retrieval
- Nutrition and allergen analysis
- Grounded recommendation generation
- Agent-to-agent communication using HTTP/REST + JSON
- Security and Responsible AI practices
- Expandable supermarket data-source architecture

The core prototype uses Open Food Facts first. Retailer-specific data such as branch stock, price, promotions, and aisle information can be added later through additional retrieval-source adapters.

---

## 2. Multi-Agent Architecture

The system is designed as a **four-agent cooperative AI architecture** coordinated by a central Orchestration Engine and protected by a cross-cutting security layer.

### System Architecture Diagram

```mermaid
graph TD
    Client["User / Client App"] -->|POST /api/chat| Security["Cross-Cutting Security Layer"]
    Security -->|Sanitized Request| Orchestrator["Orchestrator Engine - Member 1"]
    
    subgraph Agent1["Agent 1: Triage & Routing - Member 1"]
        TriageService["Triage Service"]
        GeminiLLM["Gemini 2.5 Flash / OpenAI Extractor"]
        HeuristicFallback["Rule-Based Fallback Parser"]
        SafetyRules["Deterministic Safety & Risk Escalation"]
        
        TriageService --> GeminiLLM
        GeminiLLM -.->|Fallback if offline| HeuristicFallback
        TriageService --> SafetyRules
    end

    Orchestrator -->|1. Parse Query & Route| Agent1
    Agent1 -->|TriageOutput + Route Decision| Orchestrator

    subgraph Agent2["Agent 2: Product Retrieval - Member 2"]
        RetrievalService["Retrieval Agent Service"]
        SourceAdapter["ProductSource Interface Adapter"]
        OFF_API["Open Food Facts API"]
        StoreDB[("Future Supermarket Catalogue DB")]
        
        RetrievalService --> SourceAdapter
        SourceAdapter --> OFF_API
        SourceAdapter -.-> StoreDB
    end

    Orchestrator -->|2. Fetch Product Data| Agent2
    Agent2 -->|Evidence Candidates| Orchestrator

    subgraph Agent3["Agent 3: Nutrition & Allergen Analysis - Member 3"]
        AnalysisService["Analysis Agent Service"]
        AllergenChecker["Allergen Conflict Engine"]
        DietaryChecker["Dietary Suitability Engine"]
        UncertaintyEngine["Uncertainty & Safety Assigner"]
        
        AnalysisService --> AllergenChecker
        AnalysisService --> DietaryChecker
        AnalysisService --> UncertaintyEngine
    end

    Orchestrator -->|3. Safety & Nutrition Analysis| Agent3
    Agent3 -->|Analysis Findings & Safety Status| Orchestrator

    subgraph Agent4["Agent 4: Recommendation & Response - Member 4"]
        ResponseService["Response Generation Agent"]
        LLMGrounding["LLM Grounded Response Generator"]
        TopKRanker["Candidate Recommendation Ranker"]
        
        ResponseService --> TopKRanker
        ResponseService --> LLMGrounding
    end

    Orchestrator -->|4. Generate Grounded Answer| Agent4
    Agent4 -->|Final Evidence-Grounded Answer| Orchestrator

    Orchestrator -->|Trace ID + Execution Steps + Final Answer| Client
```

---

### Conditional Execution Paths

Not every query must pass through every agent. The Orchestrator engine dynamically triggers execution paths based on Triage intent and safety requirements:

1. **Simple Product Information**:
   `Triage` $\rightarrow$ `Retrieval` $\rightarrow$ `Response`
2. **Exact Barcode Lookup**:
   `Triage` $\rightarrow$ `Retrieval(Exact)` $\rightarrow$ `Response`
3. **Allergen / Nutrition / Dietary Safety Query**:
   `Triage` $\rightarrow$ `Retrieval` $\rightarrow$ `Analysis` $\rightarrow$ `Response` *(Forces RiskLevel.HIGH and analysis reasoning)*
4. **Product Recommendation & Comparison**:
   `Triage` $\rightarrow$ `Retrieval(Top-K)` $\rightarrow$ `Analysis` $\rightarrow$ `Recommendation/Response`
5. **Missing Product Clarification**:
   `Triage` $\rightarrow$ Stops immediately & requests user clarification.
6. **Out-of-Domain / Unsupported Query**:
   `Triage` $\rightarrow$ `Response` *(Direct polite refusal)*

---

## 3. Team Responsibilities

### Member 1 – Triage & Routing Agent

**Main responsibilities**

- Intent classification
- Entity / slot extraction
- Query decomposition
- Constraint extraction
- Clarification handling
- Risk-sensitive routing
- JSON schema validation
- Agent communication contracts
- Orchestration logic

**Main technical focus**

- NLP
- LLM structured output
- Pydantic validation
- FastAPI
- HTTP/REST + JSON communication

**Primary folder**

```text
backend/app/agents/triage/
backend/app/orchestration/
backend/app/models/
```

---

### Member 2 – Product Information Retrieval Agent

**Main responsibilities**

- Open Food Facts API integration
- Exact barcode lookup
- Product name / brand / category search
- Product-record normalization
- Candidate filtering
- Completeness scoring
- Top-K ranking
- Retrieval retry strategy
- Data-source abstraction for future supermarket connectors

**Main technical focus**

- Information Retrieval
- Open Food Facts
- Ranking and filtering
- Evidence normalization
- Retrieval evaluation

**Primary folder**

```text
backend/app/agents/retrieval/
backend/app/sources/
```

---

### Member 3 – Nutrition & Allergen Analysis Agent

**Main responsibilities**

- Allergen conflict detection
- Nutrition constraint checking
- Dietary suitability analysis
- Product comparisons
- Evidence completeness handling
- Uncertainty states
- Explainable reason generation
- Security implementation
- Responsible AI test cases

**Main technical focus**

- Rule-based reasoning
- Food-information safety
- Responsible AI
- Security middleware
- Evidence-based decision logic

**Primary folder**

```text
backend/app/agents/nutrition_allergen/
backend/app/security/
```

---

### Member 4 – Recommendation & Response Agent

**Main responsibilities**

- Grounded natural-language responses
- Recommendation ranking
- Alternative-product suggestions
- Refusal / uncertainty wording
- Bounded re-retrieval requests
- Frontend development
- Deployment
- Commercialization presentation support

**Main technical focus**

- LLM grounding
- Response generation
- Recommendation logic
- React / frontend
- Deployment

**Primary folder**

```text
backend/app/agents/recommendation_response/
frontend/
```

---

## 5. Commercialization Strategy & Pricing Model

EviBite AI implements a **dual B2C SaaS subscription and B2B Enterprise API licensing model**. Full commercialization details are available in [docs/COMMERCIALIZATION_STRATEGY.md](file:///c:/Users/Wasika/Desktop/New%20folder/Evi-Bite-AI/EviBite-AI/docs/COMMERCIALIZATION_STRATEGY.md).

### Pricing Overview

| Stream | Tier Name | Price | Key Features |
| :--- | :--- | :--- | :--- |
| **B2C Consumer** | **Free Tier** | **$0 / month** | 10 daily product scans/queries, basic allergen warnings, Nutri-Score & Eco-Score display. |
| **B2C Consumer** | **Shopper Premium** | **$4.99 / month** | Unlimited queries, Family Allergy Profiles (up to 5), custom nutrient goals, healthier recommendations. |
| **B2B Retailer** | **API Starter** | **$299 / month** | Up to 50,000 API calls/month, REST API access for grocery web apps & e-commerce search. |
| **B2B Retailer** | **Enterprise Retailer** | **$1,499 / month** | Up to 500,000 API calls/month, custom store DB adapter (live stock, price, aisle API), smart cart/kiosk SDK. |

Live API Tier Endpoint: `GET /api/commercialization/tiers`

---


## 4. Planned Repository Structure

```text
EviBite-AI/
│
├── backend/
│   ├── __init__.py
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   │
│       │   ├── triage/
│       │   │   └── __init__.py
│       │   │
│       │   ├── retrieval/
│       │   │   └── __init__.py
│       │   │
│       │   ├── nutrition_allergen/
│       │   │   └── __init__.py
│       │   │
│       │   └── recommendation_response/
│       │       └── __init__.py
│       │
│       ├── api/
│       │   └── routes/
│       │
│       ├── models/
│       │
│       ├── orchestration/
│       │
│       ├── sources/
│       │
│       └── security/
│
├── frontend/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── red_team/
│   └── evaluation_queries/
│
├── docs/
│   ├── architecture/
│   └── evaluation/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

At the initialization stage, folders belonging to Members 2, 3, and 4 can remain empty except for `__init__.py` or placeholder files. Their implementations should be added by the relevant member later.

---

## 5. Development Setup

### Prerequisites

Install:

- Python 3.11+ recommended
- Git
- VS Code or another IDE
- Node.js later when frontend development begins

Check Python:

```bash
python --version
```

Check Git:

```bash
git --version
```

---

## 6. Clone the Repository

```bash
git clone <repository-url>
cd EviBite-AI
```

---

## 7. Create a Python Virtual Environment

Create the virtual environment in the **project root**, not inside the `backend` folder.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

After activation, the terminal should show something similar to:

```text
(.venv)
```

---

## 8. Install Backend Dependencies

From the project root:

```bash
pip install -r requirements.txt
```

Backend dependencies include:

```text
fastapi
uvicorn[standard]
pydantic
pytest
google-genai
httpx
python-dotenv
```

Additional dependencies required by individual agents can be added later through reviewed pull requests.

---

## 9. Environment Variables

Copy the example environment file:

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### macOS / Linux

```bash
cp .env.example .env
```

Never commit `.env`.

Add your Gemini API Key to `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

*(Note: If no API key is provided, the backend automatically uses the built-in rule-based heuristic parser for local offline testing).*

---

## 10. Run the Backend

Run all backend commands from the project root:

```bash
uvicorn backend.app.main:app --reload
```

Default development URL:

```text
http://127.0.0.1:8000
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

Interactive FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 11. Initial API Endpoints

The project will eventually expose logical agent endpoints such as:

```text
POST /agents/triage
POST /agents/retrieval
POST /agents/analysis
POST /agents/response
```

At the initial repository stage, only endpoints that have actually been implemented should be enabled.

Do not create fake working implementations for other members merely to make the endpoints appear complete.

---

## 12. Standard Agent Communication

Agents communicate using:

```text
HTTP/REST + JSON
```

A shared message envelope will follow this general structure:

```json
{
  "trace_id": "REQ-2048",
  "from_agent": "triage",
  "to_agent": "retrieval",
  "message_type": "product_search",
  "payload": {},
  "timestamp": "2026-08-11T00:00:00Z"
}
```

Shared communication contracts belong in:

```text
backend/app/models/
```

Members should reuse the shared models instead of creating incompatible agent-specific message formats.

---

## 13. Shared Status Values

The planned shared statuses include:

```text
OK
FOUND
PARTIAL
NOT_FOUND
SUITABLE
UNSUITABLE
UNCERTAIN
INSUFFICIENT_EVIDENCE
NEED_MORE_EVIDENCE
ERROR
```

These statuses make communication predictable and independently testable.

---

## 14. Responsible AI Rule

The most important safety rule is:

> Missing product information must never be treated as proof that a product is safe.

For example:

```text
allergen field missing
```

does **not** mean:

```text
allergen-free
```

Incomplete allergen, ingredient, or nutrition evidence must produce an uncertainty state rather than an unsupported claim.

---

## 15. Testing

Run tests from the project root:

```bash
pytest
```

Planned test categories:

```text
tests/
├── unit/
├── integration/
├── red_team/
└── evaluation_queries/
```

Each member should add unit tests for their own agent.

Integration tests should be added when two or more agents begin communicating.

---

## 16. Git Workflow

Each member should work on their own branch.

Example:

```bash
git checkout -b member1-triage
```

Possible branch naming:

```text
member1-triage
member2-retrieval
member3-analysis
member4-response
```

Before starting work:

```bash
git checkout main
git pull
```

Then switch to the member branch:

```bash
git checkout member1-triage
```

Commit meaningful changes:

```bash
git add .
git commit -m "Implement triage output schema"
git push origin member1-triage
```

Changes should be integrated through pull requests where possible.

---

## 17. Important Development Rule

The repository structure and shared contracts should be initialized before all four agent implementations are developed.

Each member owns their own agent implementation.

Therefore, during the initial setup:

- Member 1 can initialize the common backend structure.
- Shared Pydantic models and communication contracts can be prepared centrally.
- Empty directories can be created for the other agents.
- Member 2 should implement Retrieval.
- Member 3 should implement Nutrition & Allergen Analysis.
- Member 4 should implement Recommendation & Response.
- One member should not write placeholder implementations that could later be mistaken for another member's contribution.

This keeps Git history and individual contribution evidence clear for the final viva.

---

## 18. Development Sequence

Recommended implementation order:

```text
1. Initialize repository structure
        ↓
2. Define shared JSON contracts
        ↓
3. Validate Open Food Facts fields
        ↓
4. Build Product Retrieval foundation
        ↓
5. Build Triage & Routing
        ↓
6. Build Nutrition & Allergen Analysis
        ↓
7. Build Recommendation & Response
        ↓
8. Integrate all agent endpoints
        ↓
9. Add security middleware
        ↓
10. Run integration and Responsible AI tests
        ↓
11. Build frontend
        ↓
12. Deployment and final evaluation
```

Some agents can be developed in parallel once the shared contracts are stable.

---

## 19. Core Technology Stack

| Component | Technology |
|---|---|
| Backend | Python + FastAPI |
| Validation | Pydantic |
| LLM | Approved LLM API |
| Product Data | Open Food Facts |
| IR | Python filtering, scoring, ranking, Top-K |
| Communication | HTTP/REST + JSON |
| Testing | Pytest |
| Frontend | React |
| Version Control | Git + GitHub |

---

## 20. Current Development Status

```text
Repository initialization        Completed
Shared project structure         Completed
Shared message contracts         Completed
Agent 1 – Triage & Routing       COMPLETED (Member 1 - Gemini LLM + Heuristics)
Orchestration Engine             COMPLETED (Member 1 - POST /api/chat)
Agent 2 – Retrieval              COMPLETED (Member 2 - Open Food Facts + Source Abstraction + Ranking + Caching)
Unit Test Suite                  COMPLETED (18/18 Pytest Passed)
Agent 3 – Analysis               Pending Teammate Integration (Member 3)
Agent 4 – Response               Pending Teammate Integration (Member 4)
Frontend UI                      Pending Teammate Integration (Member 4)
```

---

## 21. Guide for Teammates (Member 3, Member 4)

Welcome team! **Member 1** has completed **Agent 1 (Triage & Routing)**, the **Gemini LLM Extraction Engine**, the **Multi-Agent Orchestrator Engine**, and the **FastAPI REST API**.  
**Member 2** has completed **Agent 2 (Product Information Retrieval Agent)**, the **Open Food Facts API Adapter**, the **Data-Source Abstraction Layer**, **Field Completeness Scoring**, **Top-K Ranking**, and **Response Caching**.

The backend system runs end-to-end today with real Open Food Facts evidence retrieval! **Member 3** and **Member 4** can start building your assigned agents immediately by plugging into the prepared folder structure and inspecting the exact outputs produced by Agent 1 and Agent 2 below.

---

### What Member 1 Has Built for You (Agent 1 – Triage & Routing):

1. **Agent 1 Service** (`backend/app/agents/triage/`):
   - Automatically extracts user intent (`allergen_query`, `nutrition_query`, `comparison`, `product_search`, `barcode_lookup`, `dietary_query`, `recommendation`, `unknown`).
   - Extracts product names, brands, barcodes, categories, allergens, nutrients, dietary requirements, requested fields, and constraints.
   - Powered by **Gemini 2.5 Flash** structured extraction with robust rule-based fallback.
   - Escalates allergen queries to `RiskLevel.HIGH` and determines execution paths.

2. **Orchestrator Engine** (`backend/app/orchestration/orchestrator.py`):
   - Receives incoming user messages at `POST /api/chat`, passes data through Triage $\rightarrow$ Retrieval $\rightarrow$ Analysis $\rightarrow$ Response, tracks Request Trace IDs (`REQ-XXXXXX`), and logs execution steps.

#### Exact JSON Output Format Produced by Agent 1 (`triage_output`):

##### Example 1: Multi-Intent Allergen & Nutrition Query
**User Query**: *"I have a peanut allergy. Can I eat Nutella and how much sugar does it have?"*

```json
{
  "trace_id": "REQ-72718B96",
  "triage_status": "READY",
  "input_type": "natural_language",
  "original_query": "I have a peanut allergy. Can I eat Nutella and how much sugar does it have?",
  "primary_intent": "allergen_query",
  "secondary_intents": ["nutrition_query"],
  "products": [{"name": "Nutella", "brand": null, "barcode": null}],
  "category": null,
  "requested_fields": ["allergens", "ingredients", "sugars"],
  "allergens": ["peanut"],
  "dietary_requirements": [],
  "nutrients": ["sugars"],
  "risk_level": "HIGH",
  "routing": {
    "next_agent": "retrieval",
    "required_agents": ["retrieval", "analysis", "response"],
    "analysis_required": true
  }
}
```

---

### What Member 2 Has Built for You (Agent 2 – Product Information Retrieval):

1. **Data-Source Abstraction Layer** (`backend/app/sources/base.py`):
   - `ProductSource` interface with `get_by_barcode(barcode)` and `search(query, category, limit)` methods. This allows future supermarket catalog databases to sit alongside or replace Open Food Facts without changing agent contracts.

2. **Open Food Facts API Adapter** (`backend/app/sources/open_food_facts.py`):
   - Fetches real packaged food evidence from Open Food Facts REST API (`/api/v2/product/{barcode}.json` and `/cgi/search.pl`).
   - Normalizes raw product JSON into standard `EvidenceObject` schema.
   - In-memory response caching for fast, reliable demo performance and resilience against external API limits.

3. **Retrieval Agent Service** (`backend/app/agents/retrieval/service.py`):
   - Multi-strategy candidate retrieval (exact barcode, product name search, category/keyword search).
   - Dynamic field completeness scoring & Top-K candidate ranking.
   - Bounded query reformulation retry when initial search returns 0 candidates.
   - Returns explicit status: `FOUND`, `PARTIAL`, `NOT_FOUND`, or `ERROR`.

#### Exact Output Format Produced by Agent 2 (`RetrievalResponse` & `EvidenceObject`):

##### Example 1: Evidence Candidates Output for Nutella Search (`retrieval_res`)

```json
{
  "trace_id": "REQ-72718B96",
  "status": "FOUND",
  "candidates": [
    {
      "product_id": "off-3017620422003",
      "name": "Nutella Hazelnut Spread",
      "brand": "Ferrero",
      "barcode": "3017620422003",
      "categories": ["spreads", "hazelnut spreads", "sweet spreads"],
      "ingredients_text": "Sugar, palm oil, hazelnuts (13%), skimmed milk powder (8.7%), fat-reduced cocoa (7.4%), emulsifier: lecithins (soy), vanillin.",
      "allergens": ["hazelnut", "milk", "soy", "nuts"],
      "nutrition": {
        "sugars_g_100g": 56.3,
        "protein_g_100g": 6.3,
        "fat_g_100g": 30.9,
        "energy_kcal_100g": 539.0,
        "sodium_mg_100g": 43.0
      },
      "completeness": 0.95,
      "source": "open_food_facts"
    }
  ]
}
```

##### Example 2: Evidence Candidates Output for Cereal Comparison (`retrieval_res`)

```json
{
  "trace_id": "REQ-28DE19B4",
  "status": "FOUND",
  "candidates": [
    {
      "product_id": "off-7613035654321",
      "name": "Cheerios Honey & Oats Cereal",
      "brand": "Nestle",
      "barcode": "7613035654321",
      "categories": ["cereals", "breakfasts"],
      "ingredients_text": "Whole grain oat flour, sugar, oat bran, honey, salt.",
      "allergens": ["oats"],
      "nutrition": {
        "sugars_g_100g": 9.3,
        "protein_g_100g": 8.4,
        "fat_g_100g": 3.8,
        "energy_kcal_100g": 382.0
      },
      "completeness": 0.92,
      "source": "open_food_facts"
    },
    {
      "product_id": "off-5000167032104",
      "name": "Special K Original Cereal",
      "brand": "Kellogg's",
      "barcode": "5000167032104",
      "categories": ["cereals", "breakfasts"],
      "ingredients_text": "Rice, wheat gluten, sugar, barley malt extract, salt.",
      "allergens": ["wheat", "gluten", "barley"],
      "nutrition": {
        "sugars_g_100g": 14.0,
        "protein_g_100g": 14.0,
        "fat_g_100g": 1.5,
        "energy_kcal_100g": 375.0
      },
      "completeness": 0.95,
      "source": "open_food_facts"
    }
  ]
}
```

---

### How Remaining Members Can Build Their Workflows:

#### 🔹 Member 3: Nutrition & Allergen Analysis Agent (Agent 3)
* **Your Main Task**: Perform food safety reasoning over retrieved evidence candidates (`EvidenceObject`), detect allergen conflicts, evaluate dietary constraints, determine safety statuses (`SUITABLE`, `UNSUITABLE`, `UNCERTAIN`), and implement security middleware.
* **Where to code**:
  - Main Agent folder: `backend/app/agents/nutrition_allergen/`
  - Security folder: `backend/app/security/`
* **What you receive from Member 1 & Member 2**:
  - `AnalysisRequest`: `trace_id`, `primary_intent`, `allergens`, `nutrients`, `dietary_requirements`, and retrieved `evidence` candidates (list of `EvidenceObject` items shown above).
* **What you produce**:
  - `AnalysisResponse`: `safety_status` (`SUITABLE`, `UNSUITABLE`, `UNCERTAIN`), `risk_level`, `findings` (bullet points explaining reasons), and `uncertainty_reasons`.
* **How to connect**:
  - Connect your `backend/app/agents/nutrition_allergen/service.py` to `stub_analysis_service()` in `backend/app/agents/agent_stubs.py` or directly in `orchestrator.py`.

---

#### 🔹 Member 4: Recommendation & Response Agent (Agent 4)
* **Your Main Task**: Generate natural-language grounded responses (no unsupported factual claims), rank recommendations, and format refusal/uncertainty wording. *(Note: Frontend UI development will be built together as a team later).*
* **Where to code**:
  - Main Agent folder: `backend/app/agents/recommendation_response/`
* **What you receive from Member 1, 2 & 3**:
  - `ResponseRequest`: `trace_id`, `query`, `intent`, `triage_status`, `evidence` (from Member 2), and `analysis` (from Member 3).
* **What you produce**:
  - `ResponseResponse`: User-facing `answer` string grounded in verified evidence.
* **How to connect**:
  - Connect your `backend/app/agents/recommendation_response/service.py` to `stub_response_service()` in `backend/app/agents/agent_stubs.py` or directly in `orchestrator.py`.

---

## 22. Contributors

| Member | Responsibility | Status |
|---|---|---|
| Member 1 | Triage & Routing Agent + Communication / Orchestration | **Completed** |
| Member 2 | Product Information Retrieval Agent + Open Food Facts Source | **Completed** |
| Member 3 | Nutrition & Allergen Analysis Agent + Security / Responsible AI | Pending Integration |
| Member 4 | Recommendation & Response Agent + Frontend / Deployment | Pending Integration |

Replace `Member 1`, `Member 2`, etc. with actual names before final submission.

---

## 23. Project Scope Limitation

The first version of EviBite AI uses Open Food Facts for packaged-product information.

The MVP does not currently provide:

- Live supermarket stock
- Branch-specific availability
- Real supermarket prices
- Promotions
- Aisle locations
- Checkout or payment functionality

The retrieval architecture is intended to allow supermarket-specific sources to be added later without redesigning the four-agent architecture.

