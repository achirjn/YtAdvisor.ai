import os
import sys
import time
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)


from pydantic import BaseModel as _BaseModel
from typing import Optional as _Optional

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
    VerdictEnum,
    ConfidenceEnum,
    SmallCreatorVerdictEnum,
    ArchetypeEnum,
)
from analyst_agent import run_analyst_agent
from strategist_agent import run_strategist_agent
from optimizer_agent import run_optimizer_agent
from audience_pipeline_scheduler import start_pipeline, get_pipeline_status, get_pipeline_dna_string, PipelinePhase


class AutoAnalyzeRequest(_BaseModel):
    video_idea: str
    creator_dna: _Optional[str] = None


class ChannelPipelineRequest(_BaseModel):
    channel_id: str
    youtube_api_key: _Optional[str] = None


class ChannelPipelineStatus(_BaseModel):
    channel_id: str
    channel_title: str
    phase: str
    videos_processed: int
    total_videos_on_channel: int
    is_reliable: bool
    last_error: str
    dna_summary: _Optional[str] = None




app = FastAPI(title="Dimenziq API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "ok", "product": "Dimenziq", "version": "2.0.0"}

@app.post("/api/v1/analyze", response_model=DimenziqAnalysisOutput)
def analyze(payload: AgentContext):
    try:
        analyst_result = run_analyst_agent(payload)
        strategist_result = run_strategist_agent(payload, analyst_result)
        optimizer_result = run_optimizer_agent(payload, analyst_result, strategist_result)

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

        return output

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/analyze/auto", response_model=DimenziqAnalysisOutput)
def analyze_auto(payload: AutoAnalyzeRequest):
    """
    Full Pipeline 1 endpoint. Takes only a video idea and optional creator DNA.
    Automatically runs competitor scraping, graph analysis, thumbnail vision,
    and all three AI agents. Returns DimenziqAnalysisOutput.
    """
    print("[auto] invoking LangGraph pipeline...")
    t_total = time.monotonic()
    try:
        from pipeline_graph import pipeline_app
        initial_state = {
            "video_idea": payload.video_idea,
            "creator_dna": payload.creator_dna,
        }
        state = pipeline_app.invoke(initial_state)
        if state.get("error"):
            status_code = state.get("error_status_code", 500)
            raise HTTPException(
                status_code=status_code,
                detail=state["error"]
            )
        print(f"[auto] LangGraph pipeline complete — total time: {time.monotonic() - t_total:.1f}s")
        return state["output"]
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}") from e


@app.post("/api/v1/audience/pipeline/start", status_code=202)
def start_audience_pipeline(payload: ChannelPipelineRequest):
    api_key = payload.youtube_api_key or os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="YOUTUBE_API_KEY not set in environment.")

    result = start_pipeline(payload.channel_id, api_key)
    return {"accepted": True, "channel_id": result.channel_id, "phase": result.phase}


@app.get(
    "/api/v1/audience/pipeline/status/{channel_id}",
    response_model=ChannelPipelineStatus,
)
def audience_pipeline_status(channel_id: str):
    state = get_pipeline_status(channel_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Pipeline not found for channel.")

    dna_summary = None
    if state.phase in (PipelinePhase.ENRICHING, PipelinePhase.COMPLETE):
        dna_summary = get_pipeline_dna_string(channel_id)

    return ChannelPipelineStatus(
        channel_id=state.channel_id,
        channel_title=state.channel_title,
        phase=state.phase.value,
        videos_processed=state.videos_processed,
        total_videos_on_channel=state.total_videos_on_channel,
        is_reliable=state.is_reliable,
        last_error=state.last_error,
        dna_summary=dna_summary,
    )
