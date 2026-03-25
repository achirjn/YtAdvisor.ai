import json
import time
import traceback
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from pydantic import BaseModel

from creator_profile import DerivedCreatorProfile
import llm_service


class CanSmallCreatorWin(BaseModel):
    verdict: str  # "YES / HARD / NO"
    confidence: str  # "LOW / MEDIUM / HIGH"


class AnalystAgentOutput(BaseModel):
    market_truth: str
    dominant_force: str
    opportunity: str
    risk: str
    content_gaps: List[str]
    can_small_creator_win: CanSmallCreatorWin
    reasoning: str


def run_analyst_agent(
    idea: str,
    features: dict,
    creator_profile: Optional[DerivedCreatorProfile],
    is_monopoly: bool = False,
    is_personality: bool = False,
    is_fragmented: bool = False,
    content_mode: str = "SEARCH",
) -> dict:
    print("[analyst] starting...")
    t0 = time.monotonic()

    creator_mode = "generic"
    subscriber_count = None
    channel_size_bucket = "small"
    growth_stage = "early"
    competition_tolerance = "low"
    performance_ratio = 0.0

    if creator_profile is not None:
        creator_mode = creator_profile.mode
        subscriber_count = creator_profile.subscriber_count
        channel_size_bucket = creator_profile.channel_size_bucket
        growth_stage = creator_profile.growth_stage
        competition_tolerance = creator_profile.competition_tolerance
        performance_ratio = creator_profile.performance_ratio

    # Add transcript sample if available
    transcript_sample = features.get("transcript_sample", "")

    breakout_summary = features.get("breakout_summary")
    creator_distribution = features.get("creator_distribution")
    title_patterns = features.get("title_patterns")
    content_clusters = features.get("content_clusters")
    freshness = features.get("freshness")
    velocity_metrics = features.get("velocity_metrics")
    market_summary = features.get("market_summary", {}) or {}
    entry_barrier = market_summary.get("entry_barrier")
    competition_level = market_summary.get("competition_level")

    if creator_mode == "generic":
        system_prompt = (
            "You are a YouTube market analyst evaluating ideas for a general audience.\n\n"
            "Your job is to:\n"
            "* Understand the competitive landscape\n"
            "* Identify real opportunities and risks\n\n"
            "STRICT RULES:\n"
            "* Do NOT generate titles or creative ideas\n"
            "* Do NOT give generic advice\n"
            "* Base your reasoning ONLY on provided data\n"
            "* market_truth must be 1-2 lines max\n"
            "* content_gaps must be specific\n\n"
            "STRICT FORMATTING RULE: Do not write essays. Use very simple words. Maximum 15 words per sentence. "
            "Never use academic jargon. Give direct, punchy, actionable facts."
        )
        user_prompt = (
            f"Idea:\n{idea}\n\n"
            "Market Signals:\n"
            f"* Breakout Summary: {breakout_summary}\n"
            f"* Creator Distribution: {creator_distribution}\n"
            f"* Title Patterns: {title_patterns}\n"
            f"* Content Clusters: {content_clusters}\n"
            f"* Freshness: {freshness}\n"
            f"* Velocity Metrics: {velocity_metrics}\n"
            f"* Consistency: {features.get('consistency')}\n"
            f"* Market Dynamics: {features.get('market_dynamics')}\n"
            f"* Anomaly Signals: MONOPOLY={is_monopoly}, PERSONALITY={is_personality}, FRAGMENTED={is_fragmented}\n\n"
            "TRANSCRIPT ANALYSIS:\n"
            f"- Hook Style: {features.get('transcript_analysis', {}).get('transcript_summary', {}).get('hook_style')}\n"
            f"- Pacing: {features.get('transcript_analysis', {}).get('transcript_summary', {}).get('pacing')}\n"
            f"- Tone: {features.get('transcript_analysis', {}).get('transcript_summary', {}).get('tone')}\n\n"
            "CRITICAL SIGNALS:\n"
            f"- Entry Barrier: {entry_barrier}\n"
            f"- Competition Level: {competition_level}\n\n"
            "Evaluate this idea purely on general market data."
        )
    else:
        # Dynamically build context to handle empty frontend fields safely
        context_parts = [
            f"* Channel Size: {channel_size_bucket} ({subscriber_count} subs)",
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
            "You are a private YouTube market analyst for a specific creator.\n\n"
            "Your job is to evaluate if the market is safe or hostile for THIS creator's size, based on their explicit skills, past videos, and the content mode.\n\n"
            "CRITICAL STRATEGY RULES BASED ON CONTENT MODE:\n"
            "1. If content_mode is 'SEARCH' (Tutorials, Tech, Finance): Competition is bad. Niche down. Find the specific gap big channels ignored. Solve a specific problem.\n"
            "2. If content_mode is 'BROWSE' (Vlogs, Food, Challenges, Entertainment): Competition is GOOD. It means high demand. Do NOT niche down. Instead, maximize the emotional hook, pacing, and visual curiosity. Beat them with better angles, not smaller niches.\n\n"
            "STRICT RULES:\n"
            "* Base your reasoning on the creator's channel size and competition tolerance.\n"
            "* market_truth must be 1-2 lines max\n"
            "* content_gaps must be specific\n\n"
            "STRICT FORMATTING RULE: Do not write essays. Use very simple words. Maximum 15 words per sentence. "
            "Never use academic jargon. Give direct, punchy, actionable facts."
        )
        user_prompt = (
            f"Idea:\n{idea}\n"
            f"Content Mode: {content_mode}\n\n"
            "Market Signals:\n"
            f"* Breakout Summary: {breakout_summary}\n"
            f"* Creator Distribution: {creator_distribution}\n"
            f"* Title Patterns: {title_patterns}\n"
            f"* Content Clusters: {content_clusters}\n"
            f"* Freshness: {freshness}\n"
            f"* Velocity Metrics: {velocity_metrics}\n"
            f"* Consistency: {features.get('consistency')}\n"
            f"* Market Dynamics: {features.get('market_dynamics')}\n"
            f"* Anomaly Signals: MONOPOLY={is_monopoly}, PERSONALITY={is_personality}, FRAGMENTED={is_fragmented}\n\n"
            "TRANSCRIPT ANALYSIS:\n"
            f"- Hook Style: {features.get('transcript_analysis', {}).get('transcript_summary', {}).get('hook_style')}\n"
            f"- Pacing: {features.get('transcript_analysis', {}).get('transcript_summary', {}).get('pacing')}\n"
            f"- Tone: {features.get('transcript_analysis', {}).get('transcript_summary', {}).get('tone')}\n\n"
            "CRITICAL SIGNALS:\n"
            f"- Entry Barrier: {entry_barrier}\n"
            f"- Competition Level: {competition_level}\n\n"
            "Creator Context:\n"
            f"{dynamic_creator_context}\n\n"
            "CREATOR PROFILE ADJUSTMENT RULES:\n"
            "- If performance_ratio is low (<0.1) → prioritize safer ideas\n"
            "- If channel_size_bucket is 'small' → focus on differentiation\n"
            "- If competition_tolerance is 'low' → avoid saturated markets\n"
            "Apply these rules to your analysis."
        )

    model = genai.GenerativeModel(
        llm_service._MODEL_NAME,  # reuse existing model name
        system_instruction=system_prompt,
    )
    try:
        response = llm_service.generate_content_with_timeout(
            model,
            user_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                response_mime_type="application/json",
                response_schema=AnalystAgentOutput,
            ),
            timeout_s=90,
        )
    except Exception:
        traceback.print_exc()
        result = {
            "market_truth": "Unknown",
            "dominant_force": "Unknown",
            "opportunity": "Insufficient signals to judge.",
            "risk": "Risk cannot be assessed.",
            "content_gaps": [],
            "can_small_creator_win": {"verdict": "HARD", "confidence": "LOW"},
            "reasoning": "LLM request timed out or failed.",
        }
        print({
            "stage": "analyst",
            "idea": idea,
            "output": result,
        })
        print(f"[analyst] done in {time.monotonic() - t0:.1f}s")
        return result

    raw_text = response.text or ""

    try:
        parsed = llm_service._parse(raw_text, AnalystAgentOutput)
        result = parsed.model_dump()
    except Exception:
        traceback.print_exc()
        # Fallback: attempt a simple JSON extraction; otherwise return safe defaults.
        try:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            obj = json.loads(raw_text[start : end + 1])
            result = AnalystAgentOutput.model_validate(obj).model_dump()
        except Exception:
            traceback.print_exc()
            result = {
                "market_truth": "Unknown",
                "dominant_force": "Unknown",
                "opportunity": "Insufficient signals to judge.",
                "risk": "Risk cannot be assessed.",
                "content_gaps": [],
                "can_small_creator_win": {"verdict": "HARD", "confidence": "LOW"},
                "reasoning": "LLM output could not be parsed reliably.",
            }

    print({
        "stage": "analyst",
        "idea": idea,
        "output": result
    })
    print(f"[analyst] done in {time.monotonic() - t0:.1f}s")
    return result

