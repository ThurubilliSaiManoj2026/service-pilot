<div align="center">

<img src="https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/FastAPI-0.115-green?style=for-the-badge&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
<img src="https://img.shields.io/badge/LangGraph-0.4-orange?style=for-the-badge" />
<img src="https://img.shields.io/badge/ChromaDB-0.6-purple?style=for-the-badge" />
<img src="https://img.shields.io/badge/LLaMA_3.3_70B-Groq-red?style=for-the-badge" />

<br />
<br />

<img width="120" src="https://raw.githubusercontent.com/ThurubilliSaiManoj2026/service-pilot/main/frontend/public/favicon.svg" alt="ServicePilot Logo" />

<h1>ServicePilot</h1>

<p align="center">
  <strong>Multi-Agent ITIL Process Automation System</strong>
  <br />
  From raw incident plain description to triage classification, resolution synthesis,
  RCA report, and CAB change request. Fully automated in under 30 seconds.
  <br />
  <br />
  <a href="#demo">View Demo</a>
  ·
  <a href="#installation">Quick Start</a>
  ·
  <a href="#api-reference">API Docs</a>
  ·
  <a href="#architecture">Architecture</a>
</p>

</div>

---

## Table of Contents

- [About the Project](#about-the-project)
- [Problem Statement](#problem-statement)
- [Objectives](#objectives)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Agent Pipeline Details](#agent-pipeline-details)
- [Knowledge Base](#knowledge-base)
- [Challenges and Solutions](#challenges-and-solutions)
- [Author](#author)
- [License](#license)

---

## About the Project

ServicePilot is an advanced **Multi-Agent AI system** built to automate the
complete ITIL (IT Infrastructure Library) incident management lifecycle. It is
designed to solve a problem that every IT service company — TCS, Infosys, Wipro,
Accenture, Cognizant — deals with daily: the enormous manual effort required to
triage incidents, find historical resolution patterns, write Root Cause Analysis
documents, and prepare Change Advisory Board requests.

This project was built as a portfolio-grade demonstration of real-world AI
engineering — combining LLM orchestration, semantic vector search, REST API
design, and a production-quality React frontend into a single cohesive system
that mirrors how enterprise ITSM automation is actually architected.

**What makes ServicePilot different from a generic chatbot:**

- It uses **LangGraph** for multi-agent orchestration with shared state passing
  between agents — each agent builds on the structured output of the previous one.
- It uses **BGE-Base dense retrieval embeddings** for semantic search, not
  keyword matching. An incident about "users cannot log in" correctly retrieves
  "authentication service returning 502 Bad Gateway" because the model understands
  meaning, not just vocabulary overlap.
- It produces **structured, deliverable-quality documents** — the RCA and CAB
  outputs are formatted to ITIL standards, not generic summaries.

---

## Problem Statement

In IT service delivery organizations, every P1/P2 incident triggers a cascade of
manual work:

| Manual Task | Time Required (Current) |
|---|---|
| Initial triage and severity classification | 30–45 minutes |
| Searching historical incident records | 1–2 hours |
| Writing the Root Cause Analysis document | 2–4 hours |
| Preparing the CAB change request | 1–2 hours |
| **Total per incident** | **4–8 hours** |

With thousands of incidents per month across enterprise client portfolios,
this represents an enormous drain on senior engineering time. ServicePilot
reduces this entire lifecycle to **under 30 seconds**.

---

## Objectives

1. Automate the complete ITIL incident management lifecycle using specialized AI agents
2. Demonstrate production-grade multi-agent LLM orchestration using LangGraph
3. Implement semantic vector search using BGE-Base dense retrieval embeddings
4. Build a domain-specific knowledge base of 100 realistic ITIL incident records
5. Produce structured, client-deliverable ITIL documents (RCA, CAB RFC)
6. Expose the pipeline through a production-ready FastAPI REST interface
7. Deliver a polished React frontend with professional SaaS design

---

## Key Features

- **Agent 1 — Triage:** Classifies any incident into P1–P4 severity with
  affected service identification, category mapping, business impact analysis,
  initial diagnosis, and resolver team assignment
- **Agent 2 — Resolution Suggester:** Performs exhaustive BGE-Base cosine
  similarity search across 100 historical incidents, retrieves the top 3 most
  semantically relevant past cases, and synthesizes tailored resolution steps
  using LLaMA 3.3 70B with citation of source incidents
- **Agent 3 — RCA Generator:** Produces complete Root Cause Analysis
  documents (900+ words) with Executive Summary, Incident Timeline, Five Whys
  causal chain analysis, Impact Assessment, Preventive Measures, Lessons
  Learned, and Action Items Table
- **Agent 4 — CAB RFC Generator:** Generates formal Change Advisory Board
  Request for Change documents with Risk Assessment, Implementation Plan,
  Rollback Procedure, Stakeholder Approval Matrix, and Communication Plan
- **PDF Export:** Both RCA and CAB documents export as professionally
  formatted PDFs (white background, Helvetica headings, Times Roman body,
  embedded tables) indistinguishable from human-authored reports
- **ITIL Knowledge Base:** 100 hand-crafted realistic incident records
  spanning 10 IT domains (Database, Application, Network, Infrastructure,
  Security, Cloud, DevOps, Data Engineering, ML Platform, Identity)
- **REST API:** FastAPI backend with OpenAPI documentation at `/docs`,
  health check endpoint, and examples endpoint
- **React Frontend:** Clean white SaaS design with Framer Motion transitions,
  green/black accent palette, five pre-loaded example incidents, and full
  four-tab results display

---

## Tech Stack

### Backend / AI Pipeline

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.12 | Core language |
| LangGraph | 0.4.1 | Multi-agent pipeline orchestration |
| LangChain | 0.3.25 | LLM abstraction and message formatting |
| LangChain-Groq | 0.3.2 | Groq LLaMA 3.3 70B integration |
| sentence-transformers | 3.4.1 | BGE-Base embedding model |
| BAAI/bge-base-en-v1.5 | — | 768-dim dense retrieval embeddings |
| ChromaDB | 0.6.3 | Persistent vector store |
| FastAPI | 0.115.6 | REST API framework |
| Uvicorn | 0.34.0 | ASGI production server |
| Pydantic | 2.11.3 | Data validation and structured output |
| python-dotenv | 1.1.0 | Environment variable management |
| Streamlit | 1.44.1 | Legacy Streamlit demo interface (app.py) |

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| React | 18 | UI framework |
| Vite | 8.0.3 | Build tool and dev server |
| Tailwind CSS | — | Utility-first styling |
| Framer Motion | — | Animations and transitions |
| Axios | — | HTTP client for API calls |
| jsPDF | — | Client-side PDF generation |
| jspdf-autotable | — | Table rendering in PDF exports |
| Lucide React | — | Icon library |

### Infrastructure / LLM

| Technology | Purpose |
|---|---|
| Groq Cloud | LLM inference for LLaMA 3.3 70B (free tier) |
| BAAI/bge-base-en-v1.5 | Local dense retrieval (no API key required) |

---

## Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                       │
│           (Vite + Tailwind + Framer Motion)             │
│                   localhost:5173                        │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP POST /api/analyze
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                       │
│                    api.py                               │
│                   localhost:8000                        │
└──────────────────────┬──────────────────────────────────┘
                       │ run_pipeline(incident_description)
                       ▼
┌─────────────────────────────────────────────────────────┐
│              LangGraph Pipeline (graph.py)              │
│                                                         │
│  ┌──────────┐   ┌────────────┐   ┌──────┐   ┌────────┐  │
│  │ Triage   |──▶│ Resolution │──▶│ RCA  │──▶│  CAB  │  |
│  │ Agent 1  │   │  Agent 2   │   │Agent3│   │ Agent 4│  │
│  └──────────┘   └────────────┘   └──────┘   └────────┘  │
│       │               │                                 │
│       │         ┌─────▼──────────────┐                  │
│       │         │   ChromaDB         │                  │
│       │         │   Vector Store     │                  │
│       │         │   (100 incidents)  │                  │
│       │         │   BGE-Base embeds  │                  │
│       │         └────────────────────┘                  │
│       │                                                 │
│       └──────────────────────────────────────────────▶  │
│                  ServicePilotState (shared)             │
│     {incident_description, triage_result,               │
│      similar_incidents, rca_report, cab_document}       │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │     Groq Cloud API      │
         │   LLaMA 3.3 70B         │
         │   (4 LLM calls total)   │
         └─────────────────────────┘
```

**State Flow:** A single `ServicePilotState` Pydantic object is created at
pipeline entry with only `incident_description` populated. Each LangGraph node
(agent) receives the full state, performs its work, and returns an enriched
state with its output field populated. By the time the graph reaches `END`,
all four fields are populated and the complete state is returned to the API.

---

## Folder Structure
```
service_pilot/
│
├── agents/                          # LangGraph agent implementations
│   ├── __init__.py
│   ├── triage_agent.py              # Agent 1: P1-P4 severity classification
│   ├── resolution_agent.py          # Agent 2: RAG-based resolution synthesis
│   ├── rca_agent.py                 # Agent 3: Root Cause Analysis generation
│   └── cab_agent.py                 # Agent 4: CAB RFC document generation
│
├── data/
│   └── incidents.json               # 100 ITIL incident records (knowledge base)
│
├── utils/
│   ├── __init__.py
│   └── chroma_utils.py              # BGE embedding + ChromaDB vector store
│
├── frontend/                        # React + Vite frontend application
│   ├── src/
│   │   ├── App.jsx                  # Complete frontend (single-file architecture)
│   │   ├── main.jsx                 # React entry point
│   │   └── index.css                # Tailwind CSS import
│   ├── public/
│   │   └── favicon.svg
│   ├── package.json
│   ├── vite.config.js               # Vite config with /api proxy to port 8000
│   └── index.html
│
├── api.py                           # FastAPI REST API server (production entry)
├── app.py                           # Streamlit demo interface (alternative UI)
├── graph.py                         # LangGraph pipeline definition
├── requirements.txt                 # Python dependencies (pinned versions)
├── .env                             # Environment variables (NOT committed)
├── .gitignore
└── README.md
```

---

## Installation

### Prerequisites

- Python 3.12+
- Node.js 18+
- A free [Groq API key](https://console.groq.com)

### 1. Clone the repository
```bash
git clone https://github.com/ThurubilliSaiManoj2026/service-pilot.git
cd service-pilot
```

### 2. Set up the Python backend
```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install all Python dependencies
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```

Get your free Groq API key at [console.groq.com](https://console.groq.com) —
no credit card required, generous free tier.

### 4. Set up the React frontend
```bash
cd frontend
npm install
cd ..
```

### 5. First run — vector store initialization

On the first run, the system will:
1. Download the `BAAI/bge-base-en-v1.5` embedding model (~438MB, cached locally)
2. Embed all 100 incidents from `data/incidents.json`
3. Persist the vector index to `vectorstore/`

Subsequent runs load from disk in under 2 seconds.

---

## Usage

ServicePilot requires two processes running simultaneously.

### Terminal 1 — Start the FastAPI backend
```bash
python api.py
```

Expected output:
```
[ServicePilot] Loading BGE-Base embedding model...
[ServicePilot] Model ready.
[ServicePilot] Initializing vector store...
[VectorStore] ✓ 100 incidents loaded.
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 — Start the React frontend
```bash
cd frontend
npm run dev
```

Expected output:
```
VITE v8.0.3  ready in 350ms
→  Local:   http://localhost:5173/
```

Open `http://localhost:5173` in your browser.

### Running the Pipeline

1. Open the browser at `http://localhost:5173`
2. Click **Get Started** or **Analyze an Incident**
3. Enter any IT incident description (minimum 20 characters)
4. Click **Run ITIL Pipeline**
5. Wait 15–30 seconds for all four agents to complete
6. Explore results in the four tabs: Triage · Incidents · RCA · CAB RFC
7. Download professional PDFs from the RCA and CAB RFC tabs

### Using the Streamlit Interface (Alternative)
```bash
streamlit run app.py --server.fileWatcherType none
```

Access at `http://localhost:8501`

---

## API Reference

The FastAPI server exposes three endpoints, documented interactively at
`http://localhost:8000/docs`.

### `GET /api/health`

Returns system health status.
```json
{
  "status": "healthy",
  "vector_store": "100 incidents loaded",
  "pipeline": "ready",
  "model": "BAAI/bge-base-en-v1.5",
  "llm": "llama-3.3-70b-versatile via Groq"
}
```

### `GET /api/examples`

Returns the five pre-loaded example incidents for the frontend UI.

### `POST /api/analyze`

The core endpoint. Runs the complete four-agent pipeline.

**Request body:**
```json
{
  "incident_description": "Production MySQL database is rejecting all connections..."
}
```

**Response (abbreviated):**
```json
{
  "success": true,
  "execution_time_sec": 22.4,
  "triage": {
    "severity": "P1",
    "affected_service": "MySQL Production Database",
    "category": "Database",
    "business_impact": "...",
    "recommended_team": "Database Administration",
    "initial_diagnosis": "...",
    "estimated_resolution_time": "30-60 minutes"
  },
  "similar_incidents": [...],
  "synthesis": {
    "primary_reference": "INC-001",
    "confidence_level": "High",
    "recommended_steps": [...]
  },
  "rca_report": "=== EXECUTIVE SUMMARY ===\n...",
  "cab_document": "CHANGE REQUEST HEADER\n..."
}
```

---

## Agent Pipeline Details

### Agent 1 — Triage Agent (`agents/triage_agent.py`)

Uses `LLaMA 3.3 70B` with a structured ITIL incident management system prompt.
Outputs a Pydantic-validated `TriageOutput` object with seven fields. The LLM
is constrained to return pure JSON, which is parsed and validated before being
stored in the pipeline state.

**Severity classification rules:**
- **P1** — Complete outage, all users affected, revenue impact occurring now
- **P2** — Major degradation, significant users affected, no workaround
- **P3** — Partial impact, limited users, workaround available
- **P4** — Minor or cosmetic issue, single user or low-priority system

### Agent 2 — Resolution Agent (`agents/resolution_agent.py`)

**Phase 1 — Retrieval:** The original incident description is encoded into a
768-dimensional vector using `BAAI/bge-base-en-v1.5`. The BGE query prefix
`"Represent this sentence for searching relevant passages: "` is prepended
to the query (but not to stored documents) — this is BGE's asymmetric encoding
contract and is critical for high similarity scores. All 100 stored incident
vectors are retrieved from ChromaDB and cosine similarity is computed
exhaustively as a matrix multiply `(100×768) @ (768,)`. Top-3 results
by cosine similarity are returned.

**Phase 2 — Synthesis:** The top-3 retrieved incidents (with full resolution
steps, root causes, and preventive measures) are passed to `LLaMA 3.3 70B`
along with the triage classification. The LLM synthesizes a tailored resolution
recommendation citing which past incidents influenced each step.

### Agent 3 — RCA Agent (`agents/rca_agent.py`)

Receives the complete accumulated context from Agents 1 and 2. Uses
`LLaMA 3.3 70B` with `temperature=0.3` (slightly higher than triage for
more natural long-form prose) to generate an 8-section ITIL-compliant RCA
document: Executive Summary, Incident Timeline, Root Cause Analysis (with
Five Whys), Impact Assessment, Resolution Summary, Preventive Measures,
Lessons Learned, Action Items Table.

### Agent 4 — CAB Agent (`agents/cab_agent.py`)

The final agent receives all three previous agents' outputs. Produces a formal
ITIL Request for Change document covering: Change Request Header, Change
Description, Justification and Business Case, Risk Assessment (with probability
and impact scoring), Implementation Plan, Rollback Plan, Testing and Validation,
Stakeholder Approval Matrix, and Communication Plan.

---

## Knowledge Base

The `data/incidents.json` file contains **100 hand-crafted realistic ITIL
incident records** covering 10 domains:

| Domain | Incidents | Examples |
|---|---|---|
| Database | 15 | Connection pool exhaustion, tablespace full, replication failure |
| Application | 18 | Memory leaks, CrashLoopBackOff, race conditions |
| Network | 10 | Latency spikes, DNS failures, firewall misconfigurations |
| Infrastructure | 12 | SSL expiry, Terraform corruption, NTP drift |
| Security | 15 | Ransomware, SQL injection, supply chain attacks |
| Cloud | 12 | S3 misconfigurations, Lambda throttling, DR failures |
| DevOps | 8 | CI/CD failures, Docker disk exhaustion, deployment errors |
| Data Engineering | 5 | Spark OOM, ETL corruption, schema migration failures |
| Identity | 5 | AD sync failures, Conditional Access, SSH compromise |

Each record contains: `incident_id`, `title`, `description`, `severity`,
`affected_service`, `category`, `resolution_steps` (6–9 numbered steps),
`root_cause`, `preventive_measures`, `resolved_in_minutes`, `assigned_team`.

---

## Challenges and Solutions

### Challenge 1: BGE Embedding Similarity Scores Stuck at 35-50%

**Root cause:** Initial implementation used `all-MiniLM-L6-v2` with a 256-token
limit. The 150-200 token document vectors were geometrically spread across too
many concepts, causing the cosine angle between short queries and long documents
to plateau at ~60% regardless of semantic relevance.

**Solution:** Migrated to `BAAI/bge-base-en-v1.5` (768-dim) and embedded only
incident titles (10-15 tokens) rather than full document text. Short-vs-short
vector comparison produces cosine similarity of 75-95% for genuinely relevant
matches. Also applied BGE's asymmetric encoding contract — query prefix prepended
at search time, not at ingestion — which is the critical detail most
implementations miss and costs ~15-20% similarity score.

### Challenge 2: Cross-Encoder Re-Ranking Producing Wrong Results

**Root cause:** `ms-marco-MiniLM-L-6-v2` was trained on Bing web search
query-document pairs. For IT incident domain, it pattern-matched surface keywords
("production") rather than semantic meaning, causing it to rank INC-014 (cloud
storage costs) above INC-002 (authentication failure) for a "users cannot log in"
query.

**Solution:** Abandoned cross-encoder reranking entirely. Exhaustive BGE-Base
cosine similarity across all 100 incidents with correct asymmetric encoding
produces semantically correct rankings with scores in the 65-85% range — which
in vector space terms represents a strong retrieval signal, even if the raw
percentage looks modest to a human reader.

### Challenge 3: ChromaDB v0.6.0 API Breaking Change

**Root cause:** `client.list_collections()` changed from returning collection
objects with `.name` attributes to returning plain strings in v0.6.0.

**Solution:** Changed `[col.name for col in client.list_collections()]` to
`client.list_collections()` — a one-line fix once the error was diagnosed.

### Challenge 4: LangGraph State Type Mismatch

**Root cause:** `ServicePilotState.similar_incidents` was typed as `list | None`
but the resolution agent stored a `dict` (`{"retrieved_incidents": [...],
"synthesis": {...}}`). Pydantic raised a `ValidationError` on every pipeline run.

**Solution:** Changed the type annotation to `dict | None`. Reinforced the
importance of keeping the shared state schema synchronized with what each agent
actually produces.

### Challenge 5: PDF Looking Like a Web UI

**Root cause:** The initial `generatePDF` implementation used green-colored
headings, gradient fills, and colored table headers — appropriate for a dark-mode
web application but completely unsuitable for a formal corporate document.

**Solution:** Complete rewrite of `generatePDF` using only Helvetica Bold black
headings with thin underline rules, Times New Roman black body text, light gray
table headers, no colors anywhere, and orphan protection for headings
(35mm minimum space required before a heading is placed on the current page).

---

## Author

**Thurubilli Sai Manoj**

B.Tech Computer Science Engineering (AI/ML Specialization)  
Woxsen University, Hyderabad — Class of 2026

- GitHub: [@ThurubilliSaiManoj2026](https://github.com/ThurubilliSaiManoj2026)
- LinkedIn: _(add your LinkedIn URL)_

---

## License

Distributed under the MIT License.
```
MIT License

Copyright (c) 2026 Thurubilli Sai Manoj

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

<div align="center">

Built with precision by **Thurubilli Sai Manoj** · ServicePilot © 2026

*Automate to Accelerate IT.*

</div>
