# app.py
# ─────────────────────────────────────────────────────────────────────────────
# ServicePilot — Streamlit Web Application
#
# This is the entry point and user interface for the entire ServicePilot system.
# It provides a clean, professional web interface where a user can:
#   1. Enter a raw incident description in plain English
#   2. Click a single button to run the complete four-agent pipeline
#   3. View the structured outputs of all four agents in organized tabs
#   4. Download the RCA report and CAB document as text files
#
# UI Architecture:
#   - Sidebar: application info, example incidents, and API status
#   - Main area: incident input form and tabbed results display
#   - Tabs: Triage | Similar Incidents | RCA Report | CAB Document
#
# The app uses Streamlit's session_state to persist results between
# interactions so the user can switch between tabs without re-running
# the pipeline on every click.
# ─────────────────────────────────────────────────────────────────────────────

import os
import logging
from datetime import datetime

# Suppress all warnings before any other imports
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"]     = "False"
logging.getLogger("chromadb").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

import streamlit as st

# ── Page configuration — must be the first Streamlit call ────────────────────
st.set_page_config(
    page_title = "ServicePilot — ITIL Process Automation",
    page_icon  = "🚀",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)

from graph import run_pipeline


# ── Custom CSS for professional appearance ────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #6B7280;
        margin-bottom: 2rem;
    }
    .severity-p1 {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .severity-p2 {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .severity-p3 {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .severity-p4 {
        background-color: #E0E7FF;
        color: #3730A3;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .incident-card {
        background: #F0F9FF;
        border-left: 4px solid #0EA5E9;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 1rem;
    }
    .stTextArea textarea {
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/artificial-intelligence.png",
        width=60
    )
    st.markdown("## ServicePilot")
    st.markdown("**Multi-Agent ITIL Process Automation**")
    st.markdown("---")

    st.markdown("### 🏗️ Pipeline Architecture")
    st.markdown("""
    **Agent 1 — Triage**
    Classifies severity, category, and assigns resolver team using ITIL standards.

    **Agent 2 — Resolution**
    Searches 100-incident knowledge base using BGE semantic search and synthesizes tailored resolution steps.

    **Agent 3 — RCA Report**
    Generates complete Root Cause Analysis with Five Whys, timeline, and preventive measures.

    **Agent 4 — CAB Document**
    Produces formal Change Advisory Board RFC for permanent preventive change approval.
    """)

    st.markdown("---")
    st.markdown("### 💡 Example Incidents")
    st.markdown("Click any example to load it:")

    examples = [
        "Production database connection pool exhausted. All checkout transactions failing. 502 errors on payment API.",
        "Kubernetes pods in CrashLoopBackOff. Payment service down. Missing Secret for gateway credentials.",
        "SSL certificate expired on main domain. All HTTPS traffic failing with security errors.",
        "Security team detected unauthorized API calls reading customer PII database. Active breach suspected.",
        "Network latency spike across all microservices. Response times went from 120ms to 8000ms.",
    ]

    for i, example in enumerate(examples, start=1):
        if st.button(f"Example {i}", key=f"ex_{i}", use_container_width=True):
            st.session_state["incident_input"] = example

    st.markdown("---")
    st.markdown("### ⚙️ System Info")
    st.markdown("""
    - **LLM**: LLaMA 3.3 70B via Groq
    - **Embeddings**: BGE-Base (768-dim)
    - **Vector DB**: ChromaDB (100 incidents)
    - **Framework**: LangGraph + LangChain
    - **ITIL Processes**: Incident, Problem, Change Management
    """)


# ── Main content area ─────────────────────────────────────────────────────────

st.markdown(
    '<div class="main-header">🚀 ServicePilot</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="sub-header">Multi-Agent ITIL Process Automation System — '
    'Powered by LangGraph, BGE Semantic Search, and LLaMA 3.3 70B</div>',
    unsafe_allow_html=True
)

# ── Incident input form ───────────────────────────────────────────────────────

st.markdown("### 📋 Describe the Incident")
st.markdown(
    "Enter a raw incident description in plain English exactly as an engineer "
    "would report it. The pipeline will automatically triage, retrieve similar "
    "past incidents, generate an RCA report, and produce a CAB change request."
)

# Use session_state to persist the text area content across example button clicks
default_text = st.session_state.get("incident_input", "")

incident_input = st.text_area(
    label       = "Incident Description",
    value       = default_text,
    height      = 150,
    placeholder = (
        "Example: Production authentication service is completely down. "
        "All users are getting 502 Bad Gateway errors when trying to log in. "
        "The issue started 20 minutes ago and affects all 50,000 active users."
    ),
    key         = "incident_textarea"
)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    run_button = st.button(
        "🔍 Run ITIL Pipeline",
        type            = "primary",
        use_container_width = True,
        disabled        = not incident_input.strip()
    )

with col2:
    clear_button = st.button(
        "🗑️ Clear",
        use_container_width = True
    )

if clear_button:
    st.session_state["incident_input"] = ""
    st.session_state.pop("pipeline_result", None)
    st.rerun()


# ── Pipeline execution ────────────────────────────────────────────────────────

if run_button and incident_input.strip():
    with st.spinner(
        "🤖 Running 4-agent ITIL pipeline... "
        "Triage → Resolution → RCA → CAB (15-20 seconds)"
    ):
        try:
            result = run_pipeline(incident_input.strip())
            st.session_state["pipeline_result"] = result
            st.session_state["pipeline_timestamp"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            st.success("✅ Pipeline completed successfully. All 4 agents ran.")
        except Exception as e:
            st.error(f"Pipeline error: {str(e)}")
            st.stop()


# ── Results display ───────────────────────────────────────────────────────────

if "pipeline_result" in st.session_state:
    result    = st.session_state["pipeline_result"]
    timestamp = st.session_state.get("pipeline_timestamp", "")
    triage    = result.triage_result

    st.markdown("---")
    st.markdown(f"### 📊 Pipeline Results — *{timestamp}*")

    # Quick summary metrics row
    m1, m2, m3, m4 = st.columns(4)

    severity_colors = {"P1": "🔴", "P2": "🟠", "P3": "🟡", "P4": "🟢"}
    severity_icon   = severity_colors.get(triage.severity, "⚪")

    with m1:
        st.metric("Severity", f"{severity_icon} {triage.severity}")
    with m2:
        st.metric("Category", triage.category)
    with m3:
        st.metric("Est. Resolution", triage.estimated_resolution_time)
    with m4:
        confidence = result.similar_incidents.get(
            "synthesis", {}
        ).get("confidence_level", "N/A")
        st.metric("RAG Confidence", confidence)

    st.markdown("")

    # Four tabs — one per agent output
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Triage Classification",
        "🔍 Similar Incidents & Resolution",
        "📄 RCA Report",
        "📋 CAB Document"
    ])

    # ── Tab 1: Triage Agent output ────────────────────────────────────────────
    with tab1:
        st.markdown("#### Agent 1 — ITIL Triage Classification")
        st.markdown(
            "The triage agent analyzed the incident description and produced "
            "the following ITIL-compliant classification. This classification "
            "is used by all subsequent agents as the authoritative context."
        )
        st.markdown("")

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Classification Details**")
            severity_css = f"severity-{triage.severity.lower()}"
            st.markdown(
                f'<span class="{severity_css}">{triage.severity}</span>',
                unsafe_allow_html=True
            )
            st.markdown("")

            st.markdown(f"**Affected Service:** {triage.affected_service}")
            st.markdown(f"**Category:** {triage.category}")
            st.markdown(f"**Recommended Team:** {triage.recommended_team}")
            st.markdown(
                f"**Estimated Resolution:** {triage.estimated_resolution_time}"
            )

        with c2:
            st.markdown("**Business Impact**")
            st.info(triage.business_impact)

            st.markdown("**Initial Diagnosis**")
            st.warning(triage.initial_diagnosis)

    # ── Tab 2: Resolution Agent output ───────────────────────────────────────
    with tab2:
        st.markdown("#### Agent 2 — Knowledge Base Retrieval & Resolution Synthesis")
        st.markdown(
            "The resolution agent searched the 100-incident ITIL knowledge base "
            "using BGE-Base semantic search and synthesized resolution guidance "
            "tailored to this specific incident."
        )
        st.markdown("")

        retrieved  = result.similar_incidents.get("retrieved_incidents", [])
        synthesis  = result.similar_incidents.get("synthesis", {})

        # Retrieved incidents section
        st.markdown("**Top 3 Similar Past Incidents from Knowledge Base**")

        for i, inc in enumerate(retrieved, start=1):
            score = inc["similarity_score"]
            with st.expander(
                f"#{i} [{inc['incident_id']}] {inc['title']} — "
                f"Similarity: {score}%",
                expanded = (i == 1)
            ):
                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    st.markdown(f"**Severity:** {inc['severity']}")
                    st.markdown(f"**Category:** {inc['category']}")
                with ec2:
                    st.markdown(
                        f"**Resolved In:** {inc['resolved_in_minutes']} min"
                    )
                    st.markdown(f"**Team:** {inc['assigned_team']}")
                with ec3:
                    # Similarity score as progress bar
                    st.progress(int(score) / 100, text=f"{score}% match")

                st.markdown(f"**Root Cause:** {inc['root_cause']}")

                if inc.get("resolution_steps"):
                    st.markdown("**Resolution Steps:**")
                    for step in inc["resolution_steps"]:
                        if step.strip():
                            st.markdown(f"- {step}")

        st.markdown("")
        st.markdown("**LLM Resolution Synthesis**")

        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.metric(
                "Primary Reference",
                synthesis.get("primary_reference", "N/A")
            )
        with sc2:
            st.metric(
                "Confidence",
                synthesis.get("confidence_level", "N/A")
            )
        with sc3:
            st.metric(
                "Est. Resolution Time",
                synthesis.get("estimated_total_resolution_time", "N/A")
            )

        if synthesis.get("key_differences"):
            st.markdown(
                f"**Key Differences from Past Incidents:** "
                f"{synthesis['key_differences']}"
            )

        if synthesis.get("recommended_steps"):
            st.markdown("**Recommended Resolution Steps:**")
            for step in synthesis["recommended_steps"]:
                if step.strip():
                    st.markdown(f"{step}")

        if synthesis.get("confidence_reason"):
            st.caption(
                f"*Confidence reasoning: {synthesis['confidence_reason']}*"
            )

    # ── Tab 3: RCA Report ─────────────────────────────────────────────────────
    with tab3:
        st.markdown("#### Agent 3 — Root Cause Analysis Report")
        st.markdown(
            "The following RCA document was generated by synthesizing the triage "
            "classification, retrieved knowledge base incidents, and resolution "
            "synthesis. This document is ready for client delivery and JIRA "
            "attachment."
        )
        st.markdown("")

        if result.rca_report:
            word_count = len(result.rca_report.split())
            st.caption(f"Document length: {word_count} words")

            # Display the full RCA report in a clean text block
            st.markdown(result.rca_report)

            # Download button
            st.download_button(
                label     = "⬇️ Download RCA Report (.txt)",
                data      = result.rca_report,
                file_name = (
                    f"RCA_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                ),
                mime      = "text/plain"
            )

    # ── Tab 4: CAB Document ───────────────────────────────────────────────────
    with tab4:
        st.markdown("#### Agent 4 — Change Advisory Board Document")
        st.markdown(
            "The following RFC (Request for Change) document was generated for "
            "presentation at the next CAB meeting. It covers the proposed permanent "
            "preventive change, risk assessment, implementation plan, and rollback "
            "procedure."
        )
        st.markdown("")

        if result.cab_document:
            word_count = len(result.cab_document.split())
            st.caption(f"Document length: {word_count} words")

            # Display the full CAB document
            st.markdown(result.cab_document)

            # Download button
            st.download_button(
                label     = "⬇️ Download CAB Document (.txt)",
                data      = result.cab_document,
                file_name = (
                    f"CAB_RFC_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                ),
                mime      = "text/plain"
            )

else:
    # Placeholder shown before the user runs the pipeline
    st.markdown("---")
    st.info(
        "👆 Enter an incident description above and click **Run ITIL Pipeline** "
        "to start the four-agent automation system. You can also click any "
        "example incident in the sidebar to load a pre-written scenario.",
        icon="ℹ️"
    )
    st.markdown("")

    # Architecture diagram as a static explanation
    st.markdown("### How ServicePilot Works")

    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1:
        st.markdown("**🎯 Agent 1: Triage**")
        st.markdown(
            "Classifies severity (P1-P4), identifies affected service and "
            "category, assigns resolver team, estimates resolution time."
        )
    with ac2:
        st.markdown("**🔍 Agent 2: Resolution**")
        st.markdown(
            "Searches 100-incident knowledge base with BGE semantic search, "
            "retrieves top-3 similar past incidents, synthesizes resolution steps."
        )
    with ac3:
        st.markdown("**📄 Agent 3: RCA**")
        st.markdown(
            "Generates complete Root Cause Analysis with Five Whys, incident "
            "timeline, impact assessment, and preventive measures."
        )
    with ac4:
        st.markdown("**📋 Agent 4: CAB**")
        st.markdown(
            "Produces formal Change Advisory Board RFC with risk assessment, "
            "implementation plan, rollback procedure, and approval matrix."
        )