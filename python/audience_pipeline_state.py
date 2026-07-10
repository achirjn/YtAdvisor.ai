from typing import List, Optional
try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class AudiencePipelineState(TypedDict, total=False):
    # PipelineState fields
    channel_id: str
    channel_title: str
    youtube_api_key: str
    phase: str  # from PipelinePhase
    is_reliable: bool
    total_videos_on_channel: int
    videos_processed: int
    current_batch_index: int
    last_run_timestamp: float
    next_run_timestamp: float
    consecutive_failures: int
    last_error: str

    # CreatorDNASnapshot fields
    dna_summary: Optional[str]
    total_comments_analysed: int
    audience_age_range: str
    preferred_format: str
    recurring_questions: List[str]
    content_complaints: List[str]
    engagement_tone: str
