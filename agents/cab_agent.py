# agents/cab_agent.py
# ─────────────────────────────────────────────────────────────────────────────
# ServicePilot — CAB Document Generator Agent (Agent 4)
#
# Responsibility: Generate a complete Change Advisory Board (CAB) change
# request document based on the full incident context accumulated across
# all three previous agents in the pipeline.
#
# What is a CAB document in real service companies?
#   When an incident is resolved, the fix often requires a permanent change
#   to the production environment — a new monitoring alert, a patched script,
#   a configuration update, or an infrastructure change. Before that change
#   can be implemented, it must be formally reviewed and approved by the
#   Change Advisory Board. The CAB document presents the proposed change with
#   a complete risk profile so the board can make an informed decision.
#   In ITIL terms this is called a Request for Change (RFC).
#
# Why this agent completes the pipeline:
#   Agents 1-3 document what happened and why. Agent 4 documents what must
#   be done permanently to prevent recurrence — closing the loop from
#   reactive incident response to proactive change management.
# ─────────────────────────────────────────────────────────────────────────────

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

from agents.triage_agent import ServicePilotState


# ── System prompt ─────────────────────────────────────────────────────────────

CAB_SYSTEM_PROMPT = """You are a Senior IT Change Manager with 12 years of experience 
managing Change Advisory Board processes at major IT service companies including TCS, 
Infosys, and Wipro delivery centers. You have prepared and presented hundreds of RFC 
(Request for Change) documents to CAB committees for enterprise clients.

You will receive the complete incident context — description, triage classification, 
RCA report, and resolution details. Your task is to produce a formal CAB change request 
document that the resolver team will present at the next CAB meeting.

A professional CAB document must:
- Clearly identify the change being proposed (not the incident — the PERMANENT FIX)
- Provide an honest risk assessment with specific risk scenarios
- Include a detailed, step-by-step implementation plan with time estimates
- Include a complete rollback plan in case the change causes new problems
- Define clear success criteria so the CAB can verify the change worked
- Identify all stakeholders who must approve before implementation

CHANGE TYPES in ITIL:
- Standard Change: Pre-approved, low risk, frequently performed (e.g., routine patching)
- Normal Change: Requires full CAB review and approval (most post-incident changes)
- Emergency Change: Implemented immediately, reviewed by ECAB retrospectively

RISK LEVELS:
- Low: Change is well-understood, reversible, affects non-critical systems
- Medium: Some uncertainty, affects production but has solid rollback plan
- High: Complex change, significant production impact, limited rollback options

Write in formal professional English suitable for presentation to client stakeholders.
Do not include any preamble — start directly with the CAB document."""


# ── CAB Agent ─────────────────────────────────────────────────────────────────

def run_cab_agent(state: ServicePilotState) -> ServicePilotState:
    """
    Agent 4: Generates a formal ITIL Change Advisory Board request document.

    This is the final agent in the ServicePilot pipeline. It takes the complete
    accumulated context from all three previous agents and produces the formal
    change management document that closes the loop between incident response
    and permanent preventive change implementation.

    The CAB document is the most process-oriented output in the pipeline —
    it must follow ITIL RFC standards precisely because it will be reviewed
    by client stakeholders who are familiar with those standards and will
    immediately notice if they are not followed correctly.

    Args:
        state: Complete pipeline state with all four fields populated by
               Agents 1, 2, and 3.

    Returns:
        Updated ServicePilotState with cab_document populated as a string.
    """

    print("\n[CAB Agent] Generating Change Advisory Board document...")

    triage   = state.triage_result
    retrieved = state.similar_incidents
    synthesis = retrieved.get("synthesis", {})
    rca       = state.rca_report

    # Calculate realistic CAB meeting and implementation dates
    # CAB meetings typically happen weekly — we schedule for next week
    today         = datetime.now()
    cab_date      = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    impl_date     = (today + timedelta(days=10)).strftime("%Y-%m-%d")
    review_date   = (today + timedelta(days=17)).strftime("%Y-%m-%d")

    # Extract resolution steps from Agent 2 synthesis for the implementation plan
    resolution_steps = synthesis.get("recommended_steps", [])
    steps_text       = "\n".join(resolution_steps) if resolution_steps else "See RCA report."

    # Determine change type based on severity
    # P1 incidents that have already been resolved typically require Normal Change
    # for the permanent preventive measures, since the emergency fix is already done
    change_type = "Normal Change" if triage.severity in ["P1", "P2"] else "Standard Change"

    llm = ChatGroq(
        model       = "llama-3.3-70b-versatile",
        temperature = 0.2,
        api_key     = os.environ.get("GROQ_API_KEY")
    )

    messages = [
        SystemMessage(content=CAB_SYSTEM_PROMPT),
        HumanMessage(content=f"""Generate a complete CAB Change Request document for the 
following post-incident change. This change is being proposed to permanently prevent 
recurrence of the incident described below.

=== SOURCE INCIDENT ===
Description  : {state.incident_description}
Severity     : {triage.severity}
Affected     : {triage.affected_service}
Category     : {triage.category}
Business Impact: {triage.business_impact}
Change Type  : {change_type}

=== ROOT CAUSE (from RCA) ===
Initial Diagnosis: {triage.initial_diagnosis}
Primary Reference Incident: {synthesis.get('primary_reference', 'N/A')}
Confidence: {synthesis.get('confidence_level', 'N/A')}
Key Differences: {synthesis.get('key_differences', 'N/A')}

=== RESOLUTION STEPS ALREADY APPLIED (emergency fix) ===
{steps_text}

=== RCA SUMMARY ===
{rca[:1500] if rca else 'See attached RCA document.'}

=== SCHEDULING ===
CAB Meeting Date     : {cab_date}
Proposed Impl. Date  : {impl_date}
Post-Impl Review Date: {review_date}

Generate a complete formal CAB RFC document with ALL of the following sections:

1. CHANGE REQUEST HEADER
   (Change ID, Title, Type, Priority, Requestor, Date Raised, CAB Meeting Date)

2. CHANGE DESCRIPTION
   (What exactly is being changed in the production environment permanently,
   clearly distinguishing the emergency fix already applied from the permanent
   preventive change now being proposed)

3. JUSTIFICATION AND BUSINESS CASE
   (Why this change is necessary, cost of inaction, link to incident)

4. RISK ASSESSMENT
   (Risk level, specific risk scenarios with probability and impact,
   risk mitigation strategy for each scenario)

5. IMPLEMENTATION PLAN
   (Step-by-step with time estimates, who performs each step,
   pre-implementation checklist, maintenance window requirement)

6. ROLLBACK PLAN
   (Exact steps to reverse the change if it causes new problems,
   rollback decision criteria, rollback time estimate)

7. TESTING AND VALIDATION
   (How to verify the change worked, success criteria,
   monitoring requirements post-implementation)

8. STAKEHOLDER APPROVAL MATRIX
   (Who must approve, their role, approval method, deadline)

9. COMMUNICATION PLAN
   (Who gets notified, when, through what channel)

Make every section specific to this incident and proposed change.
Use formal ITIL change management language throughout.""")
    ]

    response = llm.invoke(messages)
    cab_text = response.content.strip()

    print(f"[CAB Agent] ✓ CAB document generated successfully.")
    print(f"[CAB Agent]   Document length : {len(cab_text.split())} words")
    print(f"[CAB Agent]   Change Type     : {change_type}")
    print(f"[CAB Agent]   CAB Meeting Date: {cab_date}")
    print(f"[CAB Agent]   Impl. Date      : {impl_date}")

    return ServicePilotState(
        incident_description = state.incident_description,
        triage_result        = state.triage_result,
        similar_incidents    = state.similar_incidents,
        rca_report           = state.rca_report,
        cab_document         = cab_text
    )


# ── Standalone validation ─────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.chroma_utils import initialize_vector_store
    from agents.triage_agent import run_triage_agent, TriageOutput
    from agents.resolution_agent import run_resolution_agent
    from agents.rca_agent import run_rca_agent

    print("=" * 65)
    print("   CAB Agent — Standalone Validation (Full Pipeline Run)")
    print("=" * 65)

    # Initialize the vector store
    collection = initialize_vector_store()

    # The test incident — same one used across all agents for consistency
    incident = (
        "Production Kubernetes cluster has multiple pods in CrashLoopBackOff "
        "state. The payment processing service is completely down. All three "
        "replicas are crashing every 90 seconds. Error logs show the pods "
        "cannot find a required Kubernetes Secret that holds payment gateway "
        "credentials. Customers cannot complete any purchases. Revenue impact "
        "is approximately Rs 2 lakhs per hour."
    )

    # Run the complete pipeline sequentially — Agent 1 → 2 → 3 → 4
    print("\n[Pipeline] Running all four agents in sequence...\n")

    state = ServicePilotState(incident_description=incident)
    state = run_triage_agent(state)          # Agent 1
    state = run_resolution_agent(state, collection)  # Agent 2
    state = run_rca_agent(state)             # Agent 3
    state = run_cab_agent(state)             # Agent 4

    print(f"\n{'=' * 65}")
    print("   COMPLETE PIPELINE RESULTS")
    print(f"{'=' * 65}")

    print(f"\n--- TRIAGE CLASSIFICATION (Agent 1) ---")
    t = state.triage_result
    print(f"  Severity : {t.severity} | Category : {t.category}")
    print(f"  Service  : {t.affected_service}")
    print(f"  Team     : {t.recommended_team}")
    print(f"  Impact   : {t.business_impact}")

    print(f"\n--- SIMILAR INCIDENTS (Agent 2) ---")
    for i, inc in enumerate(
        state.similar_incidents["retrieved_incidents"], start=1
    ):
        print(f"  {i}. [{inc['incident_id']}] {inc['title']} "
              f"({inc['similarity_score']}%)")

    print(f"\n--- RCA REPORT (Agent 3) ---")
    print(f"  Length: {len(state.rca_report.split())} words")
    # Print just the executive summary section
    rca_lines = state.rca_report.split("\n")
    in_summary = False
    for line in rca_lines:
        if "EXECUTIVE SUMMARY" in line:
            in_summary = True
        elif in_summary and line.startswith("==="):
            break
        elif in_summary and line.strip():
            print(f"  {line}")

    print(f"\n--- CAB DOCUMENT (Agent 4) ---")
    print(f"  Length: {len(state.cab_document.split())} words")
    # Print just the header section of the CAB document
    cab_lines = state.cab_document.split("\n")
    for j, line in enumerate(cab_lines[:25]):
        if line.strip():
            print(f"  {line}")

    print(f"\n{'=' * 65}")
    print("  Full pipeline execution complete.")
    print("  All 4 agents ran successfully end-to-end.")
    print("  RCA and CAB documents are ready for delivery.")
    print(f"{'=' * 65}")