"""
PIPELINE MAP: `/api/v1/analyze/auto` sequence of function calls from `main.py`
=============================================================================

1. `queries = expand_idea_to_queries(video_idea)`
   - Module: `llm_service`
   - Input: `payload.video_idea` (str)
   - Output: `queries` (List[str]). Falls back to `[video_idea]` if empty.
   
2. `intel = scrape_competitor_intelligence(queries, youtube_api_key)`
   - Module: `competitor_scraper`
   - Input: `queries` (List[str]), `youtube_api_key` (str)
   - Output: `intel` (CompetitorIntelligence)

3. `graph_signals = analyse_market_graph(intel)`
   - Module: `market_graph` (imported as `from market_graph import build_market_graph as analyse_market_graph`)
   - Input: `intel` (CompetitorIntelligence)
   - Output: `graph_signals` (MarketGraphSignals)
   - Dependency: Depends on step 2 (`intel`). Independent of step 4.

4. `thumbnail_analysis = analyse_thumbnails(intel.top_thumbnail_urls)`
   - Module: `thumbnail_analyzer`
   - Input: `intel.top_thumbnail_urls` (List[str])
   - Output: `thumbnail_analysis` (ThumbnailAnalysis)
   - Dependency: Depends on step 2 (`intel`). Independent of step 3.

   *CONFIRMATION*: Market graph analysis (step 3) and thumbnail analysis (step 4)
   do not depend on each other's outputs. Both rely strictly on different fields
   of `intel` produced in step 2. Therefore, they are executed in parallel.

5. Build intermediate values:
   - `competitor_data = intelligence_to_competitor_data(intel)`
     - Module: `competitor_scraper`
     - Input: `intel` (CompetitorIntelligence)
     - Output: `competitor_data` (CompetitorData)
   - `median_subs = get_median_subscriber_count(intel)`
     - Module: `competitor_scraper`
     - Input: `intel` (CompetitorIntelligence)
     - Output: `median_subs` (int)
   - `agent_context = AgentContext(request=InitialRequest(video_idea=video_idea, creator_dna=creator_dna), competitors=competitor_data)`
   - `graph_for_analyst = _analyst_graph_view(graph_signals)`
     - Local private function in `main.py`
     - Input: `graph_signals` (MarketGraphSignals)
     - Output: `graph_for_analyst` (SimpleNamespace)

6. `analyst_result = run_analyst_agent(agent_context, graph_signals=graph_for_analyst, median_subscriber_count=median_subs)`
   - Module: `analyst_agent`
   - Input: `agent_context` (AgentContext), `graph_signals` (SimpleNamespace), `median_subscriber_count` (int)
   - Output: `analyst_result` (dict)

7. `strategist_result = run_strategist_agent(agent_context, analyst_result, thumbnail_analysis=thumbnail_analysis)`
   - Module: `strategist_agent`
   - Input: `agent_context` (AgentContext), `analyst_result` (dict), `thumbnail_analysis` (ThumbnailAnalysis)
   - Output: `strategist_result` (dict)

8. `optimizer_result = run_optimizer_agent(agent_context, analyst_result, strategist_result)`
   - Module: `optimizer_agent`
   - Input: `agent_context` (AgentContext), `analyst_result` (dict), `strategist_result` (dict)
   - Output: `optimizer_result` (dict)

9. Assemble Output:
   - Construct `DimenziqAnalysisOutput` using the three agent outputs.
   - Return: `output` (DimenziqAnalysisOutput)
"""

import os
import sys
import time
from types import SimpleNamespace
from typing import Dict, List, Optional, Any

from langgraph.graph import START, END, StateGraph

# Import modules and functions from the python directory of the workspace
from api_models import (
    AgentContext,
    InitialRequest,
    DimenziqAnalysisOutput,
    VerdictSection,
    MarketSection,
    CreativeSection,
    ExecutionSection,
    GrowthSection,
    ContentGap,
    TitleVariant,
    RetentionTrap,
    NextVideoIdea,
)
from llm_service import expand_idea_to_queries
from competitor_scraper import (
    scrape_competitor_intelligence,
    intelligence_to_competitor_data,
    get_median_subscriber_count,
)
from market_graph import build_market_graph as analyse_market_graph
from thumbnail_analyzer import analyse_thumbnails
from analyst_agent import run_analyst_agent
from strategist_agent import run_strategist_agent
from optimizer_agent import run_optimizer_agent

from pipeline_state import PipelineState


def _analyst_graph_view(mg) -> SimpleNamespace:
    """Maps MarketGraphSignals onto fields expected by run_analyst_agent graph prompt."""
    share = mg.monopoly_share_pct / 100.0
    return SimpleNamespace(
        market_structure_summary=(
            f"{mg.cluster_count} clusters; {mg.unique_channels} channels; "
            f"{mg.unique_categories} categories; fragmented={mg.is_fragmented}; "
            f"monopoly={mg.is_monopoly}; keyword_saturation={mg.keyword_saturation}"
        ),
        entry_opportunity_summary=(
            f"opportunity_cluster={mg.has_opportunity_cluster}; "
            f"bridge_videos={len(mg.bridge_video_ids)}; "
            f"keywords={','.join(mg.dominant_keywords[:8])}"
        ),
        small_creator_opportunity=mg.small_creator_success_rate,
        cluster_count=mg.cluster_count,
        monopoly_detected=mg.is_monopoly,
        monopoly_channel_share=share,
        breakout_concentration=f"{mg.market_dynamics} | {mg.breakout_distribution}",
        top_breakout_multiplier=mg.top_breakout_multiplier,
        avg_breakout_multiplier=mg.avg_breakout_multiplier,
        analyst_narrative=mg.analyst_summary,
    )


# ── Nodes ────────────────────────────────────────────────────────────

def expand_queries_node(state: PipelineState) -> Dict[str, Any]:
    try:
        queries = expand_idea_to_queries(state["video_idea"])
        if not queries:
            queries = [state["video_idea"]]
        return {"queries": queries}
    except Exception as e:
        # Fallback to the original video idea if expansion fails
        return {"queries": [state["video_idea"]]}


def scrape_competitors_node(state: PipelineState) -> Dict[str, Any]:
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")
    if not youtube_api_key:
        return {
            "error": "YOUTUBE_API_KEY not set in environment.",
            "error_status_code": 500,
        }

    try:
        intel = scrape_competitor_intelligence(state["queries"], youtube_api_key)
        if not intel or not intel.scrape_successful:
            error_msg = intel.error_message if intel else "Unknown scraping error."
            return {
                "error": f"Competitor scraping failed: {error_msg}",
                "error_status_code": 400,
            }
        return {"intel": intel}
    except Exception as e:
        return {
            "error": f"Competitor scraping failed: {str(e)}",
            "error_status_code": 500,
        }


def analyze_market_graph_node(state: PipelineState) -> Dict[str, Any]:
    graph_signals = analyse_market_graph(state["intel"])
    return {"graph_signals": graph_signals}


def analyze_thumbnails_node(state: PipelineState) -> Dict[str, Any]:
    thumbnail_analysis = analyse_thumbnails(state["intel"].top_thumbnail_urls)
    return {"thumbnail_analysis": thumbnail_analysis}


def build_context_node(state: PipelineState) -> Dict[str, Any]:
    competitor_data = intelligence_to_competitor_data(state["intel"])
    median_subs = get_median_subscriber_count(state["intel"])
    
    agent_context = AgentContext(
        request=InitialRequest(
            video_idea=state["video_idea"],
            creator_dna=state.get("creator_dna"),
        ),
        competitors=competitor_data,
    )
    return {
        "agent_context": agent_context,
        "median_subscriber_count": median_subs,
    }


def analyst_node(state: PipelineState) -> Dict[str, Any]:
    graph_for_analyst = _analyst_graph_view(state["graph_signals"])
    analyst_result = run_analyst_agent(
        state["agent_context"],
        graph_signals=graph_for_analyst,
        median_subscriber_count=state["median_subscriber_count"],
    )
    return {"analyst_output": analyst_result}


def strategist_node(state: PipelineState) -> Dict[str, Any]:
    strategist_result = run_strategist_agent(
        state["agent_context"],
        state["analyst_output"],
        thumbnail_analysis=state["thumbnail_analysis"],
    )
    return {"strategist_output": strategist_result}


def optimizer_node(state: PipelineState) -> Dict[str, Any]:
    optimizer_result = run_optimizer_agent(
        state["agent_context"],
        state["analyst_output"],
        state["strategist_output"],
    )
    return {"optimizer_output": optimizer_result}


def assemble_output_node(state: PipelineState) -> Dict[str, Any]:
    analyst_result = state["analyst_output"]
    strategist_result = state["strategist_output"]
    optimizer_result = state["optimizer_output"]

    output = DimenziqAnalysisOutput(
        verdict=VerdictSection(
            final_verdict=optimizer_result["final_verdict"],
            confidence=optimizer_result["confidence"],
            confidence_reason=optimizer_result["confidence_reason"],
            idea_upgrade=optimizer_result["idea_upgrade"],
            market_context=optimizer_result["market_context"],
            performance_benchmark=optimizer_result["performance_benchmark"],
            performance_outlook=optimizer_result["performance_outlook"],
            channel_strength=analyst_result["channel_strength"],
            channel_risk=analyst_result["channel_risk"],
        ),
        market=MarketSection(
            market_truth=analyst_result["market_truth"],
            dominant_force=analyst_result["dominant_force"],
            competitor_weakness=analyst_result["competitor_weakness"],
            audience_craving=analyst_result["audience_craving"],
            content_gaps=[
                ContentGap(gap=g["gap"], source=g["source"])
                for g in analyst_result.get("content_gaps", [])
            ],
            small_creator_verdict=analyst_result["small_creator_verdict"],
            small_creator_reason=analyst_result["small_creator_reason"],
            algorithm_signal=analyst_result["algorithm_signal"],
            satisfaction_risk=analyst_result["satisfaction_risk"],
            content_archetype=analyst_result["content_archetype"],
        ),
        creative=CreativeSection(
            suggested_title=strategist_result["suggested_title"],
            title_psychology=strategist_result["title_psychology"],
            title_alternatives=[
                TitleVariant(title=t["title"], psychology_tag=t["psychology_tag"])
                for t in strategist_result.get("title_alternatives", [])
            ],
            thumbnail_concept=strategist_result["thumbnail_concept"],
            thumbnail_contrast_rule=strategist_result["thumbnail_contrast_rule"],
            thumbnail_text_overlay=strategist_result.get("thumbnail_text_overlay", ""),
        ),
        execution=ExecutionSection(
            exact_hook_script=strategist_result["exact_hook_script"],
            hook_psychology=strategist_result["hook_psychology"],
            pacing_timeline=optimizer_result.get("pacing_timeline", []),
            retention_traps=[
                RetentionTrap(
                    moment=r["moment"],
                    reason=r["reason"],
                    fix=r["fix"],
                )
                for r in optimizer_result.get("retention_traps", [])
            ],
            win_conditions=optimizer_result.get("win_conditions", []),
            fail_conditions=optimizer_result.get("fail_conditions", []),
            shorts_test_recommended=optimizer_result["shorts_test_recommended"],
            shorts_test_instruction=optimizer_result.get("shorts_test_instruction", ""),
        ),
        growth=GrowthSection(
            pinned_comment=optimizer_result["pinned_comment"],
            community_post_seed=optimizer_result["community_post_seed"],
            description_timestamps=optimizer_result["description_timestamps"],
            next_video_series=[
                NextVideoIdea(
                    title=n["title"],
                    strategic_reason=n["strategic_reason"],
                    priority=n["priority"],
                )
                for n in optimizer_result.get("next_video_series", [])
            ],
            series_positioning=optimizer_result["series_positioning"],
        ),
    )
    return {"output": output}


def error_node(state: PipelineState) -> Dict[str, Any]:
    print(f"[pipeline] routing to terminal error node: {state.get('error')}")
    return {}


# ── Edge Routing ──────────────────────────────────────────────────────

def check_scrape_result(state: PipelineState) -> List[str]:
    if state.get("error"):
        return ["error_node"]
    return ["analyze_market_graph_node", "analyze_thumbnails_node"]


# ── Graph Construction ───────────────────────────────────────────────

workflow = StateGraph(PipelineState)

# Add nodes
workflow.add_node("expand_queries_node", expand_queries_node)
workflow.add_node("scrape_competitors_node", scrape_competitors_node)
workflow.add_node("analyze_market_graph_node", analyze_market_graph_node)
workflow.add_node("analyze_thumbnails_node", analyze_thumbnails_node)
workflow.add_node("build_context_node", build_context_node)
workflow.add_node("analyst_node", analyst_node)
workflow.add_node("strategist_node", strategist_node)
workflow.add_node("optimizer_node", optimizer_node)
workflow.add_node("assemble_output_node", assemble_output_node)
workflow.add_node("error_node", error_node)

# Set entry point
workflow.add_edge(START, "expand_queries_node")
workflow.add_edge("expand_queries_node", "scrape_competitors_node")

# Conditional fanning out from scraping
workflow.add_conditional_edges(
    "scrape_competitors_node",
    check_scrape_result,
    {
        "error_node": "error_node",
        "analyze_market_graph_node": "analyze_market_graph_node",
        "analyze_thumbnails_node": "analyze_thumbnails_node",
    }
)

# Parallel fanning in to build context
workflow.add_edge("analyze_market_graph_node", "build_context_node")
workflow.add_edge("analyze_thumbnails_node", "build_context_node")

# Linear steps down the pipeline
workflow.add_edge("build_context_node", "analyst_node")
workflow.add_edge("analyst_node", "strategist_node")
workflow.add_edge("strategist_node", "optimizer_node")
workflow.add_edge("optimizer_node", "assemble_output_node")

# Terminal node connections
workflow.add_edge("assemble_output_node", END)
workflow.add_edge("error_node", END)

# Compile app
pipeline_app = workflow.compile()
