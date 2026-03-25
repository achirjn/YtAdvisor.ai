from typing import List, Optional

from pydantic import BaseModel, Field


class PastVideo(BaseModel):
    title: str
    views: int
    format: str


class CreatorProfile(BaseModel):
    channel_id: Optional[str] = None
    niche: Optional[str] = None
    subscriber_count: Optional[int] = None
    avg_views: Optional[int] = None
    strengths: Optional[List[str]] = Field(default_factory=list)
    weaknesses: Optional[List[str]] = Field(default_factory=list)
    interests: Optional[List[str]] = Field(default_factory=list)
    recent_videos: Optional[List[PastVideo]] = Field(default_factory=list)


class DerivedCreatorProfile(BaseModel):
    mode: str
    subscriber_count: Optional[int]
    avg_views: Optional[int]
    niche: Optional[str]
    channel_size_bucket: str
    growth_stage: str
    performance_ratio: float
    competition_tolerance: str
    strengths: List[str]
    weaknesses: List[str]
    interests: List[str]
    recent_videos: List[PastVideo]

