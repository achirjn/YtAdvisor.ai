import os
import time
import threading
from typing import Any, Dict, List

from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import START, END, StateGraph

# Import scraper and service modules
from channel_scraper import (
    scrape_channel,
    get_bootstrap_videos,
    get_video_batch,
)
from audience_comment_scraper import (
    scrape_comments_for_videos,
    channel_videos_to_scrape_input,
)
from creator_dna_service import (
    create_dna_snapshot,
    update_dna_snapshot,
    CreatorDNASnapshot,
)
from audience_pipeline_state import AudiencePipelineState

# Configuration constants (matching legacy constants)
BOOTSTRAP_VIDEO_COUNT = 20
BOOTSTRAP_COMMENTS_PER_VIDEO = 30
ENRICHMENT_BATCH_SIZE = 10
ENRICHMENT_COMMENTS_PER_VIDEO = 50
ENRICHMENT_INTERVAL_HOURS = 6
MAX_VIDEOS_CAP = 500
RELIABILITY_THRESHOLD = 50

# Database setup in the existing pipeline_state directory
DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "pipeline_state",
)
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "audience_pipeline.sqlite")


# ── Graph Nodes ──────────────────────────────────────────────────────

def bootstrap_node(state: AudiencePipelineState) -> Dict[str, Any]:
    print(f"[pipeline-graph] starting BOOTSTRAP for '{state.get('channel_title')}'...")

    youtube_api_key = state.get("youtube_api_key")
    channel_id = state.get("channel_id")

    scrape_result = scrape_channel(
        channel_input=channel_id,
        youtube_api_key=youtube_api_key,
        max_videos=MAX_VIDEOS_CAP,
    )

    if not scrape_result.scrape_successful:
        last_error = f"Channel scrape failed: {scrape_result.error_message}"
        consecutive_failures = state.get("consecutive_failures", 0) + 1
        phase = "FAILED" if consecutive_failures >= 3 else "BOOTSTRAPPING"
        return {
            "last_error": last_error,
            "consecutive_failures": consecutive_failures,
            "phase": phase,
            "last_run_timestamp": time.time(),
        }

    bootstrap_videos = get_bootstrap_videos(scrape_result, count=BOOTSTRAP_VIDEO_COUNT)
    if not bootstrap_videos:
        consecutive_failures = state.get("consecutive_failures", 0) + 1
        return {
            "last_error": "No videos found for bootstrap",
            "consecutive_failures": consecutive_failures,
            "phase": "FAILED" if consecutive_failures >= 3 else "BOOTSTRAPPING",
            "total_videos_on_channel": scrape_result.total_video_count,
            "last_run_timestamp": time.time(),
        }

    scrape_input = channel_videos_to_scrape_input(bootstrap_videos)
    if not scrape_input:
        print("[pipeline-graph] bootstrap: no comments available — skipping DNA creation")
        return {
            "videos_processed": len(bootstrap_videos),
            "total_videos_on_channel": scrape_result.total_video_count,
            "phase": "ENRICHING",
            "current_batch_index": 0,
            "last_run_timestamp": time.time(),
            "next_run_timestamp": time.time() + (ENRICHMENT_INTERVAL_HOURS * 3600),
            "consecutive_failures": 0,
            "last_error": "",
        }

    comment_batch = scrape_comments_for_videos(
        scrape_input,
        max_comments_per_video=BOOTSTRAP_COMMENTS_PER_VIDEO,
        max_failures_before_abort=5,
    )

    if not comment_batch.batch_successful and comment_batch.total_comments == 0:
        last_error = f"Bootstrap comment scraping failed: {comment_batch.error_message}"
        consecutive_failures = state.get("consecutive_failures", 0) + 1
        phase = "FAILED" if consecutive_failures >= 3 else "BOOTSTRAPPING"
        return {
            "last_error": last_error,
            "consecutive_failures": consecutive_failures,
            "phase": phase,
            "total_videos_on_channel": scrape_result.total_video_count,
            "last_run_timestamp": time.time(),
        }

    dna_result = create_dna_snapshot(
        channel_id=channel_id,
        channel_title=state.get("channel_title"),
        comment_texts=comment_batch.all_comment_texts,
        videos_processed=len(bootstrap_videos),
    )

    if not dna_result.success or dna_result.updated_snapshot is None:
        last_error = f"Bootstrap DNA creation failed: {dna_result.error_message}"
        consecutive_failures = state.get("consecutive_failures", 0) + 1
        phase = "FAILED" if consecutive_failures >= 3 else "BOOTSTRAPPING"
        return {
            "last_error": last_error,
            "consecutive_failures": consecutive_failures,
            "phase": phase,
            "total_videos_on_channel": scrape_result.total_video_count,
            "last_run_timestamp": time.time(),
        }

    snap = dna_result.updated_snapshot
    return {
        "phase": "ENRICHING",
        "is_reliable": snap.is_reliable,
        "total_videos_on_channel": scrape_result.total_video_count,
        "videos_processed": len(bootstrap_videos),
        "current_batch_index": 0,
        "last_run_timestamp": time.time(),
        "next_run_timestamp": time.time() + (ENRICHMENT_INTERVAL_HOURS * 3600),
        "consecutive_failures": 0,
        "last_error": "",
        "dna_summary": snap.dna_summary,
        "total_comments_analysed": snap.total_comments_analysed,
        "audience_age_range": snap.audience_age_range,
        "preferred_format": snap.preferred_format,
        "recurring_questions": snap.recurring_questions,
        "content_complaints": snap.content_complaints,
        "engagement_tone": snap.engagement_tone,
    }


def enrich_batch_node(state: AudiencePipelineState) -> Dict[str, Any]:
    print(f"[pipeline-graph] starting ENRICHMENT batch {state.get('current_batch_index')} for '{state.get('channel_title')}'...")

    youtube_api_key = state.get("youtube_api_key")
    channel_id = state.get("channel_id")
    current_batch_index = state.get("current_batch_index", 0)
    videos_processed = state.get("videos_processed", 0)

    scrape_result = scrape_channel(
        channel_input=channel_id,
        youtube_api_key=youtube_api_key,
        max_videos=MAX_VIDEOS_CAP,
    )

    if not scrape_result.scrape_successful:
        last_error = f"Channel scrape failed: {scrape_result.error_message}"
        consecutive_failures = state.get("consecutive_failures", 0) + 1
        phase = "FAILED" if consecutive_failures >= 3 else "ENRICHING"
        return {
            "last_error": last_error,
            "consecutive_failures": consecutive_failures,
            "phase": phase,
            "last_run_timestamp": time.time(),
            "next_run_timestamp": time.time() + (ENRICHMENT_INTERVAL_HOURS * 3600),
        }

    batch_videos = get_video_batch(
        scrape_result,
        batch_index=current_batch_index,
        batch_size=ENRICHMENT_BATCH_SIZE,
    )

    if not batch_videos:
        print("[pipeline-graph] no more videos to process — marking as COMPLETE")
        return {
            "phase": "COMPLETE",
            "last_run_timestamp": time.time(),
        }

    scrape_input = channel_videos_to_scrape_input(batch_videos)
    if not scrape_input:
        print("[pipeline-graph] enrichment batch: no videos with comments — advancing batch index")
        new_batch_index = current_batch_index + 1
        new_processed = videos_processed + len(batch_videos)
        total_processable = min(scrape_result.videos_fetched, MAX_VIDEOS_CAP)
        phase = "COMPLETE" if new_processed >= total_processable else "ENRICHING"
        return {
            "current_batch_index": new_batch_index,
            "videos_processed": new_processed,
            "phase": phase,
            "last_run_timestamp": time.time(),
            "next_run_timestamp": time.time() + (ENRICHMENT_INTERVAL_HOURS * 3600),
            "consecutive_failures": 0,
            "last_error": "",
        }

    comment_batch = scrape_comments_for_videos(
        scrape_input,
        max_comments_per_video=ENRICHMENT_COMMENTS_PER_VIDEO,
        max_failures_before_abort=3,
    )

    existing_dna = None
    if state.get("dna_summary"):
        existing_dna = CreatorDNASnapshot(
            channel_id=channel_id,
            channel_title=state.get("channel_title"),
            dna_summary=state.get("dna_summary"),
            videos_processed=videos_processed,
            total_comments_analysed=state.get("total_comments_analysed", 0),
            audience_age_range=state.get("audience_age_range", ""),
            preferred_format=state.get("preferred_format", ""),
            recurring_questions=state.get("recurring_questions", []),
            content_complaints=state.get("content_complaints", []),
            engagement_tone=state.get("engagement_tone", ""),
            is_reliable=state.get("is_reliable", False),
        )

    if existing_dna is None:
        dna_result = create_dna_snapshot(
            channel_id=channel_id,
            channel_title=state.get("channel_title"),
            comment_texts=comment_batch.all_comment_texts,
            videos_processed=len(batch_videos),
        )
    else:
        dna_result = update_dna_snapshot(
            existing_snapshot=existing_dna,
            new_comment_texts=comment_batch.all_comment_texts,
            additional_videos_processed=len(batch_videos),
        )

    if not dna_result.success or dna_result.updated_snapshot is None:
        last_error = f"Enrichment DNA update failed: {dna_result.error_message}"
        consecutive_failures = state.get("consecutive_failures", 0) + 1
        phase = "FAILED" if consecutive_failures >= 3 else "ENRICHING"
        return {
            "last_error": last_error,
            "consecutive_failures": consecutive_failures,
            "phase": phase,
            "last_run_timestamp": time.time(),
            "next_run_timestamp": time.time() + (ENRICHMENT_INTERVAL_HOURS * 3600),
        }

    snap = dna_result.updated_snapshot
    new_batch_index = current_batch_index + 1
    new_processed = videos_processed + len(batch_videos)
    total_processable = min(scrape_result.videos_fetched, MAX_VIDEOS_CAP)
    phase = "COMPLETE" if new_processed >= total_processable else "ENRICHING"

    return {
        "phase": phase,
        "is_reliable": snap.is_reliable,
        "videos_processed": new_processed,
        "current_batch_index": new_batch_index,
        "last_run_timestamp": time.time(),
        "next_run_timestamp": time.time() + (ENRICHMENT_INTERVAL_HOURS * 3600),
        "consecutive_failures": 0,
        "last_error": "",
        "dna_summary": snap.dna_summary,
        "total_comments_analysed": snap.total_comments_analysed,
        "audience_age_range": snap.audience_age_range,
        "preferred_format": snap.preferred_format,
        "recurring_questions": snap.recurring_questions,
        "content_complaints": snap.content_complaints,
        "engagement_tone": snap.engagement_tone,
    }


# ── Edge Routing ──────────────────────────────────────────────────────

def route_start(state: AudiencePipelineState) -> str:
    phase = state.get("phase", "BOOTSTRAPPING")
    if phase == "BOOTSTRAPPING":
        return "bootstrap_node"
    elif phase == "ENRICHING":
        return "enrich_batch_node"
    else:
        return END


def route_bootstrap(state: AudiencePipelineState) -> str:
    phase = state.get("phase", "BOOTSTRAPPING")
    if phase == "ENRICHING":
        return "enrich_batch_node"
    else:
        return END


# ── Graph Construction ───────────────────────────────────────────────

workflow = StateGraph(AudiencePipelineState)

workflow.add_node("bootstrap_node", bootstrap_node)
workflow.add_node("enrich_batch_node", enrich_batch_node)

# Set conditional entry route
workflow.add_conditional_edges(START, route_start)

# Route bootstrap node outcomes
workflow.add_conditional_edges(
    "bootstrap_node",
    route_bootstrap,
    {
        "enrich_batch_node": "enrich_batch_node",
        END: END,
    }
)

# Enrich batch node is a single step that returns control to the caller
workflow.add_edge("enrich_batch_node", END)

# Thread-safe Postgres Checkpointer Setup with double-checked locking
_pipeline_app_lock = threading.Lock()
_pipeline_app = None

def get_pipeline_app():
    global _pipeline_app
    if _pipeline_app is None:
        with _pipeline_app_lock:
            if _pipeline_app is None:
                db_url = os.getenv("DATABASE_URL")
                if not db_url:
                    raise ValueError("DATABASE_URL environment variable is not set.")
                
                # Setup connection pool for Neon compatibility (disabling prepared statements)
                pool = ConnectionPool(
                    conninfo=db_url,
                    kwargs={
                        "autocommit": True,
                        "row_factory": dict_row,
                        "prepare_threshold": None
                    },
                    min_size=1,
                    max_size=10
                )
                
                checkpointer = PostgresSaver(pool)
                # Idempotently create checkpoint tables
                checkpointer.setup()
                _pipeline_app = workflow.compile(checkpointer=checkpointer)
    return _pipeline_app
