# graph.py
# ─────────────────────────────────────────────────────────────────────────────
# ServicePilot — LangGraph Pipeline Orchestrator
#
# This file defines the official execution graph that connects all four
# agents into a single orchestrated pipeline. LangGraph models the pipeline
# as a directed acyclic graph (DAG) where:
#   - Each node is one agent function
#   - Each edge defines which agent runs after which
#   - The shared ServicePilotState flows through every node automatically
#
# Why LangGraph instead of just calling agents sequentially in a function?
#   LangGraph gives you a production-grade orchestration framework with
#   built-in state persistence, error handling boundaries, streaming support,
#   and the ability to add conditional branching later (e.g., skip the CAB
#   document for P3/P4 incidents). It also makes the architecture visually
#   explainable as a graph — which is exactly what you want when describing
#   this system in an interview.
# ─────────────────────────────────────────────────────────────────────────────

import os
import logging

# Suppress ChromaDB telemetry warnings completely
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"]     = "False"
logging.getLogger("chromadb").setLevel(logging.ERROR)

from langgraph.graph import StateGraph, END
from agents.triage_agent      import ServicePilotState, run_triage_agent
from agents.resolution_agent  import run_resolution_agent
from agents.rca_agent         import run_rca_agent
from agents.cab_agent         import run_cab_agent
from utils.chroma_utils       import initialize_vector_store


# ── Initialize the vector store once at module load time ─────────────────────
# We initialize ChromaDB here rather than inside each agent call because
# loading the BGE model and connecting to the persistent store takes 2-3
# seconds. By doing it once at startup and passing the collection object
# into the graph, every subsequent pipeline run is instantaneous for the
# retrieval step — the collection object stays in memory between Streamlit
# interactions without reloading from disk each time.

print("[ServicePilot] Initializing vector store for pipeline...")
COLLECTION = initialize_vector_store()
print("[ServicePilot] Pipeline ready.\n")


# ── Node wrapper functions ────────────────────────────────────────────────────
# LangGraph nodes must be functions that accept and return the state object.
# Agent 2 needs the ChromaDB collection injected — we use a closure here
# (a function that captures COLLECTION from the outer scope) so the node
# signature matches what LangGraph expects while still having access to
# the collection object.

def triage_node(state: ServicePilotState) -> ServicePilotState:
    """LangGraph node wrapper for Agent 1 — Triage Agent."""
    return run_triage_agent(state)


def resolution_node(state: ServicePilotState) -> ServicePilotState:
    """
    LangGraph node wrapper for Agent 2 — Resolution Agent.
    Uses a closure to inject the pre-loaded ChromaDB collection
    without violating LangGraph's required node function signature.
    """
    return run_resolution_agent(state, COLLECTION)


def rca_node(state: ServicePilotState) -> ServicePilotState:
    """LangGraph node wrapper for Agent 3 — RCA Report Generator."""
    return run_rca_agent(state)


def cab_node(state: ServicePilotState) -> ServicePilotState:
    """LangGraph node wrapper for Agent 4 — CAB Document Generator."""
    return run_cab_agent(state)


# ── Build the LangGraph execution graph ──────────────────────────────────────

def build_pipeline() -> StateGraph:
    """
    Constructs and compiles the four-agent ServicePilot pipeline as a
    LangGraph StateGraph.

    The graph topology is a simple linear chain:
        START → triage → resolution → rca → cab → END

    Each node receives the complete ServicePilotState, adds its own output
    to the state, and passes the enriched state forward to the next node.
    By the time the graph reaches END, all four fields of ServicePilotState
    are populated: triage_result, similar_incidents, rca_report, cab_document.

    Returns:
        A compiled LangGraph StateGraph ready to invoke with .invoke()
    """

    # Create a new StateGraph using ServicePilotState as the shared state schema.
    # LangGraph uses this schema to validate state at each node boundary —
    # if an agent returns an incompatible state object, it fails immediately
    # with a clear error rather than propagating bad data silently downstream.
    graph = StateGraph(ServicePilotState)

    # Add each agent as a named node in the graph
    graph.add_node("triage",     triage_node)
    graph.add_node("resolution", resolution_node)
    graph.add_node("rca",        rca_node)
    graph.add_node("cab",        cab_node)

    # Define the execution order with directed edges
    # These edges form the pipeline: each agent's output becomes the next
    # agent's input through the shared ServicePilotState object
    graph.set_entry_point("triage")        # Pipeline starts at triage
    graph.add_edge("triage",     "resolution")
    graph.add_edge("resolution", "rca")
    graph.add_edge("rca",        "cab")
    graph.add_edge("cab",        END)      # Pipeline ends after CAB document

    # Compile the graph into an executable runnable
    # After compilation, the graph can be invoked with .invoke(initial_state)
    return graph.compile()


# ── The main pipeline function called by the Streamlit app ───────────────────

def run_pipeline(incident_description: str) -> ServicePilotState:
    """
    Runs the complete four-agent pipeline for a given incident description.

    This is the single function that the Streamlit UI calls. It takes the
    raw incident text, creates the initial state, invokes the compiled graph,
    and returns the fully populated state with all four agent outputs.

    Args:
        incident_description: The raw incident text entered by the user.

    Returns:
        ServicePilotState with all fields populated:
            - triage_result        → Agent 1 output
            - similar_incidents    → Agent 2 output
            - rca_report           → Agent 3 output
            - cab_document         → Agent 4 output
    """

    pipeline = build_pipeline()

    initial_state = ServicePilotState(
        incident_description = incident_description
    )

    # .invoke() runs the entire graph synchronously and returns the final state
    # LangGraph handles the node-to-node state passing internally
    final_state = pipeline.invoke(initial_state)

    # LangGraph returns a dict when invoked — convert back to ServicePilotState
    # so the Streamlit app can access fields with dot notation (state.triage_result)
    return ServicePilotState(**final_state)