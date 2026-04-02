# agents/resolution_agent.py
# ─────────────────────────────────────────────────────────────────────────────
# ServicePilot — Resolution Suggester Agent (Agent 2)
#
# Responsibility: Given a new incident and its triage classification, search
# the ITIL knowledge base for the most similar past incidents and synthesize
# a tailored resolution recommendation that adapts historical solutions to
# the current incident's specific context.
#
# Architecture: Two-phase RAG pipeline
#   Phase 1 — Retrieval: BGE-Base cosine similarity search across all 100
#              incidents in ChromaDB. Returns the top 3 most semantically
#              similar past incidents with full metadata (resolution steps,
#              root cause, preventive measures, resolution time).
#   Phase 2 — Generation: LLaMA 3.3 70B receives the current incident +
#              triage result + 3 retrieved incidents and synthesizes a
#              structured resolution recommendation tailored to the new case.
#
# Why RAG instead of pure LLM generation?
#   A pure LLM would generate plausible-sounding but hallucinated resolution
#   steps. By grounding the LLM in real historical incident data from your
#   knowledge base, the recommendations are based on steps that actually
#   worked in similar past situations — dramatically improving reliability.
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Import the vector store utilities built in Step 3
from utils.chroma_utils import search_similar_incidents

load_dotenv()

# Import the shared state schema from the triage agent
# All agents share the same ServicePilotState so the pipeline stays coherent
from agents.triage_agent import ServicePilotState, TriageOutput


# ── System prompt ─────────────────────────────────────────────────────────────

RESOLUTION_SYSTEM_PROMPT = """You are a Senior IT Service Management consultant with 15 years 
of experience resolving production incidents at Fortune 500 companies. You specialize in 
adapting proven resolution patterns from past incidents to new situations.

You will be given:
1. A new IT incident description with its triage classification
2. The top 3 most similar past incidents retrieved from a knowledge base, each with 
   their proven resolution steps, root causes, and preventive measures

Your task is to synthesize a TAILORED resolution recommendation for the new incident by:
- Adapting the most relevant resolution steps from similar past incidents
- Adjusting for any differences between the past incidents and the current one
- Prioritizing steps that address the most likely root cause
- Providing clear, actionable numbered steps that an engineer can follow immediately

IMPORTANT GUIDELINES:
- Be specific and actionable — avoid generic advice like "check the logs"
- Number all resolution steps clearly
- Acknowledge which past incident most influenced each recommendation
- Note any important differences between past incidents and the current one
- Include estimated time for each major phase of the resolution

Respond ONLY with a valid JSON object. No markdown, no backticks, pure JSON only."""


# ── Resolution Agent ──────────────────────────────────────────────────────────

def run_resolution_agent(
    state      : ServicePilotState,
    collection          # ChromaDB collection passed in from the pipeline
) -> ServicePilotState:
    """
    Agent 2: Retrieves similar past incidents and synthesizes resolution guidance.

    This agent is the bridge between your vector knowledge base and the LLM.
    It ensures that every resolution recommendation is grounded in real
    historical data rather than LLM hallucination.

    Args:
        state      : Current pipeline state with incident_description and
                     triage_result populated by Agent 1.
        collection : The initialized ChromaDB collection from Step 3.

    Returns:
        Updated ServicePilotState with similar_incidents populated.
    """

    print("\n[Resolution Agent] Starting knowledge base retrieval...")

    # ── Phase 1: Semantic retrieval from ChromaDB ─────────────────────────────
    # We query using the original incident description — this gives the best
    # semantic match because it contains the full problem context in natural
    # language, not just the structured triage fields.

    similar = search_similar_incidents(
        collection = collection,
        query      = state.incident_description,
        n_results  = 3
    )

    print(f"[Resolution Agent] ✓ Retrieved {len(similar)} similar past incidents:")
    for i, inc in enumerate(similar, start=1):
        print(f"  {i}. [{inc['incident_id']}] {inc['title']} "
              f"(similarity: {inc['similarity_score']}%)")

    # ── Phase 2: LLM-synthesized resolution recommendation ────────────────────
    # Build a rich context string from the retrieved incidents and pass it
    # to the LLM along with the current incident details.

    # Format each retrieved incident into a readable context block
    retrieved_context = ""
    for i, inc in enumerate(similar, start=1):
        steps_text = "\n      ".join(inc["resolution_steps"])
        prevent_text = "\n      ".join(inc["preventive_measures"])

        retrieved_context += f"""
PAST INCIDENT {i} (Similarity: {inc['similarity_score']}%):
  ID           : {inc['incident_id']}
  Title        : {inc['title']}
  Severity     : {inc['severity']}
  Category     : {inc['category']}
  Affected     : {inc['affected_service']}
  Resolved In  : {inc['resolved_in_minutes']} minutes
  Team         : {inc['assigned_team']}
  Root Cause   : {inc['root_cause']}
  Resolution Steps:
      {steps_text}
  Preventive Measures:
      {prevent_text}
"""

    # Build the triage summary for context
    triage = state.triage_result
    triage_summary = f"""
CURRENT INCIDENT TRIAGE:
  Severity         : {triage.severity}
  Affected Service : {triage.affected_service}
  Category         : {triage.category}
  Recommended Team : {triage.recommended_team}
  Initial Diagnosis: {triage.initial_diagnosis}
  Business Impact  : {triage.business_impact}
"""

    llm = ChatGroq(
        model       = "llama-3.3-70b-versatile",
        temperature = 0.2,
        api_key     = os.environ.get("GROQ_API_KEY")
    )

    messages = [
        SystemMessage(content=RESOLUTION_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"NEW INCIDENT:\n{state.incident_description}\n\n"
            f"{triage_summary}\n"
            f"SIMILAR PAST INCIDENTS FROM KNOWLEDGE BASE:\n{retrieved_context}\n\n"
            f"Synthesize a tailored resolution recommendation as a JSON object with these fields:\n"
            f"- recommended_steps: array of strings, each a numbered actionable step\n"
            f"- primary_reference: incident ID that most closely matches (e.g. 'INC-002')\n"
            f"- key_differences: string describing how current incident differs from past ones\n"
            f"- estimated_total_resolution_time: string with time estimate\n"
            f"- confidence_level: one of 'High', 'Medium', 'Low'\n"
            f"- confidence_reason: string explaining why this confidence level was assigned"
        ))
    ]

    response      = llm.invoke(messages)
    response_text = response.content.strip()

    # Strip markdown fences if present
    if response_text.startswith("```"):
        lines         = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    try:
        llm_synthesis = json.loads(response_text)
    except json.JSONDecodeError as e:
        # If JSON parsing fails, store raw text rather than crashing the pipeline
        llm_synthesis = {"raw_response": response_text, "parse_error": str(e)}

    # Combine the retrieved incidents with the LLM synthesis into one rich object
    # This gives downstream agents (RCA and CAB) both the raw retrieved data
    # and the LLM's synthesized interpretation to work from
    combined_result = {
        "retrieved_incidents" : similar,
        "synthesis"           : llm_synthesis
    }

    print(f"[Resolution Agent] ✓ Resolution synthesis complete.")
    print(f"[Resolution Agent]   Primary reference : "
          f"{llm_synthesis.get('primary_reference', 'N/A')}")
    print(f"[Resolution Agent]   Confidence        : "
          f"{llm_synthesis.get('confidence_level', 'N/A')}")
    print(f"[Resolution Agent]   Est. resolution   : "
          f"{llm_synthesis.get('estimated_total_resolution_time', 'N/A')}")

    return ServicePilotState(
        incident_description = state.incident_description,
        triage_result        = state.triage_result,
        similar_incidents    = combined_result,
        rca_report           = state.rca_report,
        cab_document         = state.cab_document
    )


# ── Standalone validation ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import chromadb
    from utils.chroma_utils import initialize_vector_store

    print("=" * 65)
    print("   Resolution Agent — Standalone Validation")
    print("=" * 65)

    # Initialize the vector store
    collection = initialize_vector_store()

    # Simulate a state as if Agent 1 already ran successfully
    test_state = ServicePilotState(
        incident_description=(
            "Production Kubernetes cluster has multiple pods in CrashLoopBackOff "
            "state. The payment processing service is completely down. All three "
            "replicas are crashing every 90 seconds. Error logs show the pods "
            "cannot find a required Kubernetes Secret that holds payment gateway "
            "credentials. Customers cannot complete any purchases."
        ),
        triage_result=TriageOutput(
            severity                  = "P1",
            affected_service          = "Payment Processing Service (Kubernetes)",
            category                  = "Application",
            business_impact           = "All payment transactions failing. Complete e-commerce revenue loss.",
            recommended_team          = "DevOps",
            initial_diagnosis         = "Missing or deleted Kubernetes Secret causing pod startup failure.",
            estimated_resolution_time = "20-45 minutes"
        )
    )

    result_state = run_resolution_agent(test_state, collection)
    result       = result_state.similar_incidents

    print(f"\n{'─' * 65}")
    print("RETRIEVED SIMILAR INCIDENTS:")
    print(f"{'─' * 65}")
    for i, inc in enumerate(result["retrieved_incidents"], start=1):
        print(f"  {i}. [{inc['incident_id']}] {inc['title']}")
        print(f"     Similarity: {inc['similarity_score']}% | "
              f"Resolved in: {inc['resolved_in_minutes']} min")

    print(f"\n{'─' * 65}")
    print("LLM RESOLUTION SYNTHESIS:")
    print(f"{'─' * 65}")
    synthesis = result["synthesis"]
    print(f"  Primary Reference : {synthesis.get('primary_reference', 'N/A')}")
    print(f"  Confidence        : {synthesis.get('confidence_level', 'N/A')}")
    print(f"  Reason            : {synthesis.get('confidence_reason', 'N/A')}")
    print(f"  Est. Time         : "
          f"{synthesis.get('estimated_total_resolution_time', 'N/A')}")
    print(f"  Key Differences   : {synthesis.get('key_differences', 'N/A')}")
    print(f"\n  Recommended Steps:")
    for step in synthesis.get("recommended_steps", []):
        print(f"    {step}")

    print(f"\n{'=' * 65}")
    print("   Resolution Agent validation complete.")
    print("=" * 65)