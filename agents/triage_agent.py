# agents/triage_agent.py
# ─────────────────────────────────────────────────────────────────────────────
# ServicePilot — Triage Agent (Agent 1)
#
# Responsibility: Receive a raw incident description and produce a structured
# ITIL-compliant classification containing severity, affected service, category,
# business impact, resolver team, and initial diagnosis.
#
# Design pattern: The agent uses Groq's LLaMA 3.3 70B model with a carefully
# engineered system prompt that constrains the LLM to think like an experienced
# ITIL incident manager. The output is validated by Pydantic before being
# returned, ensuring downstream agents always receive well-formed data.
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables from .env file
# This makes GROQ_API_KEY available via os.environ
load_dotenv()


# ── Pydantic output schema ────────────────────────────────────────────────────
# This schema does two things simultaneously:
#   1. It tells the LLM exactly what fields to produce (via the prompt)
#   2. It validates the LLM's response before it reaches the rest of the system
#
# If the LLM omits a required field or uses the wrong type, Pydantic raises
# a ValidationError immediately rather than letting bad data flow downstream.
# This is the difference between a robust agent and a brittle one.

class TriageOutput(BaseModel):
    """Structured output schema for the Triage Agent."""

    severity: Literal["P1", "P2", "P3", "P4"] = Field(
        description=(
            "ITIL severity level. "
            "P1 = complete service outage, revenue impact, all users affected. "
            "P2 = major degradation, significant user impact, workaround unavailable. "
            "P3 = partial impact, workaround available, moderate user impact. "
            "P4 = minor issue, cosmetic, single user or low-priority system."
        )
    )

    affected_service: str = Field(
        description=(
            "The specific service, system, or component that is failing. "
            "Be precise — not 'the application' but 'Payment Gateway API' or "
            "'MySQL Production Database' or 'Authentication Microservice'."
        )
    )

    category: Literal[
        "Database", "Application", "Network",
        "Infrastructure", "Security", "Cloud"
    ] = Field(
        description="The ITIL incident category that best describes the failure domain."
    )

    business_impact: str = Field(
        description=(
            "A concise 1-2 sentence description of the business consequence "
            "if this incident is not resolved. Focus on user impact, revenue "
            "risk, or operational disruption — not technical details."
        )
    )

    recommended_team: str = Field(
        description=(
            "The resolver team that should own this incident. Examples: "
            "Database Administration, Cloud Infrastructure, Network Operations, "
            "Application Support, DevOps, Cybersecurity, Platform Engineering."
        )
    )

    initial_diagnosis: str = Field(
        description=(
            "A 2-3 sentence technical hypothesis about the most likely root cause "
            "based on the symptoms described. This is not a confirmed root cause — "
            "it is an educated starting point for the resolver team's investigation."
        )
    )

    estimated_resolution_time: str = Field(
        description=(
            "Estimated time to resolve based on severity and category. "
            "Examples: '15-30 minutes', '1-2 hours', '2-4 hours', '4-8 hours'."
        )
    )


# ── LangGraph state schema ────────────────────────────────────────────────────
# The state is the data object that flows through the entire LangGraph pipeline.
# Each agent receives the state, does its work, and returns an updated version.
# Fields set by earlier agents are available to all later agents automatically.
# Fields that are None have not yet been populated by any agent.

class ServicePilotState(BaseModel):
    """Shared state object that flows through all four agents in the pipeline."""

    # Input — provided by the user before the pipeline starts
    incident_description: str = Field(
        description="The raw, unstructured incident description from the engineer."
    )

    # Set by Agent 1 (Triage Agent) — used by Agents 2, 3, and 4
    triage_result: TriageOutput | None = Field(
        default=None,
        description="Structured triage classification produced by Agent 1."
    )

    # Set by Agent 2 (Resolution Agent) — used by Agents 3 and 4
    similar_incidents: dict | None = Field(
        default=None,
        description="Top-3 similar past incidents retrieved by Agent 2's RAG system."
    )

    # Set by Agent 3 (RCA Agent) — used by Agent 4
    rca_report: str | None = Field(
        default=None,
        description="Full Root Cause Analysis document generated by Agent 3."
    )

    # Set by Agent 4 (CAB Agent) — final output of the pipeline
    cab_document: str | None = Field(
        default=None,
        description="Change Advisory Board document generated by Agent 4."
    )


# ── System prompt ─────────────────────────────────────────────────────────────
# The system prompt is the most important engineering decision in an LLM agent.
# It defines the model's persona, its decision-making framework, its output
# format, and the constraints it must follow. A well-written system prompt
# eliminates the need for output post-processing and dramatically reduces
# hallucinations by grounding the model in a specific, well-defined role.

TRIAGE_SYSTEM_PROMPT = """You are an expert ITIL Incident Manager with 15 years of experience 
in IT service management at major technology consulting firms. You have classified thousands 
of production incidents across banking, e-commerce, healthcare, and enterprise software clients.

Your role is to perform the initial triage of incoming IT incidents — the critical first step 
in the ITIL incident management lifecycle. You must analyze the incident description provided 
and produce a precise, structured classification that enables the resolver team to begin 
working immediately without ambiguity.

SEVERITY CLASSIFICATION RULES (follow these strictly):
- P1: Complete service outage. ALL users affected. Revenue or regulatory impact occurring NOW.
  Requires immediate escalation. Examples: payment gateway down, production database unreachable,
  authentication service failing for all users, security breach in progress.
- P2: Major service degradation. SIGNIFICANT portion of users affected. No acceptable workaround.
  Examples: severe performance degradation, partial authentication failure, critical API errors.
- P3: Partial impact. LIMITED user group affected OR workaround available.
  Examples: one geographic region affected, specific feature broken, non-critical service slow.
- P4: Minor or cosmetic issue. Single user, low-priority system, or easily worked around.
  Examples: UI display bug, non-critical batch job delayed, informational alert.

CATEGORY DEFINITIONS:
- Database: MySQL, PostgreSQL, Oracle, MongoDB, Redis, Elasticsearch, Cassandra issues
- Application: Microservices, APIs, web applications, authentication, payment processing
- Network: DNS, load balancers, VPN, firewall, latency, connectivity between services
- Infrastructure: Servers, Kubernetes, Docker, CI/CD pipelines, SSL certificates, backups
- Security: Breaches, vulnerabilities, unauthorized access, data exposure, ransomware
- Cloud: AWS, Azure, GCP resource failures, cloud storage, serverless, cloud networking

INITIAL DIAGNOSIS GUIDELINES:
- Base your hypothesis on the most statistically common root causes for the described symptoms
- Be specific about the likely failure component, not generic
- Acknowledge uncertainty where appropriate — this is a hypothesis, not a confirmed diagnosis

You must respond ONLY with a valid JSON object matching the required schema. 
Do not include any text before or after the JSON object.
Do not include markdown code fences or backticks.
Return pure JSON only."""


# ── Triage Agent function ─────────────────────────────────────────────────────

def run_triage_agent(state: ServicePilotState) -> ServicePilotState:
    """
    Agent 1: Classifies and prioritizes an incoming incident.

    This function is designed to be used as a LangGraph node — it receives
    the current pipeline state, performs its work, and returns the updated
    state with the triage_result field populated.

    The LLM is invoked with a structured prompt that includes the incident
    description. The response is parsed as JSON and validated against the
    TriageOutput Pydantic schema before being stored in the state.

    Args:
        state: The current ServicePilotState with incident_description populated.

    Returns:
        The updated ServicePilotState with triage_result populated.
    """

    print("\n[Triage Agent] Starting incident triage...")
    print(f"[Triage Agent] Analyzing: '{state.incident_description[:80]}...'")

    # Initialize the Groq LLM client
    # temperature=0.1 keeps responses consistent and factual while allowing
    # slight variation. temperature=0 can produce overly rigid outputs for
    # classification tasks that benefit from minor reasoning flexibility.
    llm = ChatGroq(
        model       = "llama-3.3-70b-versatile",
        temperature = 0.1,
        api_key     = os.environ.get("GROQ_API_KEY")
    )

    # Construct the message list for the LLM
    # SystemMessage sets the agent's persona and output constraints
    # HumanMessage contains the actual incident to classify
    messages = [
        SystemMessage(content=TRIAGE_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Please triage the following IT incident:\n\n"
            f"INCIDENT DESCRIPTION:\n{state.incident_description}\n\n"
            f"Respond with a JSON object containing: severity, affected_service, "
            f"category, business_impact, recommended_team, initial_diagnosis, "
            f"estimated_resolution_time."
        ))
    ]

    # Invoke the LLM and get the raw response text
    response      = llm.invoke(messages)
    response_text = response.content.strip()

    # Clean the response — sometimes the LLM adds markdown fences despite
    # the instruction not to, so we strip them defensively before parsing
    if response_text.startswith("```"):
        lines         = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    # Parse JSON and validate against the Pydantic schema
    # If the LLM returned malformed JSON or missing fields, this raises
    # a clear error immediately rather than propagating bad data silently
    try:
        parsed_json   = json.loads(response_text)
        triage_result = TriageOutput(**parsed_json)
    except (json.JSONDecodeError, Exception) as e:
        raise ValueError(
            f"[Triage Agent] Failed to parse LLM response as TriageOutput.\n"
            f"Raw response: {response_text}\n"
            f"Error: {e}"
        )

    print(f"[Triage Agent] ✓ Triage complete.")
    print(f"[Triage Agent]   Severity : {triage_result.severity}")
    print(f"[Triage Agent]   Category : {triage_result.category}")
    print(f"[Triage Agent]   Service  : {triage_result.affected_service}")
    print(f"[Triage Agent]   Team     : {triage_result.recommended_team}")

    # Return the updated state — LangGraph passes this to the next agent
    return ServicePilotState(
        incident_description = state.incident_description,
        triage_result        = triage_result,
        similar_incidents    = state.similar_incidents,
        rca_report           = state.rca_report,
        cab_document         = state.cab_document
    )


# ── Standalone validation test ────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 65)
    print("   Triage Agent — Standalone Validation")
    print("=" * 65)

    # Test with three different incident types to validate classification quality
    test_incidents = [
        # Should classify as P1, Application, Authentication/Cloud
        (
            "Production authentication service is completely down. "
            "All 50,000 users are unable to log into the banking portal. "
            "We are getting 502 Bad Gateway errors on all login attempts. "
            "Started 15 minutes ago. Revenue impact is critical."
        ),
        # Should classify as P2, Database, Database Administration
        (
            "Our PostgreSQL database is showing high disk usage at 94%. "
            "Several write transactions are beginning to fail intermittently. "
            "Read operations still working. Affects the order management system."
        ),
        # Should classify as P1, Security, Cybersecurity
        (
            "Security team detected unauthorized API calls from an unknown IP. "
            "The calls are reading from our customer PII database table. "
            "Approximately 10,000 customer records may have been accessed. "
            "The activity started 2 hours ago and is still ongoing."
        )
    ]

    for i, incident in enumerate(test_incidents, start=1):
        print(f"\n{'─' * 65}")
        print(f"Test {i}: {incident[:70]}...")
        print(f"{'─' * 65}")

        # Create the initial state with just the incident description
        initial_state = ServicePilotState(incident_description=incident)

        # Run the triage agent
        result_state  = run_triage_agent(initial_state)
        triage        = result_state.triage_result

        print(f"\n  Severity              : {triage.severity}")
        print(f"  Affected Service      : {triage.affected_service}")
        print(f"  Category              : {triage.category}")
        print(f"  Recommended Team      : {triage.recommended_team}")
        print(f"  Est. Resolution Time  : {triage.estimated_resolution_time}")
        print(f"\n  Business Impact:")
        print(f"  {triage.business_impact}")
        print(f"\n  Initial Diagnosis:")
        print(f"  {triage.initial_diagnosis}")

    print(f"\n{'=' * 65}")
    print("   Triage Agent validation complete.")
    print("=" * 65)