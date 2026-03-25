import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from llm_service import configure_gemini, expand_idea_to_queries
from creator_profile_service import build_creator_profile
from data_feature_extractor import extract_features
from analyst_agent import run_analyst_agent
from optimizer_agent import OptimizerAgentOutput, run_optimizer_agent
from strategist_agent import run_strategist_agent
from models import IdeaRequest
from youtube_service import (
    detect_fragmented,
    detect_monopoly,
    detect_personality_driven,
    get_competitor_data,
)

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "YouTube AI Strategy Engine Active"}


@app.get("/test")
def test_gemini():
    """Lightweight health-check: confirms Gemini API connectivity."""
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="Missing GEMINI_API_KEY in environment.")
    configure_gemini(gemini_api_key)
    queries = expand_idea_to_queries("study tips")
    return {"status": "ok", "queries": queries}


@app.post("/analyze", response_model=OptimizerAgentOutput)
def analyze(request: IdeaRequest) -> OptimizerAgentOutput:
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="Missing GEMINI_API_KEY in environment.")
    youtube_api_key = os.environ.get("YOUTUBE_API_KEY")
    if not youtube_api_key:
        raise HTTPException(status_code=500, detail="Missing YOUTUBE_API_KEY in environment.")

    try:
        t0 = time.monotonic()
        configure_gemini(gemini_api_key)

        t_queries = time.monotonic()
        queries = expand_idea_to_queries(request.idea)
        print({"stage": "main", "action": "queries_done", "elapsed_s": round(time.monotonic() - t_queries, 3)})
        if not queries:
            queries = [request.idea]

        t_videos = time.monotonic()
        videos = get_competitor_data(queries, youtube_api_key)
        print({"stage": "main", "action": "videos_done", "elapsed_s": round(time.monotonic() - t_videos, 3), "video_count": len(videos)})
        
        if not videos:
            raise HTTPException(
                status_code=400,
                detail="No relevant videos found. Try a clearer idea."
            )

        t_features = time.monotonic()
        features = extract_features(videos)
        print({"stage": "main", "action": "features_done", "elapsed_s": round(time.monotonic() - t_features, 3)})

        is_monopoly = detect_monopoly(videos)
        is_personality = detect_personality_driven(videos)
        is_fragmented = detect_fragmented(videos)

        t_profile = time.monotonic()
        derived_profile = build_creator_profile(request.creator_profile)
        print({
            "stage": "main",
            "action": "creator_profile_built",
            "mode": derived_profile.mode,
            "channel_size": derived_profile.channel_size_bucket,
            "elapsed_s": round(time.monotonic() - t_profile, 3),
        })

        t_analyst = time.monotonic()
        analyst_output = run_analyst_agent(
            request.idea,
            features,
            derived_profile,
            is_monopoly=is_monopoly,
            is_personality=is_personality,
            is_fragmented=is_fragmented,
            content_mode=request.content_mode,
        )
        print({"stage": "main", "action": "analyst_done", "elapsed_s": round(time.monotonic() - t_analyst, 3)})

        t_strategist = time.monotonic()
        strategist_output = run_strategist_agent(
            request.idea,
            analyst_output,
            derived_profile,
            content_mode=request.content_mode,
        )
        print({"stage": "main", "action": "strategist_done", "elapsed_s": round(time.monotonic() - t_strategist, 3)})
        # Stored for now; do not merge into the strategy response yet.

        t_optimizer = time.monotonic()
        optimizer_output = run_optimizer_agent(
            request.idea,
            analyst_output,
            strategist_output,
            derived_profile,
            content_mode=request.content_mode,
        )

        print({
            "stage": "main",
            "action": "optimizer_done",
            "elapsed_s": round(time.monotonic() - t_optimizer, 3),
            "total_elapsed_s": round(time.monotonic() - t0, 3),
        })

        return optimizer_output
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"External API failure: {exc}") from exc
