import json
import time
import traceback
from typing import Any, List, Optional

from pydantic import BaseModel

from api_models import AgentContext
import llm_client
import llm_service


class TitleVariantItem(BaseModel):
    title: str
    psychology_tag: str  # Must be exactly: "CURIOSITY", "FEAR", or "ASPIRATION"


class StrategistAgentOutput(BaseModel):
    suggested_title: str
    title_psychology: str
    title_alternatives: List[TitleVariantItem]  # Exactly 2 items
    thumbnail_concept: str
    thumbnail_contrast_rule: str
    thumbnail_text_overlay: str
    exact_hook_script: str
    hook_psychology: str


def run_strategist_agent(
    context: AgentContext,
    analyst_output: dict,
    thumbnail_analysis: Optional[Any] = None,
) -> dict:
    print("[strategist] starting...")
    t0 = time.monotonic()

    system_prompt = (
        "Be a YouTube packaging strategist. Your job is to win the click before filming starts\n"
        "suggested_title: The single best most clickable title. One decisive recommendation. No hedging. Optimised for the content_archetype — if SEARCH_EVERGREEN lead with the exact search phrase, if VIRAL_REACH lead with an emotional trigger, if CORE_AUDIENCE lead with the specific value promise\n"
        "title_psychology: One sentence naming the SPECIFIC psychological trigger used — e.g. \"exploits the curiosity gap between 'one weekend' and the complexity implied\" — not generic descriptions like \"creates curiosity\"\n"
        "title_alternatives: Exactly 2 items. Each must have a psychology_tag that is EXACTLY one of: CURIOSITY, FEAR, ASPIRATION — no other values accepted\n"
        "thumbnail_concept: Specific enough that a creator can open Canva and execute in 10 minutes with zero creative decisions remaining. Include: what is shown, layout position, color mood, any text on the image, and what is deliberately excluded\n"
        "thumbnail_contrast_rule: Must directly reference the competitor thumbnails provided. State specifically what colors, composition, and visual elements to use BECAUSE they are absent from the current search results page thumbnails\n"
        "thumbnail_text_overlay: The exact words to overlay on the thumbnail. Maximum 4 words. If no overlay is recommended return an empty string — never say \"none\" or \"N/A\"\n"
        "exact_hook_script: The complete word-for-word script for the first 15 seconds. This is what the creator reads aloud. Not a description of what to say — the actual words. Should create immediate tension or curiosity\n"
        "hook_psychology: One sentence explaining why THESE specific words create tension — must reference the actual hook content directly not generically\n"
        "Base tone on content_archetype from analyst: CORE_AUDIENCE = authoritative educational tone, VIRAL_REACH = emotional dramatic tone, SEARCH_EVERGREEN = direct practical tone\n"
        "No generic YouTube advice. Everything must be specific to this exact video idea and competitor landscape"
    )

    creator_dna = context.request.creator_dna
    user_prompt = (
        "VIDEO IDEA:\n"
        f"{context.request.video_idea}\n\n"
        "CREATOR DNA:\n"
        f"{creator_dna if creator_dna is not None else 'Not provided'}\n\n"
        "COMPETITOR THUMBNAILS — USE THESE TO WRITE CONTRAST RULE:\n"
        f"{json.dumps(context.competitors.thumbnails, indent=2)}\n\n"
        "COMPETITOR COMMENTS:\n"
        f"{context.competitors.top_comments}\n\n"
        "ANALYST INTELLIGENCE:\n"
        f"{json.dumps(analyst_output, indent=2)}\n"
    )

    # Append thumbnail visual analysis if available
    if thumbnail_analysis is not None:
        from thumbnail_analyzer import thumbnail_analysis_to_prompt_block

        thumbnail_block = thumbnail_analysis_to_prompt_block(thumbnail_analysis)
        user_prompt += f"\n\n{thumbnail_block}\n"
        user_prompt += (
            "\nIMPORTANT: The thumbnail visual analysis above shows what competitor "
            "thumbnails ACTUALLY look like. Your thumbnail_contrast_rule MUST reference "
            "these specific visual details — not generic advice. "
            "Your thumbnail_concept must deliberately avoid the dominant pattern described above.\n"
        )

    try:
        structured_llm = llm_client.get_structured_llm(StrategistAgentOutput, temperature=0.7, timeout_s=90)
        result_obj = structured_llm.invoke(
            [("system", system_prompt), ("human", user_prompt)]
        )
        result = result_obj.model_dump()
    except Exception:
        traceback.print_exc()
        result = StrategistAgentOutput(
            suggested_title="Insufficient data",
            title_psychology="Insufficient data",
            title_alternatives=[],
            thumbnail_concept="Insufficient data",
            thumbnail_contrast_rule="Insufficient data",
            thumbnail_text_overlay="",
            exact_hook_script="Insufficient data",
            hook_psychology="Insufficient data",
        ).model_dump()

    print({"stage": "strategist", "output": result})
    print(f"[strategist] done in {time.monotonic() - t0:.1f}s")
    return result

