from typing import List, Optional, Any
try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

from api_models import AgentContext, DimenziqAnalysisOutput


class PipelineState(TypedDict, total=False):
    # Inputs
    video_idea: str
    creator_dna: Optional[str]

    # Intermediate values
    queries: List[str]
    intel: Any  # CompetitorIntelligence from competitor_scraper
    graph_signals: Any  # MarketGraphSignals from market_graph
    thumbnail_analysis: Any  # ThumbnailAnalysis from thumbnail_analyzer
    median_subscriber_count: int
    agent_context: AgentContext

    # Agent outputs
    analyst_output: dict
    strategist_output: dict
    optimizer_output: dict

    # Final outputs
    output: DimenziqAnalysisOutput

    # Error handling
    error: Optional[str]
    error_status_code: Optional[int]
