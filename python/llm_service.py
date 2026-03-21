import json
import os
from typing import Any, List

import google.generativeai as genai
from pydantic import ValidationError

from .models import StrategyResponse, VideoData

_MODEL_NAME = "gemini-2.5-flash"
_QUERY_EXPANSION_SYSTEM_PROMPT = (
    "You are a YouTube SEO expert. Convert the user's raw video idea into exactly 3 "
    "highly optimized YouTube search queries that will find the closest competitor videos. "
    "Return ONLY a JSON array of 3 strings."
)


def configure_gemini(api_key: str) -> None:
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY in environment.")
    genai.configure(api_key=api_key)


def _configure_from_env() -> None:
    configure_gemini(os.environ.get("GEMINI_API_KEY", ""))


def _extract_json_array(raw_content: str) -> List[str]:
    content = raw_content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if "\n" in content:
            content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    array_start = content.find("[")
    array_end = content.rfind("]")
    if array_start == -1 or array_end == -1 or array_end < array_start:
        raise ValueError("LLM response did not contain a valid JSON array.")

    parsed = json.loads(content[array_start : array_end + 1])
    if not isinstance(parsed, list):
        raise ValueError("LLM query expansion output is not a list.")

    normalized = [str(item).strip() for item in parsed]
    if len(normalized) != 3 or any(not item for item in normalized):
        raise ValueError("LLM query expansion output must be exactly 3 non-empty strings.")
    return normalized


def _extract_json_object(raw_content: str) -> dict[str, Any]:
    content = raw_content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if "\n" in content:
            content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    object_start = content.find("{")
    object_end = content.rfind("}")
    if object_start == -1 or object_end == -1 or object_end < object_start:
        raise ValueError("LLM response did not contain a valid JSON object.")

    parsed = json.loads(content[object_start : object_end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("LLM strategy output is not a JSON object.")
    return parsed


def expand_idea_to_queries(idea: str) -> List[str]:
    _configure_from_env()
    model = genai.GenerativeModel(
        _MODEL_NAME,
        system_instruction=_QUERY_EXPANSION_SYSTEM_PROMPT,
    )
    response = model.generate_content(
        idea,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
        ),
    )
    content = response.text or "[]"
    return _extract_json_array(content)


def _build_video_summary(videos: List[VideoData]) -> str:
    summary = [
        {
            "video_id": video.video_id,
            "title": video.title,
            "view_count": video.view_count,
            "subscriber_count": video.subscriber_count,
            "age_days": video.age_days,
            "category_id": video.category_id,
            "transcript_excerpt": video.transcript[:300],
        }
        for video in videos
    ]
    return json.dumps(summary, ensure_ascii=False)


def generate_strategy(
    idea: str,
    videos: List[VideoData],
    is_monopoly: bool,
    is_personality: bool,
    is_fragmented: bool,
) -> StrategyResponse:
    _configure_from_env()

    # 1. Inject the Harsher Anomaly Overrides
    override_instructions: List[str] = []
    if is_monopoly:
        override_instructions.append(
            "SYSTEM OVERRIDE: IMPENETRABLE MONOPOLY DETECTED. Massive, old channels own this search term. "
            "Do not suggest generic 'better thumbnails'. You MUST force a radical micro-niche pivot "
            "(e.g., extreme budget, specific year constraint, bizarre twist) or tell them not to make it."
        )
    if is_personality:
        override_instructions.append(
            "SYSTEM OVERRIDE: PERSONALITY-DRIVEN VLOG NICHE DETECTED. Search Engine Optimization (SEO) is useless here. "
            "Tell the user their success relies 100% on their charisma, high-stakes storytelling, and rapid editing. "
            "Force the strategy to focus entirely on emotional stakes."
        )
    if is_fragmented:
        override_instructions.append(
            "SYSTEM OVERRIDE: FRANKENSTEIN IDEA DETECTED. This is a bizarre mashup with no established audience. "
            "Warn the user that nobody is searching for this combination. Your hook MUST focus on the sheer absurdity "
            "of the idea to create a curiosity gap."
        )

    # 2. The Ruthless Persona Base Prompt
    system_prompt = (
        "You are a ruthless, highly-paid YouTube strategist. Your job is to protect the creator from wasting time "
        "on dead trends, overly saturated markets, or bizarre ideas. DO NOT flatter the user. DO NOT be overly optimistic. "
        "Be brutally honest, highly critical, and entirely data-driven.\n\n"
        "CRITICAL RULES FOR EVALUATION:\n"
        "1. Check 'age_days' of the top videos. If the videos with the most views are over 1000 days old (e.g., 3+ years), "
        "THIS IS A DEAD TREND. You must score Demand as 'Low' and tell the user the trend is dead.\n"
        "2. If the market is too competitive, tell them they will fail unless they aggressively niche down.\n"
        "3. You MUST provide 2 to 3 'execution_risks'. These are the fatal pitfalls of the idea. "
        "Tell the creator exactly how they will ruin this video during production (e.g., 'If your pacing is too slow, "
        "retention will tank', or 'If you don't actually show the final product in the first 10 seconds, people will click off'). "
        "Make it sound like a strict warning.\n"
        "4. For the 'hook_rewrite', you MUST write a first-person, spoken-word script (1-2 sentences) that the creator will actually say to the camera. "
        "Do not give advice in this field; write the actual script."
        "5. Return output that strictly matches the required schema."
    )
    
    if override_instructions:
        system_prompt = f"{system_prompt}\n\n" + "\n".join(override_instructions)

    user_prompt = (
        f"Idea:\n{idea}\n\n"
        f"Competitor Video Summary (JSON):\n{_build_video_summary(videos)}"
    )

    model = genai.GenerativeModel(
        _MODEL_NAME,
        system_instruction=system_prompt,
    )
    
    response = model.generate_content(
        user_prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=StrategyResponse,
        ),
    )

    content = response.text or "{}"
    try:
        return StrategyResponse.model_validate_json(content)
    except ValidationError:
        return StrategyResponse.model_validate(_extract_json_object(content))
