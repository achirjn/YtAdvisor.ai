import json
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import List, Optional

import llm_client
from pydantic import BaseModel


class _DNAGenerationOutput(BaseModel):
    dna_summary: str
    audience_age_range: str
    preferred_format: str
    recurring_questions: List[str]
    content_complaints: List[str]
    engagement_tone: str


@dataclass
class CreatorDNASnapshot:
    channel_id: str
    channel_title: str

    # The living summary — this is what gets injected into AgentContext.creator_dna
    dna_summary: str

    # Tracking fields
    videos_processed: int = 0
    total_comments_analysed: int = 0
    last_updated_timestamp: float = 0.0  # Unix timestamp

    # Structured fields extracted from the summary for easy access
    audience_age_range: str = ""  # e.g. "25-35"
    preferred_format: str = ""  # e.g. "fast-paced tutorials under 15 minutes"
    recurring_questions: List[str] = field(default_factory=list)  # top 3-5 question themes
    content_complaints: List[str] = field(default_factory=list)  # top 3 recurring complaints
    engagement_tone: str = ""  # e.g. "highly technical, low emotion"

    # Whether this snapshot has enough data to be useful
    is_reliable: bool = False  # True only after >= 50 comments processed


@dataclass
class DNAUpdateResult:
    success: bool
    updated_snapshot: Optional[CreatorDNASnapshot] = None
    comments_processed: int = 0
    error_message: str = ""


def _build_generation_prompt(
    channel_title: str,
    comment_texts: List[str],
    existing_summary: Optional[str] = None,
) -> str:
    truncated = [c[:200] for c in comment_texts if c.strip()][:300]
    comments_block = "\n".join(f"- {c}" for c in truncated)

    base = (
        f"You are analysing the YouTube audience of the channel: '{channel_title}'.\n\n"
        f"Here are {len(truncated)} audience comments from this channel's videos:\n\n"
        f"{comments_block}\n\n"
    )

    if existing_summary:
        base += (
            "An existing audience summary already exists from previous analysis:\n\n"
            f"EXISTING SUMMARY:\n{existing_summary}\n\n"
            "Your task: UPDATE and ENRICH the existing summary with insights from "
            "the new comments above. Do not discard existing insights — only add, "
            "refine, or correct them based on the new data.\n\n"
        )
    else:
        base += (
            "Your task: Analyse these comments and produce a fresh audience summary.\n\n"
        )

    base += (
        "Produce a JSON object with exactly these fields:\n"
        "- dna_summary: A compressed natural-language paragraph (max 400 words) describing "
        "this creator's audience. Write it as if briefing an AI content strategist. "
        "Include: typical viewer age range, preferred content format and length, "
        "recurring topics they want more of, recurring complaints or gaps, "
        "and their engagement tone. Be specific — avoid generic statements.\n"
        "- audience_age_range: A string like '25-35' or '18-24' — best estimate from comment language and references.\n"
        "- preferred_format: One sentence describing the content format this audience prefers.\n"
        "- recurring_questions: A JSON array of exactly 3-5 strings. Each is a specific question theme "
        "this audience repeatedly asks. Derive from actual comment patterns.\n"
        "- content_complaints: A JSON array of exactly 3 strings. Each is a specific complaint "
        "or gap this audience repeatedly expresses. Derive from actual comment patterns.\n"
        "- engagement_tone: One sentence describing how this audience communicates — "
        "e.g. 'highly technical, uses industry jargon, low emotional content'.\n\n"
        "Return ONLY the JSON object. No explanation outside the JSON."
    )

    return base


def _generate_dna_with_gemini(
    channel_title: str,
    comment_texts: List[str],
    existing_summary: Optional[str],
) -> Optional[_DNAGenerationOutput]:
    """
    Calls Gemini to generate or update the creator DNA summary.
    Returns None if the call fails.
    """
    system_prompt = (
        "You are an expert YouTube audience analyst. "
        "You analyse viewer comments to extract precise, actionable insights "
        "about a creator's audience. "
        "You always return valid JSON matching the requested schema exactly. "
        "You never make generic observations — every insight must be grounded "
        "in the actual comment data provided."
    )

    user_prompt = _build_generation_prompt(channel_title, comment_texts, existing_summary)

    try:
        structured_llm = llm_client.get_structured_llm(_DNAGenerationOutput, temperature=0.3)
        result = structured_llm.invoke([
            ("system", system_prompt),
            ("human", user_prompt),
        ])
        return result
    except Exception as e:
        print(f"[dna_service] Gemini call failed: {e}")
        traceback.print_exc()
        return None


def create_dna_snapshot(
    channel_id: str,
    channel_title: str,
    comment_texts: List[str],
    videos_processed: int,
) -> DNAUpdateResult:
    """
    Creates a brand-new CreatorDNASnapshot from a list of comment texts.
    Used during Phase 1 bootstrapping when no existing snapshot exists.
    Returns DNAUpdateResult with success status and the new snapshot.
    """
    print(
        f"[dna_service] creating fresh DNA for '{channel_title}' "
        f"from {len(comment_texts)} comments..."
    )

    if len(comment_texts) == 0:
        return DNAUpdateResult(
            success=False,
            error_message="No comment texts provided — cannot generate DNA.",
        )

    t0 = time.monotonic()
    result = _generate_dna_with_gemini(
        channel_title=channel_title,
        comment_texts=comment_texts,
        existing_summary=None,
    )

    if result is None:
        return DNAUpdateResult(
            success=False,
            error_message="Gemini DNA generation failed.",
        )

    snapshot = CreatorDNASnapshot(
        channel_id=channel_id,
        channel_title=channel_title,
        dna_summary=result.dna_summary,
        videos_processed=videos_processed,
        total_comments_analysed=len(comment_texts),
        last_updated_timestamp=time.time(),
        audience_age_range=result.audience_age_range,
        preferred_format=result.preferred_format,
        recurring_questions=result.recurring_questions,
        content_complaints=result.content_complaints,
        engagement_tone=result.engagement_tone,
        is_reliable=len(comment_texts) >= 50,
    )

    print(
        f"[dna_service] fresh DNA created in {time.monotonic() - t0:.1f}s — "
        f"reliable={snapshot.is_reliable}"
    )
    return DNAUpdateResult(
        success=True,
        updated_snapshot=snapshot,
        comments_processed=len(comment_texts),
    )


def update_dna_snapshot(
    existing_snapshot: CreatorDNASnapshot,
    new_comment_texts: List[str],
    additional_videos_processed: int,
) -> DNAUpdateResult:
    """
    Enriches an existing CreatorDNASnapshot with new comment data.
    Used during Phase 2 background enrichment batches.
    The existing summary is preserved and enriched — never discarded.
    Returns DNAUpdateResult with the updated snapshot.
    """
    print(
        f"[dna_service] updating DNA for '{existing_snapshot.channel_title}' "
        f"with {len(new_comment_texts)} new comments "
        f"(was {existing_snapshot.total_comments_analysed} total)..."
    )

    if len(new_comment_texts) == 0:
        print("[dna_service] no new comments — returning existing snapshot unchanged")
        return DNAUpdateResult(
            success=True,
            updated_snapshot=existing_snapshot,
            comments_processed=0,
        )

    t0 = time.monotonic()
    result = _generate_dna_with_gemini(
        channel_title=existing_snapshot.channel_title,
        comment_texts=new_comment_texts,
        existing_summary=existing_snapshot.dna_summary,
    )

    if result is None:
        return DNAUpdateResult(
            success=False,
            error_message="Gemini DNA update failed — existing snapshot preserved.",
            updated_snapshot=existing_snapshot,
        )

    new_total_comments = existing_snapshot.total_comments_analysed + len(new_comment_texts)
    new_videos_processed = existing_snapshot.videos_processed + additional_videos_processed

    updated = CreatorDNASnapshot(
        channel_id=existing_snapshot.channel_id,
        channel_title=existing_snapshot.channel_title,
        dna_summary=result.dna_summary,
        videos_processed=new_videos_processed,
        total_comments_analysed=new_total_comments,
        last_updated_timestamp=time.time(),
        audience_age_range=result.audience_age_range,
        preferred_format=result.preferred_format,
        recurring_questions=result.recurring_questions,
        content_complaints=result.content_complaints,
        engagement_tone=result.engagement_tone,
        is_reliable=new_total_comments >= 50,
    )

    print(
        f"[dna_service] DNA updated in {time.monotonic() - t0:.1f}s — "
        f"total_comments={new_total_comments}, reliable={updated.is_reliable}"
    )
    return DNAUpdateResult(
        success=True,
        updated_snapshot=updated,
        comments_processed=len(new_comment_texts),
    )


def snapshot_to_creator_dna_string(snapshot: CreatorDNASnapshot) -> str:
    """
    Converts a CreatorDNASnapshot into the creator_dna string format
    expected by AgentContext.request.creator_dna.

    If the snapshot is not yet reliable (< 50 comments), appends a note
    so agents know to weight it accordingly.

    This is the bridge between Pipeline 2 and the agent pipeline.
    """
    if not snapshot.dna_summary:
        return "Audience data not yet available."

    reliability_note = (
        ""
        if snapshot.is_reliable
        else (
            f"\n\n[Note: This audience summary is based on only "
            f"{snapshot.total_comments_analysed} comments from "
            f"{snapshot.videos_processed} videos — treat with moderate confidence "
            f"until more data is collected.]"
        )
    )

    structured_addendum = ""
    if snapshot.recurring_questions:
        questions = "; ".join(snapshot.recurring_questions[:3])
        structured_addendum += f"\nTop audience questions: {questions}."
    if snapshot.content_complaints:
        complaints = "; ".join(snapshot.content_complaints[:3])
        structured_addendum += f"\nRecurring complaints: {complaints}."

    return (
        f"{snapshot.dna_summary}"
        f"{structured_addendum}"
        f"{reliability_note}"
    )


def snapshot_to_dict(snapshot: CreatorDNASnapshot) -> dict:
    """Serialises a CreatorDNASnapshot to a plain dict for JSON storage."""
    return {
        "channel_id": snapshot.channel_id,
        "channel_title": snapshot.channel_title,
        "dna_summary": snapshot.dna_summary,
        "videos_processed": snapshot.videos_processed,
        "total_comments_analysed": snapshot.total_comments_analysed,
        "last_updated_timestamp": snapshot.last_updated_timestamp,
        "audience_age_range": snapshot.audience_age_range,
        "preferred_format": snapshot.preferred_format,
        "recurring_questions": snapshot.recurring_questions,
        "content_complaints": snapshot.content_complaints,
        "engagement_tone": snapshot.engagement_tone,
        "is_reliable": snapshot.is_reliable,
    }


def snapshot_from_dict(data: dict) -> CreatorDNASnapshot:
    """Deserialises a CreatorDNASnapshot from a plain dict loaded from JSON storage."""
    return CreatorDNASnapshot(
        channel_id=data.get("channel_id", ""),
        channel_title=data.get("channel_title", ""),
        dna_summary=data.get("dna_summary", ""),
        videos_processed=data.get("videos_processed", 0),
        total_comments_analysed=data.get("total_comments_analysed", 0),
        last_updated_timestamp=data.get("last_updated_timestamp", 0.0),
        audience_age_range=data.get("audience_age_range", ""),
        preferred_format=data.get("preferred_format", ""),
        recurring_questions=data.get("recurring_questions", []),
        content_complaints=data.get("content_complaints", []),
        engagement_tone=data.get("engagement_tone", ""),
        is_reliable=data.get("is_reliable", False),
    )


if __name__ == "__main__":
    import os

    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not gemini_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    test_comments = [
        "Could you show how to add authentication to this?",
        "Great tutorial but you skipped the deployment part completely",
        "Please do a video on Docker and Kubernetes next",
        "The explanation of the database schema was too fast",
        "I've been following your channel for 2 years, best dev content on YouTube",
        "Can you show how to test this with Jest?",
        "This is exactly what I needed for my job interview prep",
        "Would love to see a video on microservices architecture",
        "You always skip error handling, please cover that",
        "I'm a junior developer and this was really helpful",
        "The code is great but the audio quality could be better",
        "Please cover TypeScript in your next video",
        "I've tried 10 other tutorials and yours is the clearest",
        "Can you explain the difference between REST and GraphQL?",
        "More backend content please, too many frontend tutorials out there",
        "The pace is perfect, not too slow not too fast",
        "I always learn something new from your videos even as a senior dev",
        "You should cover CI/CD pipelines next",
        "Skipped over the environment variables setup, confusing for beginners",
        "Could you do a full project from scratch series?",
        "Best explanation of async/await I've seen",
        "Please add timestamps to your videos",
        "I follow you and two other devs, you're all teaching different things which is good",
        "The code examples are realistic, not toy projects",
        "Would love AWS or GCP tutorials",
        "You should explain WHY not just HOW",
        "Perfect length, I watch during lunch break",
        "Finally someone who doesn't use Todo apps as examples",
        "Can you cover Redis caching next?",
        "The debugging section saved me hours at work",
    ]

    print(f"[test] creating fresh DNA from {len(test_comments)} simulated comments...")
    result1 = create_dna_snapshot(
        channel_id="UC_test_channel",
        channel_title="Test Dev Channel",
        comment_texts=test_comments,
        videos_processed=5,
    )

    print(f"\n[test] create_dna_snapshot result:")
    print(f"  success: {result1.success}")
    print(f"  comments_processed: {result1.comments_processed}")
    print(f"  error_message: {result1.error_message}")

    if result1.success and result1.updated_snapshot:
        snap = result1.updated_snapshot
        print(f"\n  channel_id: {snap.channel_id}")
        print(f"  videos_processed: {snap.videos_processed}")
        print(f"  total_comments_analysed: {snap.total_comments_analysed}")
        print(f"  is_reliable: {snap.is_reliable}")
        print(f"  audience_age_range: {snap.audience_age_range}")
        print(f"  preferred_format: {snap.preferred_format}")
        print(f"  engagement_tone: {snap.engagement_tone}")
        print(f"  recurring_questions: {snap.recurring_questions}")
        print(f"  content_complaints: {snap.content_complaints}")
        print(f"\n  dna_summary (first 300 chars):")
        print(f"  {snap.dna_summary[:300]}")

        new_comments = [
            "Please cover system design interviews",
            "Would love a video on PostgreSQL optimization",
            "Your explanations of complex topics are so clear",
            "Missing section on security best practices",
            "Can you do a live coding session?",
        ]

        print(f"\n[test] updating DNA with {len(new_comments)} new comments...")
        result2 = update_dna_snapshot(
            existing_snapshot=snap,
            new_comment_texts=new_comments,
            additional_videos_processed=2,
        )

        print(f"\n[test] update_dna_snapshot result:")
        print(f"  success: {result2.success}")
        print(f"  comments_processed: {result2.comments_processed}")

        if result2.success and result2.updated_snapshot:
            updated = result2.updated_snapshot
            print(
                f"  total_comments_analysed after update: {updated.total_comments_analysed}"
            )
            print(f"  videos_processed after update: {updated.videos_processed}")

        print(f"\n[test] testing serialisation round-trip...")
        snap_dict = snapshot_to_dict(snap)
        restored = snapshot_from_dict(snap_dict)
        assert restored.channel_id == snap.channel_id
        assert restored.dna_summary == snap.dna_summary
        assert restored.recurring_questions == snap.recurring_questions
        print(f"  serialisation round-trip: PASSED")

        print(f"\n[test] agent-ready DNA string (first 400 chars):")
        agent_str = snapshot_to_creator_dna_string(snap)
        print(agent_str[:400])
