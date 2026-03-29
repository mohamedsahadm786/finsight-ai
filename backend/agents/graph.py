"""
LangGraph Pipeline — Wires all 6 agents into a directed graph.

Execution order:
  Agent 1 (Parser) → Agent 2 (Extractor) ─┐
                   → Agent 3 (Sentiment) ──┼→ Agent 5 (Risk Scorer) → Agent 6 (Report Writer)
                   → Agent 4 (Breach) ─────┘

Agents 2, 3, 4 run after Agent 1 completes.
Agent 5 runs after Agent 2 completes (needs extracted ratios).
Agent 6 runs after ALL of 2, 3, 4, 5 complete.

NOTE on LangGraph parallel execution:
LangGraph's StateGraph does NOT natively run nodes in parallel threads.
When we add edges from parser → extractor, parser → sentiment, parser → breach,
LangGraph runs them sequentially in the order they were added.
True parallelism would require asyncio or threading, which adds complexity.
For this project, sequential execution is perfectly fine — the mock pipeline
completes in seconds, and on EC2 the bottleneck is LLaMA inference (single-threaded anyway).
"""

import logging
from typing import Any

from langgraph.graph import StateGraph, END

from backend.agents.state import PipelineState
from backend.agents.agent_1_parser import agent_1_parser
from backend.agents.agent_2_extractor import agent_2_extractor
from backend.agents.agent_3_sentiment import agent_3_sentiment
from backend.agents.agent_4_breach import agent_4_breach
from backend.agents.agent_5_risk_scorer import agent_5_risk_scorer
from backend.agents.agent_6_report_writer import agent_6_report_writer

logger = logging.getLogger(__name__)


def _should_run_risk_scorer(state: dict[str, Any]) -> str:
    """
    Conditional edge: decides whether Agent 5 (Risk Scorer) should run.

    If Agent 2 found fewer than 2 ratios, XGBoost scoring is unreliable
    and we skip directly to Agent 6 (Report Writer).
    """
    ratios_found = state.get("ratios_found_count", 0)
    errors = state.get("errors", [])

    if errors:
        logger.warning(f"Pipeline has errors: {errors}. Proceeding to report writer.")
        return "report_writer"

    if ratios_found < 2:
        logger.warning(
            f"Only {ratios_found} ratios found. Skipping risk scorer, "
            f"going directly to report writer."
        )
        return "report_writer"

    return "risk_scorer"


def build_pipeline_graph() -> StateGraph:
    """
    Build and compile the LangGraph pipeline.

    Returns a compiled graph ready to be invoked with:
        result = graph.invoke(initial_state)
    """
    workflow = StateGraph(PipelineState)

    # --- Add all 6 agent nodes ---
    workflow.add_node("parser", agent_1_parser)
    workflow.add_node("extractor", agent_2_extractor)
    workflow.add_node("sentiment", agent_3_sentiment)
    workflow.add_node("breach", agent_4_breach)
    workflow.add_node("risk_scorer", agent_5_risk_scorer)
    workflow.add_node("report_writer", agent_6_report_writer)

    # --- Set entry point ---
    workflow.set_entry_point("parser")

    # --- Agent 1 → Agents 2, 3, 4 ---
    # After parser completes, run extractor first (sequential execution)
    workflow.add_edge("parser", "extractor")

    # --- Agent 2 → Agent 3 (sentiment runs after extractor) ---
    workflow.add_edge("extractor", "sentiment")

    # --- Agent 3 → Agent 4 (breach runs after sentiment) ---
    workflow.add_edge("sentiment", "breach")

    # --- Agent 4 → Conditional: Risk Scorer or Report Writer ---
    workflow.add_conditional_edges(
        "breach",
        _should_run_risk_scorer,
        {
            "risk_scorer": "risk_scorer",
            "report_writer": "report_writer",
        },
    )

    # --- Agent 5 → Agent 6 ---
    workflow.add_edge("risk_scorer", "report_writer")

    # --- Agent 6 → END ---
    workflow.add_edge("report_writer", END)

    # --- Compile the graph ---
    graph = workflow.compile()
    logger.info("LangGraph pipeline compiled successfully.")

    return graph


# ---------------------------------------------------------------------------
# Module-level compiled graph — ready to be invoked by the Celery task
# ---------------------------------------------------------------------------
pipeline_graph = build_pipeline_graph()