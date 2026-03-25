from __future__ import annotations

import json
import time
import traceback
from typing import List, Optional

import google.generativeai as genai
from pydantic import BaseModel

from creator_profile import DerivedCreatorProfile
import llm_service


class FinalVerdict(BaseModel):
    decision: str  # "GO / MODIFY / AVOID"
    confidence: str  # "LOW / MEDIUM / HIGH"
    reason: str


class ExecutionPlan(BaseModel):
    title: str
    hook: str
    thumbnail_concept: str
    video_structure: List[str]


class PerformanceOutlook(BaseModel):
    potential: str  # "LOW / MEDIUM / HIGH"
    risk: str  # "LOW / MEDIUM / HIGH"
    reason: str


class OptimizerLLMOutput(BaseModel):
    executive_summary: str
    key_insight: str
    final_verdict: FinalVerdict
    execution_plan: ExecutionPlan
    next_moves: List[str]
    avoid: List[str]
    performance_outlook: PerformanceOutlook
    why_this_will_work: str


class OptimizerAgentOutput(OptimizerLLMOutput):
    gap_exploited: Optional[str] = None
    is_reliable: bool = True
    warning: Optional[str] = None


def run_optimizer_agent(
    idea: str,
    analyst_output: dict,
    strategist_output: dict,
    creator_profile: Optional[DerivedCreatorProfile],
    content_mode: str = "SEARCH",
) -> dict:
    print("[optimizer] starting...")
    t0 = time.monotonic()

    creator_mode = "generic"
    channel_size_bucket = "small"
    competition_tolerance = "low"
    growth_stage = "early"
    performance_ratio = 0.0
    subscriber_count = 0

    if creator_profile is not None:
        creator_mode = creator_profile.mode
        channel_size_bucket = creator_profile.channel_size_bucket
        competition_tolerance = creator_profile.competition_tolerance
        growth_stage = creator_profile.growth_stage
        performance_ratio = creator_profile.performance_ratio
        subscriber_count = creator_profile.subscriber_count or 0

    if creator_mode == "generic":
        system_prompt = (
            "You are a fast, decisive YouTube execution expert for the general market.\n\n"
            "Your job is to convert strategy into a clear action plan.\n\n"
            "DECISION AUTHORITY RULE:\n"
            "* You MUST make a clear decision in final_verdict.decision: GO / MODIFY / AVOID.\n"
            "* title must create curiosity and NOT be generic.\n"
            "* hook must create tension in the first sentence.\n"
            "* executive_summary must be exactly 1-2 punchy sentences.\n\n"
            "STRICT FORMATTING RULE: Do not write essays. Use simple words. Maximum 15 words per sentence. "
            "Never use academic jargon. Give direct, punchy, actionable facts. Keep titles under 60 characters."
        )
        user_prompt = (
            f"Idea:\n{idea}\n\n"
            "Analyst Output:\n"
            f"{json.dumps(analyst_output, indent=2)}\n\n"
            "Strategist Output:\n"
            f"{json.dumps(strategist_output, indent=2)}\n\n"
            "Evaluate the execution plan for a general audience."
        )
    else:
        context_parts = [
            f"* Subscriber Count: {subscriber_count}",
            f"* Performance Ratio: {performance_ratio}"
        ]
        if creator_profile.strengths:
            context_parts.append(f"* Strengths: {', '.join(creator_profile.strengths)}")
        if creator_profile.weaknesses:
            context_parts.append(f"* Weaknesses: {', '.join(creator_profile.weaknesses)}")
        if creator_profile.recent_videos:
            past_vids_str = json.dumps([v.model_dump() for v in creator_profile.recent_videos])
            context_parts.append(f"* Past Video Performance: {past_vids_str}")
            
        dynamic_creator_context = "\n".join(context_parts)

        system_prompt = (
            "You are an elite, ruthless YouTube growth hacker.\n\n"
            "Your goal is MAXIMAL UPSIDE. Safe videos get zero views. You must find the smartest way for this specific creator to take a big swing and win.\n\n"
            "THE VIRAL RULES:\n"
            "1. IDEA PRESERVATION: If the core idea has high viral or CTR potential, DO NOT kill it. Keep the core hook, but mutate the execution to fit the creator's skills.\n"
            "2. SMART RISK: Do not tell them to play it safe. Tell them how to take a smart risk. If they lack budget, use their strengths (like editing or scripting) to create the same viral feeling.\n"
            "3. RAW SUBS INTELLIGENCE: Look at their raw subscriber count. If they have 15 subs, focus on wild differentiation to break out. If they have 25,000 subs, focus on leveraging their existing authority. Never call a creator 'small'.\n"
            "4. FAMILIAR + TWIST: Do not force people into tiny, boring niches just to avoid competition. Take a massive, popular topic and add a weird, hyper-specific twist based on their profile.\n\n"
            "STRICT FORMATTING RULE: Do not write essays. Use simple words. Maximum 15 words per sentence. Give direct, punchy, actionable facts."
        )
        
        user_prompt = (
            f"Idea:\n{idea}\n"
            f"Content Mode: {content_mode}\n\n"
            "Analyst Output:\n"
            f"{json.dumps(analyst_output, indent=2)}\n\n"
            "Creator Context (CRITICAL):\n"
            f"{dynamic_creator_context}\n\n"
            "Build a high-upside execution plan. Do not play it safe. Maximize their chance to blow up."
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
                temperature=0.7,
                response_mime_type="application/json",
                response_schema=OptimizerLLMOutput,
            ),
            timeout_s=60,
        )
    except Exception:
        traceback.print_exc()
        result = {
            "executive_summary": "System overloaded. Please try again.",
            "key_insight": "Entry angle exists, but only if you differentiate hard from the default creator playbook.",
            "final_verdict": {
                "decision": "MODIFY",
                "confidence": "LOW",
                "reason": "LLM request timed out or failed.",
            },
            "execution_plan": {
                "title": "N/A",
                "hook": "N/A",
                "thumbnail_concept": "N/A",
                "video_structure": [],
            },
            "next_moves": [],
            "avoid": [],
            "performance_outlook": {
                "potential": "LOW",
                "risk": "MEDIUM",
                "reason": "No reliable execution guidance available.",
            },
            "why_this_will_work": "Unable to generate reliable execution plan due to timeout/failure.",
            "gap_exploited": strategist_output.get("gap_exploited") or "Unknown",
            "is_reliable": False,
            "warning": "Low confidence output. Retry recommended.",
        }
        print({
            "stage": "optimizer",
            "idea": idea,
            "output": result,
        })
        print(f"[optimizer] done in {time.monotonic() - t0:.1f}s")
        return result

    raw_text = response.text or ""

    parsed_successfully = False
    try:
        parsed = llm_service._parse(raw_text, OptimizerLLMOutput)
        result = parsed.model_dump()
        parsed_successfully = True
    except Exception:
        traceback.print_exc()
        try:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            obj = json.loads(raw_text[start : end + 1])
            result = OptimizerAgentOutput.model_validate(obj).model_dump()
            parsed_successfully = True
        except Exception:
            traceback.print_exc()
            result = {
                "executive_summary": "System parsing failed. Please try again.",
                "key_insight": "Entry angle exists, but only if you differentiate hard from the default creator playbook.",
                "final_verdict": {
                    "decision": "MODIFY",
                    "confidence": "LOW",
                    "reason": "LLM output could not be parsed reliably.",
                },
                "execution_plan": {
                    "title": "N/A",
                    "hook": "N/A",
                    "thumbnail_concept": "N/A",
                    "video_structure": [],
                },
                "next_moves": [],
                "avoid": [],
                "performance_outlook": {
                    "potential": "LOW",
                    "risk": "MEDIUM",
                    "reason": "No reliable execution guidance available.",
                },
                "why_this_will_work": "Unable to generate reliable execution plan due to parsing failure.",
                "gap_exploited": "Unknown",
                "is_reliable": False,
                "warning": "Low confidence output. Retry recommended.",
            }
    
    result["is_reliable"] = parsed_successfully
    
    # Manually copy the gap from the Strategist so it doesn't show as null
    result["gap_exploited"] = strategist_output.get("gap_exploited", "Unknown")
    
    if parsed_successfully:
        # Analyst override enforcement
        analyst_win = str(analyst_output.get("can_small_creator_win", {}).get("verdict", "")).upper()
        decision = str(result.get("final_verdict", {}).get("decision", "")).upper()
        
        if "NO" in analyst_win and decision == "GO":
            result["final_verdict"]["decision"] = "MODIFY"
            result["final_verdict"]["reason"] = "Adjusted because analyst flagged low feasibility."

    # Failure escalation system
    if not result.get("is_reliable", True):
        # Always default to MODIFY for unreliable outputs
        if "final_verdict" in result and "decision" in result["final_verdict"]:
            if result["final_verdict"]["decision"] == "GO":
                result["final_verdict"]["decision"] = "MODIFY"
                result["final_verdict"]["reason"] = "Low confidence output. Retry recommended."
        
        # Add warning for frontend
        result["warning"] = "Low confidence output. Retry recommended."

    print({
        "stage": "optimizer",
        "idea": idea,
        "output": result
    })
    print(f"[optimizer] done in {time.monotonic() - t0:.1f}s")
    return result

