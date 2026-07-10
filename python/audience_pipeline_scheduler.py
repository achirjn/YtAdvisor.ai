import os
import sys
import threading
import time
import traceback
from enum import Enum
from typing import Dict, Optional

# Import components from audience_pipeline_graph
from audience_pipeline_graph import get_pipeline_app, ENRICHMENT_INTERVAL_HOURS
from channel_scraper import scrape_channel

# Export PipelinePhase enum matching main.py imports
class PipelinePhase(str, Enum):
    BOOTSTRAPPING = "BOOTSTRAPPING"
    ENRICHING = "ENRICHING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"

# Global locking mechanism to fix race conditions in _running_channels
_running_channels_lock = threading.Lock()
_running_channels: Dict[str, bool] = {}


def _get_status_from_graph(channel_id: str) -> Optional[dict]:
    config = {"configurable": {"thread_id": channel_id}}
    state_snapshot = get_pipeline_app().get_state(config)
    if not state_snapshot or not state_snapshot.values:
        return None

    values = state_snapshot.values
    phase_str = values.get("phase", "BOOTSTRAPPING")
    phase = PipelinePhase(phase_str)

    # Gate dna_summary: visible only during ENRICHING or COMPLETE
    dna_summary = None
    if phase_str in ("ENRICHING", "COMPLETE"):
        dna_summary = values.get("dna_summary")

    with _running_channels_lock:
        is_running = _running_channels.get(channel_id, False)

    return {
        "channel_id": values.get("channel_id", ""),
        "channel_title": values.get("channel_title", ""),
        "phase": phase,
        "videos_processed": values.get("videos_processed", 0),
        "total_videos_on_channel": values.get("total_videos_on_channel", 0),
        "is_reliable": values.get("is_reliable", False),
        "last_error": values.get("last_error", ""),
        "dna_summary": dna_summary,
        "is_running": is_running,
    }


def _scheduler_thread_worker(channel_id: str, youtube_api_key: str) -> None:
    print(f"[scheduler] background thread worker started for '{channel_id}'")
    config = {"configurable": {"thread_id": channel_id}}

    try:
        while True:
            # 1. Fetch current checkpoint values
            state_snapshot = get_pipeline_app().get_state(config)
            if not state_snapshot or not state_snapshot.values:
                print(f"[scheduler] ERROR: no state found for {channel_id} — worker exiting")
                break

            values = state_snapshot.values
            phase = values.get("phase", "BOOTSTRAPPING")

            if phase in ("COMPLETE", "FAILED"):
                print(f"[scheduler] channel {channel_id} has finished in phase {phase}")
                break

            # 2. Timing check if in ENRICHING phase
            if phase == "ENRICHING":
                last_run = values.get("last_run_timestamp", 0.0)
                next_run = values.get("next_run_timestamp", 0.0)
                now = time.time()

                if last_run > 0 and now < next_run:
                    wait_seconds = next_run - now
                    print(f"[scheduler] next enrichment batch for {channel_id} in {wait_seconds/3600:.2f}h — sleeping...")
                    time.sleep(min(wait_seconds, 3600))
                    continue

            # 3. Trigger exactly ONE invocation to process one unit of work
            print(f"[scheduler] invoking pipeline graph for {channel_id} (current phase: {phase})...")
            try:
                result = get_pipeline_app().invoke(None, config)
                new_phase = result.get("phase")
                print(f"[scheduler] invocation completed. New phase: {new_phase}")
                if new_phase in ("COMPLETE", "FAILED"):
                    break
            except Exception as e:
                print(f"[scheduler] ERROR: Graph invocation failed for {channel_id}: {str(e)}")
                traceback.print_exc()
                # Recoverable sleep before trying again
                time.sleep(60)

    except Exception as e:
        print(f"[scheduler] worker thread crashed for {channel_id}")
        traceback.print_exc()
    finally:
        with _running_channels_lock:
            _running_channels[channel_id] = False
        print(f"[scheduler] thread finished for channel {channel_id}")


def start_pipeline(channel_input: str, youtube_api_key: str) -> Optional[object]:
    """
    Spawns or resumes the background thread scheduler for the channel.
    Guarded by a thread lock to prevent concurrent execution races.
    """
    try:
        raw = (channel_input or "").strip()
        is_bare_channel_id = raw.startswith("UC") and " " not in raw

        channel_id = raw
        channel_title = ""
        if not is_bare_channel_id:
            sr = scrape_channel(raw, youtube_api_key, max_videos=1)
            if sr.scrape_successful and sr.channel_id:
                channel_id = sr.channel_id
                channel_title = sr.channel_title

        if not channel_title:
            channel_title = channel_id

        config = {"configurable": {"thread_id": channel_id}}

        with _running_channels_lock:
            # Check if a thread is already active for this channel
            if _running_channels.get(channel_id) is True:
                # Thread is running, load and return current checkpoint state
                status = _get_status_from_graph(channel_id)
                if status:
                    return type('Struct', (object,), status)()

            _running_channels[channel_id] = True

        # Check existing checkpoint
        state_snapshot = get_pipeline_app().get_state(config)
        values = state_snapshot.values if state_snapshot else {}
        phase = values.get("phase")

        if not phase or phase in ("COMPLETE", "FAILED"):
            # Initialize or reset state in the checkpointer
            initial_state = {
                "channel_id": channel_id,
                "channel_title": channel_title,
                "youtube_api_key": youtube_api_key,
                "phase": "BOOTSTRAPPING",
                "is_reliable": False,
                "total_videos_on_channel": 0,
                "videos_processed": 0,
                "current_batch_index": 0,
                "last_run_timestamp": 0.0,
                "next_run_timestamp": 0.0,
                "consecutive_failures": 0,
                "last_error": "",
                "dna_summary": "",
                "total_comments_analysed": 0,
                "audience_age_range": "",
                "preferred_format": "",
                "recurring_questions": [],
                "content_complaints": [],
                "engagement_tone": "",
            }
            get_pipeline_app().update_state(config, initial_state)
        else:
            # Keep api key updated
            get_pipeline_app().update_state(config, {"youtube_api_key": youtube_api_key})

        # Start background daemon thread
        thread = threading.Thread(
            target=_scheduler_thread_worker,
            args=(channel_id, youtube_api_key),
            daemon=True,
            name=f"audience-pipeline-scheduler-{channel_id}",
        )
        thread.start()

        status = _get_status_from_graph(channel_id)
        if status:
            return type('Struct', (object,), status)()

    except Exception:
        traceback.print_exc()
        
    fallback = {
        "channel_id": "",
        "channel_title": "",
        "phase": PipelinePhase.FAILED,
        "videos_processed": 0,
        "total_videos_on_channel": 0,
        "is_reliable": False,
        "last_error": "start_pipeline failed",
        "dna_summary": None,
        "is_running": False,
    }
    return type('Struct', (object,), fallback)()


def get_pipeline_status(channel_id: str) -> Optional[object]:
    """
    Returns the current state object expected by main.py
    """
    status = _get_status_from_graph(channel_id)
    if status is None:
        return None
    return type('Struct', (object,), status)()


def get_pipeline_dna_string(channel_id: str) -> Optional[str]:
    """
    Compiles the snapshot fields in state into creator DNA string format
    """
    config = {"configurable": {"thread_id": channel_id}}
    state_snapshot = get_pipeline_app().get_state(config)
    if not state_snapshot or not state_snapshot.values:
        return None

    values = state_snapshot.values
    if not values.get("dna_summary"):
        return None

    from creator_dna_service import CreatorDNASnapshot, snapshot_to_creator_dna_string
    snap = CreatorDNASnapshot(
        channel_id=values.get("channel_id"),
        channel_title=values.get("channel_title"),
        dna_summary=values.get("dna_summary"),
        videos_processed=values.get("videos_processed", 0),
        total_comments_analysed=values.get("total_comments_analysed", 0),
        last_updated_timestamp=values.get("last_run_timestamp", 0.0),
        audience_age_range=values.get("audience_age_range", ""),
        preferred_format=values.get("preferred_format", ""),
        recurring_questions=values.get("recurring_questions", []),
        content_complaints=values.get("content_complaints", []),
        engagement_tone=values.get("engagement_tone", ""),
        is_reliable=values.get("is_reliable", False),
    )
    return snapshot_to_creator_dna_string(snap)


def start_pipeline_for_channel(
    channel_id: str,
    channel_title: str,
    youtube_api_key: str,
) -> bool:
    """
    Initializes and starts the audience pipeline for connected channel
    """
    config = {"configurable": {"thread_id": channel_id}}
    state_snapshot = get_pipeline_app().get_state(config)
    values = state_snapshot.values if state_snapshot else {}
    phase = values.get("phase")

    with _running_channels_lock:
        if _running_channels.get(channel_id) is True:
            return False

    if phase == "FAILED":
        # Reset failed state
        get_pipeline_app().update_state(config, {"phase": "BOOTSTRAPPING", "consecutive_failures": 0})
    elif not phase:
        initial_state = {
            "channel_id": channel_id,
            "channel_title": channel_title,
            "youtube_api_key": youtube_api_key,
            "phase": "BOOTSTRAPPING",
            "is_reliable": False,
            "total_videos_on_channel": 0,
            "videos_processed": 0,
            "current_batch_index": 0,
            "last_run_timestamp": 0.0,
            "next_run_timestamp": 0.0,
            "consecutive_failures": 0,
            "last_error": "",
            "dna_summary": "",
            "total_comments_analysed": 0,
            "audience_age_range": "",
            "preferred_format": "",
            "recurring_questions": [],
            "content_complaints": [],
            "engagement_tone": "",
        }
        get_pipeline_app().update_state(config, initial_state)

    with _running_channels_lock:
        _running_channels[channel_id] = True

    thread = threading.Thread(
        target=_scheduler_thread_worker,
        args=(channel_id, youtube_api_key),
        daemon=True,
        name=f"audience-pipeline-scheduler-{channel_id}",
    )
    thread.start()
    return True


def get_creator_dna_for_channel(channel_id: str) -> Optional[str]:
    return get_pipeline_dna_string(channel_id)


def run_single_enrichment_now(
    channel_id: str,
    youtube_api_key: str,
) -> bool:
    config = {"configurable": {"thread_id": channel_id}}
    state_snapshot = get_pipeline_app().get_state(config)
    if not state_snapshot or not state_snapshot.values:
        return False

    try:
        # Direct graph execution to run one enrichment batch immediately
        get_pipeline_app().invoke(None, config)
        return True
    except Exception:
        traceback.print_exc()
        return False
