from typing import List

from pydantic import BaseModel


class IdeaRequest(BaseModel):
    idea: str


class StrategyPivot(BaseModel):
    new_titles: List[str]
    thumbnail_directive: str
    hook_rewrite: str


class StrategyResponse(BaseModel):
    market_verdict: str
    search_volume: str      # E.g., "Low", "Medium", "High"
    browse_potential: str   # E.g., "Low", "Medium", "High (Viral)"
    actionable_weaknesses: List[str]
    execution_risks: List[str]
    killer_idea: str        # NEW: One highly specific, non-generic video concept
    strategy_pivot: StrategyPivot


class VideoData(BaseModel):
    video_id: str
    title: str
    view_count: int
    subscriber_count: int
    age_days: int
    category_id: str
    transcript: str
