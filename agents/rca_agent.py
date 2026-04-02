# agents/rca_agent.py
# ─────────────────────────────────────────────────────────────────────────────
# ServicePilot — RCA Report Generator Agent (Agent 3)
#
# Responsibility: Generate a complete, professionally structured Root Cause
# Analysis (RCA) document by synthesizing all context accumulated by the
# previous two agents — triage classification, similar past incidents, and
# resolution synthesis.
#
# Why this agent matters in a service company context:
#   Every P1 and P2 incident in ITIL requires a formal RCA document to be
#   submitted to the Change Advisory Board and client stakeholders within
#   24-72 hours of resolution. Writing this manually takes senior engineers
#   2-4 hours. This agent produces a complete, audit-ready RCA in seconds
#   by reasoning across the full incident context accumulated in the pipeline.
#
# Design decision — why long-form generation instead of structured JSON:
#   The RCA document is the final human-readable artifact of the incident
#   lifecycle. Unlike the triage output (which feeds machines downstream),
#   the RCA is read by engineers, managers, and clients. Generating it as
#   clean formatted text rather than JSON produces a document that can be
#   directly copied into a JIRA ticket, email, or incident management system.
# ─────────────────────────────────────────────────────────────────────────────

import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

from agents.triage_agent import ServicePilotState


# ── System prompt ─────────────────────────────────────────────────────────────

RCA_SYSTEM_PROMPT = """You are a Principal IT Service Management Engineer specializing in 
post-incident analysis and Root Cause Analysis documentation. You have written hundreds of 
RCA reports for Fortune 500 clients across banking, healthcare, e-commerce, and enterprise 
software sectors.

Your RCA reports are known for three qualities:
1. TECHNICAL PRECISION — every claim is grounded in evidence from the incident data
2. CAUSAL CLARITY — the chain from trigger to symptom to impact is explained clearly
3. ACTIONABLE PREVENTION — preventive measures are specific, prioritized, and implementable

You will receive the complete incident context: the original description, triage classification,
similar past incidents from the knowledge base, and the resolution synthesis. Use ALL of this
information to produce a comprehensive RCA document.

CRITICAL REQUIREMENTS:
- The RCA must follow ITIL post-incident review standards
- Every section must be substantive — no placeholder text or vague statements
- The Five Whys analysis must actually trace the causal chain logically
- Timeline entries must be realistic given the incident type and severity
- Preventive measures must be specific, not generic best practices

Format the document with clear section headers using === markers.
Write in professional technical English suitable for client delivery.
Do not include any preamble or postamble — start directly with the RCA document."""


# ── RCA Agent ─────────────────────────────────────────────────────────────────

def run_rca_agent(state: ServicePilotState) -> ServicePilotState:
    """
    Agent 3: Generates a complete ITIL-compliant RCA document.

    This agent is the synthesis culmination of the entire pipeline. It takes
    everything produced by Agents 1 and 2 and produces the human-readable
    artifact that represents the complete incident lifecycle documentation.

    The prompt engineering here is deliberately rich — the more context the
    LLM receives about the incident, the more specific and accurate the RCA
    document will be. We pass triage results, retrieved incidents, resolution
    steps, and confidence analysis all at once so the model can reason across
    all of them simultaneously.

    Args:
        state: Pipeline state with incident_description, triage_result,
               and similar_incidents all populated by Agents 1 and 2.

    Returns:
        Updated ServicePilotState with rca_report populated as a string.
    """

    print("\n[RCA Agent] Generating Root Cause Analysis report...")

    triage    = state.triage_result
    retrieved = state.similar_incidents

    # Extract the synthesis and retrieved incidents from Agent 2's output
    synthesis          = retrieved.get("synthesis", {})
    similar_incidents  = retrieved.get("retrieved_incidents", [])

    # Build the most relevant past incident context for the RCA prompt.
    # We use the primary reference incident (highest similarity) as the
    # main historical anchor for the RCA's causal analysis section.
    primary_ref_id   = synthesis.get("primary_reference", "N/A")
    primary_incident = next(
        (inc for inc in similar_incidents
         if inc["incident_id"] == primary_ref_id),
        similar_incidents[0] if similar_incidents else {}
    )

    # Format resolution steps from synthesis for the RCA timeline section
    resolution_steps_text = "\n".join(
        synthesis.get("recommended_steps", [])
    )

    # Format similar incidents summary for the knowledge base context section
    similar_summary = ""
    for inc in similar_incidents:
        similar_summary += (
            f"  - [{inc['incident_id']}] {inc['title']} "
            f"(Similarity: {inc['similarity_score']}%, "
            f"Resolved in: {inc['resolved_in_minutes']} min)\n"
        )

    # Current timestamp for the RCA document header
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    llm = ChatGroq(
        model       = "llama-3.3-70b-versatile",
        # Slightly higher temperature for long-form document generation —
        # allows more natural, varied prose while staying factually grounded
        temperature = 0.3,
        api_key     = os.environ.get("GROQ_API_KEY")
    )

    messages = [
        SystemMessage(content=RCA_SYSTEM_PROMPT),
        HumanMessage(content=f"""Generate a complete Root Cause Analysis report for the following incident.

=== INCIDENT INFORMATION ===
Report Generated  : {timestamp}
Incident Description: {state.incident_description}

=== TRIAGE CLASSIFICATION ===
Severity          : {triage.severity}
Affected Service  : {triage.affected_service}
Category          : {triage.category}
Recommended Team  : {triage.recommended_team}
Business Impact   : {triage.business_impact}
Initial Diagnosis : {triage.initial_diagnosis}
Est. Resolution   : {triage.estimated_resolution_time}

=== RESOLUTION SYNTHESIS (from Agent 2) ===
Primary Reference : {primary_ref_id}
Confidence Level  : {synthesis.get('confidence_level', 'N/A')}
Key Differences   : {synthesis.get('key_differences', 'N/A')}
Recommended Steps :
{resolution_steps_text}

=== MOST SIMILAR PAST INCIDENT (from Knowledge Base) ===
Incident ID       : {primary_incident.get('incident_id', 'N/A')}
Title             : {primary_incident.get('title', 'N/A')}
Root Cause        : {primary_incident.get('root_cause', 'N/A')}
Resolution Time   : {primary_incident.get('resolved_in_minutes', 'N/A')} minutes

=== OTHER SIMILAR INCIDENTS ===
{similar_summary}

Generate a complete ITIL-compliant RCA document with ALL of these sections:

1. EXECUTIVE SUMMARY (3-4 sentences for management audience)
2. INCIDENT TIMELINE (realistic entries from detection to resolution)
3. ROOT CAUSE ANALYSIS
   - Immediate Cause (the direct trigger)
   - Contributing Factors (conditions that allowed the trigger to cause impact)
   - Five Whys Analysis (trace the causal chain 5 levels deep)
4. IMPACT ASSESSMENT (users affected, business impact, data integrity)
5. RESOLUTION SUMMARY (what was done to restore service)
6. PREVENTIVE MEASURES (minimum 5 specific, actionable items with owners and timelines)
7. LESSONS LEARNED (what this incident teaches about the system and processes)
8. ACTION ITEMS TABLE (item | owner | priority | due date)

Make every section substantive and specific to this incident.
Use the similar past incidents as supporting evidence where relevant.""")
    ]

    response  = llm.invoke(messages)
    rca_text  = response.content.strip()

    print(f"[RCA Agent] ✓ RCA report generated successfully.")
    print(f"[RCA Agent]   Document length: {len(rca_text.split())} words")
    print(f"[RCA Agent]   Sections: Executive Summary, Timeline, Root Cause, "
          f"Impact, Resolution, Prevention, Lessons Learned, Action Items")

    return ServicePilotState(
        incident_description = state.incident_description,
        triage_result        = state.triage_result,
        similar_incidents    = state.similar_incidents,
        rca_report           = rca_text,
        cab_document         = state.cab_document
    )


# ── Standalone validation ─────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.chroma_utils import initialize_vector_store
    from agents.triage_agent import TriageOutput
    from agents.resolution_agent import run_resolution_agent

    print("=" * 65)
    print("   RCA Agent — Standalone Validation")
    print("=" * 65)

    # Initialize vector store
    collection = initialize_vector_store()

    # Simulate a complete pipeline state as if Agents 1 and 2 already ran
    incident = (
        "Production Kubernetes cluster has multiple pods in CrashLoopBackOff "
        "state. The payment processing service is completely down. All three "
        "replicas are crashing every 90 seconds. Error logs show the pods "
        "cannot find a required Kubernetes Secret that holds payment gateway "
        "credentials. Customers cannot complete any purchases. Revenue impact "
        "is approximately Rs 2 lakhs per hour."
    )

    # Run Agent 1 to get triage result
    from agents.triage_agent import run_triage_agent
    state = ServicePilotState(incident_description=incident)
    state = run_triage_agent(state)

    # Run Agent 2 to get similar incidents and synthesis
    state = run_resolution_agent(state, collection)

    # Run Agent 3 to generate the RCA report
    state = run_rca_agent(state)

    print(f"\n{'=' * 65}")
    print("   GENERATED RCA REPORT")
    print(f"{'=' * 65}\n")
    print(state.rca_report)
    print(f"\n{'=' * 65}")
    print("   RCA Agent validation complete.")
    print("=" * 65)