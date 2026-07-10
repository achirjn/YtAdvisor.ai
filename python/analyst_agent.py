import json
import time
import traceback
from typing import Any, List, Optional

from pydantic import BaseModel

from api_models import AgentContext
import llm_client
import llm_service


class ContentGapItem(BaseModel):
    gap: str
    source: str


class AnalystAgentOutput(BaseModel):
    market_truth: str
    dominant_force: str
    competitor_weakness: str
    audience_craving: str
    content_gaps: List[ContentGapItem]  # Exactly 3 items
    small_creator_verdict: str  # Must be exactly: "CAN_WIN", "HARD", or "AVOID"
    small_creator_reason: str
    algorithm_signal: str
    satisfaction_risk: int  # 1-10
    content_archetype: str  # Must be exactly: "CORE_AUDIENCE", "VIRAL_REACH", or "SEARCH_EVERGREEN"
    channel_strength: str
    channel_risk: str


def run_analyst_agent(
    context: AgentContext,
    graph_signals: Optional[Any] = None,
    median_subscriber_count: Optional[int] = None,
) -> dict:
    print("[analyst] starting...")
    t0 = time.monotonic()

    system_prompt = (
        "You are a YouTube market analyst. Output ONLY a single valid JSON "
        "object with EXACTLY these keys — no extra keys, no missing keys:\n"
        "market_truth, dominant_force, competitor_weakness, audience_craving, "
        "content_gaps, small_creator_verdict, small_creator_reason, "
        "algorithm_signal, satisfaction_risk, content_archetype, "
        "channel_strength, channel_risk\n\n"
        "FIELD RULES:\n"
        "market_truth: One bold sentence stating what this market actually "
        "rewards right now. Under 20 words.\n"
        "dominant_force: One sentence — who wins here and the single specific "
        "structural reason why. Under 20 words.\n"
        "competitor_weakness: The specific structural failure of the top "
        "competing video. Under 20 words. Derive from top_comments.\n"
        "audience_craving: One sentence from comment patterns only — what "
        "viewers are begging for that nobody delivers. Under 20 words. Must "
        "reference the actual comments provided.\n"
        "content_gaps: JSON array of EXACTLY 3 objects, each with keys 'gap' "
        "and 'source'. Each gap must be derived STRICTLY from the provided "
        "top_comments. The source field must say where the gap was found e.g. "
        "'Repeated in 3 competitor comments' or 'Top upvoted complaint'.\n"
        "small_creator_verdict: MUST be exactly one of these three strings: "
        "'CAN_WIN', 'HARD', or 'AVOID'. "
        "If median competitor subscriber count is above 500000 use 'AVOID'. "
        "If 100000 to 500000 use 'HARD'. Below 100000 use 'CAN_WIN'.\n"
        "small_creator_reason: One sentence explaining the small_creator_verdict.\n"
        "algorithm_signal: One specific sentence about how this content type "
        "will interact with the YouTube algorithm based on competitor patterns.\n"
        "satisfaction_risk: Integer 1-10. Measures the gap between what the "
        "title promises and what can realistically be delivered.\n"
        "content_archetype: MUST be exactly one of these three strings: "
        "'CORE_AUDIENCE', 'VIRAL_REACH', or 'SEARCH_EVERGREEN'.\n"
        "channel_strength: If creator_dna is provided, one sentence explaining "
        "how that creator's style is a strategic weapon in this market. If no "
        "creator_dna provided, output exactly: "
        "'Provide creator DNA for personalised analysis'\n"
        "channel_risk: If creator_dna is provided, one sentence explaining what "
        "in their style works against them in this market. If no creator_dna "
        "provided, output exactly: "
        "'Provide creator DNA for personalised analysis'\n\n"
        "CRITICAL RULES:\n"
        "1. Output ONLY the JSON object. No markdown, no code fences, no "
        "explanation before or after.\n"
        "2. Every single one of the 12 keys listed above MUST be present.\n"
        "3. If data is insufficient for a field output the string "
        "'Insufficient data' as the value — never omit the key.\n"
        "4. content_gaps MUST always be an array of exactly 3 objects.\n"
        "5. satisfaction_risk MUST always be an integer, never a string.\n"
        "6. small_creator_verdict MUST be exactly 'CAN_WIN', 'HARD', or "
        "'AVOID' — no other value is acceptable.\n"
        "7. content_archetype MUST be exactly 'CORE_AUDIENCE', 'VIRAL_REACH', "
        "or 'SEARCH_EVERGREEN' — no other value is acceptable."
    )

    creator_dna = context.request.creator_dna
    user_prompt = (
        "VIDEO IDEA:\n"
        f"{context.request.video_idea}\n\n"
        "CREATOR DNA:\n"
        f"{creator_dna if creator_dna is not None else 'Not provided'}\n\n"
        "COMPETITOR THUMBNAILS:\n"
        f"{json.dumps(context.competitors.thumbnails, indent=2)}\n\n"
        "COMPETITOR COMMENTS — PRIMARY DATA SOURCE FOR GAPS:\n"
        f"{context.competitors.top_comments[:6000]}\n"
    )

    # Append graph signals if available
    if graph_signals is not None:
        user_prompt += (
            "\n\nMARKET GRAPH SIGNALS (derived from real YouTube data):\n"
            f"- Market structure: {getattr(graph_signals, 'market_structure_summary', 'Not available')}\n"
            f"- Entry opportunity: {getattr(graph_signals, 'entry_opportunity_summary', 'Not available')}\n"
            f"- Small creator opportunity: {getattr(graph_signals, 'small_creator_opportunity', 'Not available')}\n"
            f"- Monopoly detected: {getattr(graph_signals, 'is_monopoly', getattr(graph_signals, 'monopoly_detected', 'Not available'))}\n"
            f"- Breakout concentration: {getattr(graph_signals, 'breakout_concentration', 'Not available')}\n"
            f"- Analyst narrative: {getattr(graph_signals, 'analyst_narrative', getattr(graph_signals, 'analyst_summary', 'Not available'))}\n"
            "Treat these signals as ground truth from real data.\n"
        )

    # Append median subscriber count if available
    if median_subscriber_count is not None and median_subscriber_count > 0:
        user_prompt += (
            f"\nMEDIAN COMPETITOR SUBSCRIBER COUNT: {median_subscriber_count:,}\n"
            "Use this to determine small_creator_verdict:\n"
            "- Above 500,000 → AVOID\n"
            "- 100,000 to 500,000 → HARD\n"
            "- Below 100,000 → CAN_WIN\n"
            "This is real data from the YouTube API — do not override it with assumptions.\n"
        )

    try:
        structured_llm = llm_client.get_structured_llm(AnalystAgentOutput, temperature=0.7, timeout_s=240)
        result_obj = structured_llm.invoke(
            [("system", system_prompt), ("human", user_prompt)]
        )
        result = result_obj.model_dump()
    except Exception:
        traceback.print_exc()
        result = AnalystAgentOutput(
            market_truth="Insufficient data",
            dominant_force="Insufficient data",
            competitor_weakness="Insufficient data",
            audience_craving="Insufficient data",
            content_gaps=[ContentGapItem(gap="Insufficient data", source="Analysis failed")],
            small_creator_verdict="HARD",
            small_creator_reason="Insufficient data",
            algorithm_signal="Insufficient data",
            satisfaction_risk=5,
            content_archetype="CORE_AUDIENCE",
            channel_strength="Insufficient data",
            channel_risk="Insufficient data",
        ).model_dump()

    print({"stage": "analyst", "output": result})
    print(f"[analyst] done in {time.monotonic() - t0:.1f}s")
    return result
