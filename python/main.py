import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .llm_service import configure_gemini, expand_idea_to_queries, generate_strategy
from .models import IdeaRequest, StrategyResponse
from .youtube_service import (
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


@app.post("/analyze", response_model=StrategyResponse)
async def analyze(request: IdeaRequest) -> StrategyResponse:
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="Missing GEMINI_API_KEY in environment.")
    youtube_api_key = os.environ.get("YOUTUBE_API_KEY")
    if not youtube_api_key:
        raise HTTPException(status_code=500, detail="Missing YOUTUBE_API_KEY in environment.")

    try:
        configure_gemini(gemini_api_key)
        queries = expand_idea_to_queries(request.idea)
        videos = get_competitor_data(queries, youtube_api_key)

        is_monopoly = detect_monopoly(videos)
        is_personality = detect_personality_driven(videos)
        is_fragmented = detect_fragmented([video.video_id for video in videos], youtube_api_key)

        return generate_strategy(
            idea=request.idea,
            videos=videos,
            is_monopoly=is_monopoly,
            is_personality=is_personality,
            is_fragmented=is_fragmented,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"External API failure: {exc}") from exc
