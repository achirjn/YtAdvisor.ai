from typing import List, Optional

from pydantic import BaseModel

from creator_profile import CreatorProfile


class IdeaRequest(BaseModel):
    idea: str
    content_mode: str = "SEARCH"  # "SEARCH" or "BROWSE"
    creator_profile: Optional[CreatorProfile] = None


# --- Analyst Agent Models ---
class Verdict(BaseModel):
    decision: str  # GO, MODIFY, AVOID
    confidence_score: int  # 0-100

    # 🔥 NEW (important)
    one_line_reason: str

    brutal_truth: str
    opportunity_type: str  # VIRAL, SATURATED, NICHE, PERSONAL, TRENDING, DEAD


class CompetitorMetrics(BaseModel):
    common_title_keywords_percentage: str
    average_video_age: str
    highest_breakout_multiplier: float


class MarketAnalysis(BaseModel):
    demand_score: int
    competition_score: int

    viral_potential: int
    exploitability: int
    market_type: str  # SATURATED, TRENDING, DEAD, NOVEL, PERSONALITY, HYBRID

    dominant_patterns: List[str]
    content_gaps: List[str]


class AnalystReport(BaseModel):
    verdict: Verdict
    competitor_metrics: CompetitorMetrics
    market_analysis: MarketAnalysis


# --- Creative Agent Models ---
class Strategy(BaseModel):
    positioning: str
    content_angle: str
    differentiation: str


class TitleExecution(BaseModel):
    primary: str
    alternatives: List[str]


class Execution(BaseModel):
    title: TitleExecution
    thumbnail_concept: str
    hook_script: str
    target_video_length: str
    video_structure_timestamps: List[str]


class ScoringMatrix(BaseModel):
    idea_viability: int
    ctr_potential: int
    retention_difficulty: int
    overall_score: int

    viral_score: int
    competition_difficulty: int


class ActionPlan(BaseModel):
    do_this_now: List[str]
    avoid_this: List[str]


class CreativeStrategy(BaseModel):
    strategy: Strategy
    execution: Execution
    scoring_matrix: ScoringMatrix
    action_plan: ActionPlan
    effort_level: str


# --- Final Output ---
class StrategyResponse(BaseModel):
    verdict: Verdict
    competitor_metrics: CompetitorMetrics
    market_analysis: MarketAnalysis
    strategy: Strategy
    execution: Execution
    scoring_matrix: ScoringMatrix
    action_plan: ActionPlan
    effort_level: str


class VideoData(BaseModel):
    video_id: str
    channel_id: str
    title: str
    view_count: int
    subscriber_count: int
    age_days: int
    category_id: str
    transcript: str
    breakout_multiplier: float