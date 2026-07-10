import json
import time
import traceback
from typing import List

from pydantic import BaseModel

from api_models import AgentContext
import llm_client
import llm_service


class RetentionTrapItem(BaseModel):
    moment: str
    reason: str
    fix: str


class NextVideoItem(BaseModel):
    title: str
    strategic_reason: str
    priority: int  # 1, 2, or 3


class OptimizerAgentOutput(BaseModel):
    final_verdict: str  # Must be exactly: "GO", "MODIFY", or "ABORT"
    confidence: str  # Must be exactly: "HIGH", "MEDIUM", or "LOW"
    confidence_reason: str
    idea_upgrade: str
    market_context: str
    performance_benchmark: str
    performance_outlook: str
    pacing_timeline: List[str]
    retention_traps: List[RetentionTrapItem]
    win_conditions: List[str]
    fail_conditions: List[str]
    shorts_test_recommended: bool
    shorts_test_instruction: str
    pinned_comment: str
    community_post_seed: str
    description_timestamps: str
    next_video_series: List[NextVideoItem]
    series_positioning: str


def run_optimizer_agent(
    context: AgentContext,
    analyst_output: dict,
    strategist_output: dict,
) -> dict:
    print("[optimizer] starting...")
    t0 = time.monotonic()

    system_prompt = (
        "VERDICT RULES:\n\n"
        "final_verdict must be EXACTLY one of: GO, MODIFY, ABORT. No punctuation. No other values. ABORT replaces AVOID — use ABORT when the market makes success structurally impossible for a small creator regardless of execution quality\n"
        "confidence must be EXACTLY one of: HIGH, MEDIUM, LOW\n"
        "confidence_reason: One sentence explaining why this confidence level — must reference specific signals from analyst data\n"
        "idea_upgrade: A specific reframing of the original idea that increases success probability. Must name the exact pivot e.g. \"Narrow from 'full stack deployment' to 'AWS RDS connection specifically' — the gap competitors left in comments\" — not generic improvement advice\n"
        "market_context: Exactly two sentences. First sentence: current state of this niche. Second sentence: what that means for timing right now\n"
        "performance_benchmark: A qualitative relative statement about expected performance — never use absolute view numbers. Examples: \"above channel average for this niche given low competitor quality\", \"below channel average — market too saturated for new entrants\", \"top performer potential if content gaps are filled\"\n"
        "performance_outlook: One sentence qualitative judgment on expected performance trajectory\n\n"
        "EXECUTION RULES:\n\n"
        "pacing_timeline: Minimum 5 items. Must start at 0:00. Strict format for every item: \"MM:SS - Section Title - retention instruction\". The retention instruction is the specific thing to do at that moment to keep viewers watching e.g. \"0:00 - Hook - show the end result first, then explain how\"\n"
        "retention_traps: Exactly 3 items. Each moment must describe when in THIS TYPE of video viewers typically drop off — inferred from comment complaints and content structure, not fabricated analytics data. Each fix must be concrete and actionable\n"
        "win_conditions: Exactly 3 items. Direct commands phrased as imperatives. Derived DIRECTLY from competitor top_comments and content_gaps — not generic YouTube advice\n"
        "fail_conditions: Exactly 3 items. Direct warnings. Also derived from competitor top_comments and content_gaps\n"
        "shorts_test_recommended: True if satisfaction_risk from analyst_output is 7 or higher, OR if small_creator_verdict from analyst_output is \"AVOID\" or \"HARD\"\n"
        "shorts_test_instruction: If True — exact description of what the Short should contain (first 60 seconds of the hook script), how long to run it before checking data (48-72 hours), and what metric to look at (retention past 50%). If False — empty string\n\n"
        "GROWTH RULES:\n\n"
        "pinned_comment: Exact text to paste — written to drive replies, reference the specific technical topics covered, and invite follow-up questions. Should feel like the creator wrote it not an AI\n"
        "community_post_seed: Exact text for Community Tab post 24 hours before upload — written to tease the specific insight, not the generic topic. Should end with a question to drive replies\n"
        "description_timestamps: Pre-written timestamp block derived directly from pacing_timeline. Format exactly as YouTube description timestamps — each line is \"MM:SS Title\"\n"
        "next_video_series: Exactly 3 items. Priority 1 is highest strategic importance. Each strategic_reason must explain the ALGORITHMIC connection — why the audience that watched this video will search for or click on that next video\n"
        "series_positioning: One sentence — how this video plus the 3 follow-ups establish the creator as the authority in a specific sub-niche within 30 days"
    )

    satisfaction_risk = analyst_output.get("satisfaction_risk")
    small_creator_verdict = analyst_output.get("small_creator_verdict")

    user_prompt = (
        "REQUEST AND COMPETITOR DATA:\n"
        f"{json.dumps(context.model_dump(), indent=2)}\n\n"
        "COMPETITOR COMMENTS — PRIMARY SOURCE OF TRUTH FOR WIN/FAIL CONDITIONS:\n"
        f"{context.competitors.top_comments}\n\n"
        "ANALYST OUTPUT:\n"
        f"{json.dumps(analyst_output, indent=2)}\n\n"
        "SATISFACTION RISK (used for shorts decision):\n"
        f"{satisfaction_risk}\n\n"
        "SMALL CREATOR VERDICT (used for shorts decision):\n"
        f"{small_creator_verdict}\n\n"
        "STRATEGIST OUTPUT:\n"
        f"{json.dumps(strategist_output, indent=2)}\n"
    )

    try:
        structured_llm = llm_client.get_structured_llm(OptimizerAgentOutput, temperature=0.7, timeout_s=90)
        result_obj = structured_llm.invoke(
            [("system", system_prompt), ("human", user_prompt)]
        )
        result = result_obj.model_dump()
    except Exception:
        traceback.print_exc()
        result = OptimizerAgentOutput(
            final_verdict="MODIFY",
            confidence="LOW",
            confidence_reason="Analysis failed — retry recommended",
            idea_upgrade="Insufficient data",
            market_context="Insufficient data",
            performance_benchmark="Insufficient data",
            performance_outlook="Insufficient data",
            pacing_timeline=["0:00 - Hook - open with the core value immediately"],
            retention_traps=[
                RetentionTrapItem(
                    moment="Insufficient data",
                    reason="Insufficient data",
                    fix="Insufficient data",
                )
            ],
            win_conditions=["Insufficient data"],
            fail_conditions=["Insufficient data"],
            shorts_test_recommended=True,
            shorts_test_instruction="",
            pinned_comment="Insufficient data",
            community_post_seed="Insufficient data",
            description_timestamps="Insufficient data",
            next_video_series=[
                NextVideoItem(
                    title="Insufficient data",
                    strategic_reason="Insufficient data",
                    priority=1,
                )
            ],
            series_positioning="Insufficient data",
        ).model_dump()

    print({"stage": "optimizer", "output": result})
    print(f"[optimizer] done in {time.monotonic() - t0:.1f}s")
    return result

