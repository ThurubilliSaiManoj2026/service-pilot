# api.py
# ─────────────────────────────────────────────────────────────────────────────
# ServicePilot — FastAPI Backend Server
#
# This file wraps the entire four-agent LangGraph pipeline as a REST API.
# The React frontend will communicate exclusively with these endpoints.
#
# Architecture:
#   POST /api/analyze  → Runs the full pipeline, returns all four agent outputs
#   GET  /api/health   → Health check endpoint for deployment monitoring
#   GET  /api/examples → Returns the five example incidents for the frontend
#
# Why FastAPI specifically?
#   FastAPI is the most widely used Python API framework in 2026 for AI/ML
#   applications. It provides automatic OpenAPI documentation, Pydantic
#   validation (which you are already using), async support, and CORS
#   middleware — everything needed to serve a React frontend correctly.
# ─────────────────────────────────────────────────────────────────────────────

import os
import logging
import time
from datetime import datetime

# Suppress all noise before any imports
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"]     = "False"
logging.getLogger("chromadb").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph import run_pipeline, COLLECTION


# ── FastAPI app initialization ────────────────────────────────────────────────

app = FastAPI(
    title       = "ServicePilot API",
    description = "Multi-Agent ITIL Process Automation — Four-Agent Pipeline",
    version     = "1.0.0"
)

# CORS middleware is essential when your React frontend (running on port 3000
# or 5173 during development) calls this FastAPI server (running on port 8000).
# Without CORS, browsers block all cross-origin requests as a security measure.
# We allow all origins here for development — you would restrict this in
# production to your specific frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"]
)


# ── Request and Response schemas ──────────────────────────────────────────────

class IncidentRequest(BaseModel):
    """The JSON body the React frontend sends to the /api/analyze endpoint."""
    incident_description: str


class TriageData(BaseModel):
    """Structured triage result returned to the frontend."""
    severity               : str
    affected_service       : str
    category               : str
    business_impact        : str
    recommended_team       : str
    initial_diagnosis      : str
    estimated_resolution_time: str


class SimilarIncident(BaseModel):
    """A single retrieved past incident from the knowledge base."""
    incident_id        : str
    title              : str
    severity           : str
    category           : str
    affected_service   : str
    root_cause         : str
    resolution_steps   : list[str]
    preventive_measures: list[str]
    resolved_in_minutes: str
    assigned_team      : str
    similarity_score   : float


class ResolutionSynthesis(BaseModel):
    """The LLM synthesis of resolution steps from similar incidents."""
    primary_reference              : str
    confidence_level               : str
    confidence_reason              : str
    key_differences                : str
    estimated_total_resolution_time: str
    recommended_steps              : list[str]


class AnalysisResponse(BaseModel):
    """
    The complete JSON response returned to the React frontend after
    the full four-agent pipeline has executed. All four agent outputs
    are included in a single response object so the frontend can
    populate all tabs simultaneously without multiple API calls.
    """
    success           : bool
    execution_time_sec: float
    timestamp         : str
    triage            : TriageData
    similar_incidents : list[SimilarIncident]
    synthesis         : ResolutionSynthesis
    rca_report        : str
    cab_document      : str


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint. Called by deployment platforms to verify the
    service is running. Returns the current status of all system components.
    """
    return {
        "status"          : "healthy",
        "timestamp"       : datetime.now().isoformat(),
        "vector_store"    : f"{COLLECTION.count()} incidents loaded",
        "pipeline"        : "ready",
        "model"           : "BAAI/bge-base-en-v1.5",
        "llm"             : "llama-3.3-70b-versatile via Groq"
    }


@app.get("/api/examples")
async def get_examples():
    """
    Returns the five example incidents displayed in the frontend sidebar.
    Keeping these in the backend means you can update them without
    redeploying the frontend.
    """
    return {
        "examples": [
            {
                "id"         : 1,
                "title"      : "Database Connection Pool Exhausted",
                "category"   : "Database",
                "severity"   : "P1",
                "description": (
                    "Production MySQL database for our e-commerce client is rejecting "
                    "all new connections since 3:15 AM IST. Application servers are "
                    "throwing 'Too many connections' errors on every request. The checkout "
                    "flow, order history, and user login are all completely broken. "
                    "Approximately 25,000 users are affected and revenue loss is estimated "
                    "at Rs 3 lakhs per hour."
                )
            },
            {
                "id"         : 2,
                "title"      : "Kubernetes Pod CrashLoopBackOff",
                "category"   : "Application",
                "severity"   : "P1",
                "description": (
                    "Production Kubernetes cluster has multiple pods in CrashLoopBackOff "
                    "state. The payment processing service is completely down. All three "
                    "replicas are crashing every 90 seconds. Error logs show the pods "
                    "cannot find a required Kubernetes Secret that holds payment gateway "
                    "credentials. Customers cannot complete any purchases."
                )
            },
            {
                "id"         : 3,
                "title"      : "SSL Certificate Expired",
                "category"   : "Infrastructure",
                "severity"   : "P1",
                "description": (
                    "SSL certificate expired on our main client domain at midnight. "
                    "All HTTPS traffic is now failing with security errors in browsers. "
                    "API consumers are receiving TLS handshake failures. The affected "
                    "domain serves 50,000 daily active users and processes Rs 80 lakhs "
                    "in daily transactions."
                )
            },
            {
                "id"         : 4,
                "title"      : "Active Security Breach — PII Exposure",
                "category"   : "Security",
                "severity"   : "P1",
                "description": (
                    "Security team detected unauthorized API calls from an unknown IP "
                    "reading from our customer PII database table. Approximately 10,000 "
                    "customer records may have been accessed. The activity started 2 hours "
                    "ago and is still ongoing. GDPR breach notification window is now active."
                )
            },
            {
                "id"         : 5,
                "title"      : "Network Latency Cascade Failure",
                "category"   : "Network",
                "severity"   : "P1",
                "description": (
                    "Average API response times across all microservices spiked from 120ms "
                    "baseline to over 8,000ms. The spike originated in the network layer "
                    "between the application tier and data tier. Services began timing out "
                    "waiting for downstream responses, triggering a cascade failure across "
                    "14 dependent microservices including order management and inventory."
                )
            }
        ]
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_incident(request: IncidentRequest):
    """
    The core endpoint. Receives a raw incident description from the React
    frontend, runs the complete four-agent pipeline, and returns all outputs.

    This endpoint is called exactly once per user submission. The pipeline
    runs synchronously — the response is returned only after all four agents
    have completed. The React frontend shows a loading animation during this
    15-20 second window.

    Error handling: if any agent fails (LLM API error, parsing error, etc.),
    a 500 HTTP error is returned with the specific error message so the
    frontend can display a meaningful error state to the user.
    """

    # Validate that the description is not empty after stripping whitespace
    description = request.incident_description.strip()
    if not description:
        raise HTTPException(
            status_code = 400,
            detail      = "Incident description cannot be empty."
        )

    if len(description) < 20:
        raise HTTPException(
            status_code = 400,
            detail      = "Please provide a more detailed incident description (minimum 20 characters)."
        )

    # Record start time so we can report total execution time to the frontend
    start_time = time.time()

    try:
        # Run the complete four-agent pipeline
        # This is the same function called by the Streamlit app — the pipeline
        # itself is unchanged, only the interface layer (API vs Streamlit) differs
        state = run_pipeline(description)

    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail      = f"Pipeline execution failed: {str(e)}"
        )

    execution_time = round(time.time() - start_time, 2)

    # Extract triage result from the pipeline state
    triage = state.triage_result

    # Extract similar incidents and synthesis from Agent 2's output
    retrieved  = state.similar_incidents or {}
    raw_incs   = retrieved.get("retrieved_incidents", [])
    synthesis  = retrieved.get("synthesis", {})

    # Structure similar incidents for the response schema
    similar_incidents_structured = [
        SimilarIncident(
            incident_id         = inc.get("incident_id", ""),
            title               = inc.get("title", ""),
            severity            = inc.get("severity", ""),
            category            = inc.get("category", ""),
            affected_service    = inc.get("affected_service", ""),
            root_cause          = inc.get("root_cause", ""),
            resolution_steps    = inc.get("resolution_steps", []),
            preventive_measures = inc.get("preventive_measures", []),
            resolved_in_minutes = str(inc.get("resolved_in_minutes", "N/A")),
            assigned_team       = inc.get("assigned_team", "N/A"),
            similarity_score    = inc.get("similarity_score", 0.0)
        )
        for inc in raw_incs
    ]

    # Structure synthesis for the response schema
    synthesis_structured = ResolutionSynthesis(
        primary_reference               = synthesis.get("primary_reference", "N/A"),
        confidence_level                = synthesis.get("confidence_level", "N/A"),
        confidence_reason               = synthesis.get("confidence_reason", ""),
        key_differences                 = synthesis.get("key_differences", ""),
        estimated_total_resolution_time = synthesis.get(
                                              "estimated_total_resolution_time", "N/A"),
        recommended_steps               = synthesis.get("recommended_steps", [])
    )

    # Build and return the complete response
    return AnalysisResponse(
        success            = True,
        execution_time_sec = execution_time,
        timestamp          = datetime.now().isoformat(),
        triage             = TriageData(
            severity                 = triage.severity,
            affected_service         = triage.affected_service,
            category                 = triage.category,
            business_impact          = triage.business_impact,
            recommended_team         = triage.recommended_team,
            initial_diagnosis        = triage.initial_diagnosis,
            estimated_resolution_time= triage.estimated_resolution_time
        ),
        similar_incidents  = similar_incidents_structured,
        synthesis          = synthesis_structured,
        rca_report         = state.rca_report or "",
        cab_document       = state.cab_document or ""
    )


# ── Run the server ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "api:app",
        host   = "0.0.0.0",
        port   = port,
        reload = False
    )