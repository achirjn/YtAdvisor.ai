from __future__ import annotations

import json
import time
import traceback
from typing import List, Optional

import google.generativeai as genai
from pydantic import BaseModel, Field

from creator_profile import DerivedCreatorProfile
import llm_service


class StrategistAgentOutput(BaseModel):
    positioning: str
    content_angle: str
    idea_upgrade: str
    differentiation_strategy: str
    gap_exploited: str
    next_video_ideas: List[str]
    reasoning: str


def run_strategist_agent(
    idea: str,
    analyst_output: dict,
    creator_profile: Optional[DerivedCreatorProfile],
    content_mode: str = "SEARCH",
) -> dict:
    print("[strategist] starting...")
    t0 = time.monotonic()

    creator_mode = "generic"
    channel_size_bucket = "small"
    competition_tolerance = "low"
    growth_stage = "early"
    performance_ratio = 0.0

    if creator_profile is not None:
        creator_mode = creator_profile.mode
        channel_size_bucket = creator_profile.channel_size_bucket
        competition_tolerance = creator_profile.competition_tolerance
        growth_stage = creator_profile.growth_stage
        performance_ratio = creator_profile.performance_ratio

    if creator_mode == "generic":
        system_prompt = (
            "You are a general YouTube content strategist.\n\n"
            "Your job is to turn market insights into winning video angles for a general audience.\n\n"
            "STRICT RULES:\n"
            "* Your strategy MUST exploit at least one content gap from the analysis.\n"
            "* If you do not use a content gap, your strategy is INVALID.\n"
            "* next_video_ideas must follow a progression (beginner → deeper → viral).\n\n"
            "STRICT FORMATTING RULE: Do not write essays. Use simple words. Maximum 15 words per sentence. "
            "No academic jargon. Direct, punchy facts."
        )
        user_prompt = (
            "Idea:\n"
            f"{idea}\n\n"
            "Analyst Insights:\n"
            f"* Market Truth: {analyst_output.get('market_truth')}\n"
            f"* Dominant Force: {analyst_output.get('dominant_force')}\n"
            f"* Opportunity: {analyst_output.get('opportunity')}\n"
            f"* Risk: {analyst_output.get('risk')}\n"
            f"* Content Gaps: {analyst_output.get('content_gaps')}\n"
            f"* Can Win: {analyst_output.get('can_small_creator_win')}\n"
            f"* Reasoning: {analyst_output.get('reasoning')}\n"
        )
    else:
        # Dynamically build context to handle empty frontend fields safely
        context_parts = [
            f"* Channel Size: {channel_size_bucket}",
            f"* Growth Stage: {growth_stage}",
            f"* Performance Ratio: {performance_ratio}",
            f"* Competition Tolerance: {competition_tolerance}"
        ]
        if creator_profile and creator_profile.strengths:
            context_parts.append(f"* Strengths: {', '.join(creator_profile.strengths)}")
        if creator_profile and creator_profile.weaknesses:
            context_parts.append(f"* Weaknesses: {', '.join(creator_profile.weaknesses)}")
        if creator_profile and creator_profile.interests:
            context_parts.append(f"* Interests: {', '.join(creator_profile.interests)}")
        if creator_profile and creator_profile.recent_videos:
            past_vids_str = json.dumps([v.model_dump() for v in creator_profile.recent_videos])
            context_parts.append(f"* Past Video Performance: {past_vids_str}")
            
        dynamic_creator_context = "\n".join(context_parts)

        system_prompt = (
            "You are a private YouTube strategist for a specific channel.\n\n"
            "Your job is to figure out how THIS specific channel can pivot to beat larger competitors based on their explicit skills, past videos, and the content mode.\n\n"
            "CRITICAL STRATEGY RULES BASED ON CONTENT MODE:\n"
            "1. If content_mode is 'SEARCH' (Tutorials, Tech, Finance): Competition is bad. Niche down. Find the specific gap big channels ignored. Solve a specific problem.\n"
            "2. If content_mode is 'BROWSE' (Vlogs, Food, Challenges, Entertainment): Competition is GOOD. It means high demand. Do NOT niche down. Instead, maximize the emotional hook, pacing, and visual curiosity. Beat them with better angles, not smaller niches.\n\n"
            "STRICT RULES:\n"
            "* Your strategy MUST exploit at least one content gap from the analysis.\n"
            "* Focus heavily on differentiation based on their channel size.\n"
            "* next_video_ideas must be safe and scalable for their current growth stage.\n\n"
            "STRICT FORMATTING RULE: Do not write essays. Use simple words. Maximum 15 words per sentence. "
            "No academic jargon. Direct, punchy facts."
        )
        user_prompt = (
            f"Idea:\n{idea}\n"
            f"Content Mode: {content_mode}\n\n"
            "Analyst Insights:\n"
            f"* Market Truth: {analyst_output.get('market_truth')}\n"
            f"* Dominant Force: {analyst_output.get('dominant_force')}\n"
            f"* Opportunity: {analyst_output.get('opportunity')}\n"
            f"* Risk: {analyst_output.get('risk')}\n"
            f"* Content Gaps: {analyst_output.get('content_gaps')}\n"
            f"* Can Win: {analyst_output.get('can_small_creator_win')}\n"
            f"* Reasoning: {analyst_output.get('reasoning')}\n\n"
            "Creator Context:\n"
            f"{dynamic_creator_context}\n\n"
            "Apply these creator constraints to your strategy."
        )

    model = genai.GenerativeModel(
        llm_service._MODEL_NAME,
        system_instruction=system_prompt,
    )
    try:
        response = llm_service.generate_content_with_timeout(
            model,
            user_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.8,
                response_mime_type="application/json",
                response_schema=StrategistAgentOutput,
            ),
            timeout_s=45,
        )
    except Exception:
        traceback.print_exc()
        result = {
            "positioning": "N/A",
            "content_angle": "N/A",
            "idea_upgrade": "N/A",
            "differentiation_strategy": "N/A",
            "gap_exploited": "Unknown",
            "next_video_ideas": [],
            "reasoning": "LLM request timed out or failed.",
        }
        print({
            "stage": "strategist",
            "idea": idea,
            "output": result,
        })
        print(f"[strategist] done in {time.monotonic() - t0:.1f}s")
        return result

    raw_text = response.text or ""

    try:
        parsed = llm_service._parse(raw_text, StrategistAgentOutput)
        result = parsed.model_dump()
    except Exception:
        traceback.print_exc()
        try:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            obj = json.loads(raw_text[start : end + 1])
            result = StrategistAgentOutput.model_validate(obj).model_dump()
        except Exception:
            traceback.print_exc()
            result = {
                "positioning": "N/A",
                "content_angle": "N/A",
                "idea_upgrade": "N/A",
                "differentiation_strategy": "N/A",
                "gap_exploited": "Unknown",
                "next_video_ideas": [],
                "reasoning": "LLM output could not be parsed reliably.",
            }

    print({
        "stage": "strategist",
        "idea": idea,
        "output": result
    })
    print(f"[strategist] done in {time.monotonic() - t0:.1f}s")
    return result

