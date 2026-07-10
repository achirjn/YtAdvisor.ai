import json
import traceback
from typing import Any, List
from pydantic import BaseModel
import llm_client

class QueryExpansionOutput(BaseModel):
    queries: List[str]

# -------------------------------
# QUERY EXPANSION
# -------------------------------
_QUERY_EXPANSION_SYSTEM_PROMPT = (
    "You are a YouTube SEO expert. Convert the user's raw video idea into exactly 3 "
    "highly optimized YouTube search queries."
)


def expand_idea_to_queries(idea: str) -> List[str]:
    try:
        structured_llm = llm_client.get_structured_llm(QueryExpansionOutput, temperature=0.7)
        res = structured_llm.invoke([
            ("system", _QUERY_EXPANSION_SYSTEM_PROMPT),
            ("human", f"Expand this video idea: '{idea}'")
        ])
        
        queries = res.queries
        normalized = [str(q).strip() for q in queries if str(q).strip()]
        return normalized[:3]
    except Exception as e:
        print(f"[llm_service] query expansion failed: {e}")
        traceback.print_exc()
        return []


# -------------------------------
# VIDEO SUMMARY
# -------------------------------
def _build_video_summary(videos: List[Any]) -> str:
    return json.dumps([
        {
            "title": v.title,
            "views": v.view_count,
            "subs": v.subscriber_count,
            "age": v.age_days,
            "breakout": v.breakout_multiplier,
        }
        for v in videos
    ])