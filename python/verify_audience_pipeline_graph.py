import os
import sys
import time
import shutil
import psycopg
import traceback
from dotenv import load_dotenv

# Ensure python directory is in path
sys.path.append(os.path.dirname(__file__))

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
youtube_key = os.getenv("YOUTUBE_API_KEY")
db_url = os.getenv("DATABASE_URL")

if not youtube_key:
    print("ERROR: YOUTUBE_API_KEY must be set in .env to run verification.")
    sys.exit(1)

if not db_url:
    print("ERROR: DATABASE_URL must be set in .env to run Postgres checkpointer verification.")
    sys.exit(1)

import audience_pipeline_graph
import audience_pipeline_scheduler

# Force low caps for quick execution
TEST_CHANNEL_ID = "UCsBjURrPoezykLs9EqgamOA" # Fireship
TEST_CHANNEL_TITLE = "Fireship"

audience_pipeline_graph.MAX_VIDEOS_CAP = 2
audience_pipeline_graph.BOOTSTRAP_VIDEO_COUNT = 1
audience_pipeline_graph.ENRICHMENT_BATCH_SIZE = 1


def clean_state():
    print(f"[verify] Cleaning up test state records from Neon for thread_id '{TEST_CHANNEL_ID}'...")
    # Prune Postgres tables
    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.checkpoints')")
                exists = cur.fetchone()[0]
                if exists:
                    cur.execute("DELETE FROM checkpoints WHERE thread_id = %s", (TEST_CHANNEL_ID,))
                    cur.execute("DELETE FROM checkpoint_blobs WHERE thread_id = %s", (TEST_CHANNEL_ID,))
                    cur.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (TEST_CHANNEL_ID,))
                    print("  Successfully pruned Neon Postgres checkpoint rows.")
                else:
                    print("  Checkpoint tables do not exist yet (setup() will create them on first app launch).")
            conn.commit()
    except Exception as e:
        print(f"  Error pruning Postgres tables: {str(e)}")


def test_new_pipeline_status():
    print("\n--- Running New LangGraph Postgres Pipeline ---")
    start_res = audience_pipeline_scheduler.start_pipeline(TEST_CHANNEL_ID, youtube_key)
    print(f"New start_pipeline phase: {start_res.phase}")

    status = None
    # Poll status until finished
    for _ in range(30):
        time.sleep(2)
        status = audience_pipeline_scheduler.get_pipeline_status(TEST_CHANNEL_ID)
        print(f"  Polling status: phase={status.phase if status else None}, processed={status.videos_processed if status else None}")
        if status and status.phase in ("COMPLETE", "FAILED"):
            break

    print(f"New Pipeline Final Status Object: {status}")
    return status


def verify_schema_format(status):
    print("\n--- Checking Status Object Schema Keys and Types ---")
    if not status:
        print("FAILED: Status object is missing.")
        sys.exit(1)

    expected_keys = [
        "channel_id", "channel_title", "phase", "videos_processed",
        "total_videos_on_channel", "is_reliable", "last_error", "dna_summary"
    ]

    for key in expected_keys:
        if not hasattr(status, key):
            print(f"FAILED: Status missing expected property '{key}'")
            sys.exit(1)

    print("SUCCESS: Status object format and keys are correct!")


def verify_db_rows():
    print("\n--- Direct Database Query Verification ---")
    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT thread_id, checkpoint_id, parent_checkpoint_id FROM checkpoints WHERE thread_id = %s", (TEST_CHANNEL_ID,))
                rows = cur.fetchall()
                print(f"Found {len(rows)} checkpointer rows in Neon's 'checkpoints' table:")
                for r in rows:
                    print(f"  thread_id: {r[0]} | checkpoint_id: {r[1]} | parent: {r[2]}")
                
                assert len(rows) > 0, "No checkpoint rows found in the database!"
                print("SUCCESS: Direct Neon query confirmed checkpoint rows exist in actual database tables.")
    except Exception as e:
        print(f"FAILED: Direct database verification failed: {str(e)}")
        sys.exit(1)


def test_resumption_logic():
    print("\n--- Testing Resumption Logic (Neon Postgres Checkpointing) ---")
    clean_state()

    config = {"configurable": {"thread_id": TEST_CHANNEL_ID}}
    app = audience_pipeline_graph.get_pipeline_app()

    # 1. Initialize to BOOTSTRAPPING
    initial_state = {
        "channel_id": TEST_CHANNEL_ID,
        "channel_title": TEST_CHANNEL_TITLE,
        "youtube_api_key": youtube_key,
        "phase": "BOOTSTRAPPING",
        "videos_processed": 0,
        "current_batch_index": 0,
    }
    app.update_state(config, initial_state)
    print("Graph initialized to BOOTSTRAPPING phase.")

    # 2. Invoke once -> executes bootstrap_node -> transitions phase to ENRICHING
    print("Executing first invoke (Bootstrap Node)...")
    res = app.invoke(None, config)
    print(f"  Result phase: {res.get('phase')}")
    print(f"  Result current_batch_index: {res.get('current_batch_index')}")
    assert res.get("phase") == "ENRICHING", "Phase should transition to ENRICHING after bootstrap"
    assert res.get("current_batch_index") == 0, "Batch index should be 0 after bootstrap"

    # 3. Invoke second time -> executes enrich_batch_node (batch index 0) -> increments batch index to 1
    print("Executing second invoke (Enrichment Batch Index 0)...")
    res = app.invoke(None, config)
    print(f"  Result phase: {res.get('phase')}")
    print(f"  Result current_batch_index (BEFORE restart): {res.get('current_batch_index')}")
    assert res.get("current_batch_index") == 1, "Batch index should increment to 1"

    # 4. Simulate process restart by reloading state from checkpoint DB
    print("Simulating process restart (re-fetching state from Neon Postgres)...")
    
    audience_pipeline_graph._pipeline_app = None
    new_app = audience_pipeline_graph.get_pipeline_app()
    
    state_snap = new_app.get_state(config)
    reloaded_values = state_snap.values
    print(f"  Reloaded phase: {reloaded_values.get('phase')}")
    print(f"  Reloaded current_batch_index (ON reload): {reloaded_values.get('current_batch_index')}")
    assert reloaded_values.get("current_batch_index") == 1, "Reloaded batch index should be 1"

    # 5. Invoke third time -> executes enrich_batch_node (batch index 1) -> increments batch index to 2
    print("Executing third invoke (Resuming from batch index 1)...")
    res = new_app.invoke(None, config)
    print(f"  Result phase: {res.get('phase')}")
    print(f"  Result current_batch_index (AFTER resumption): {res.get('current_batch_index')}")
    assert res.get("current_batch_index") == 2, "Batch index should increment to 2, proving resumption works!"
    
    print("SUCCESS: Postgres checkpointer resumption verification passed!")


if __name__ == "__main__":
    try:
        clean_state()
        new_status = test_new_pipeline_status()
        
        verify_schema_format(new_status)
        verify_db_rows()
        test_resumption_logic()
        
        print("\nALL BACKGROUND STATE MACHINE MIGRATION VERIFICATIONS PASSED!")
    except Exception as e:
        print("\nFAILED: Verification script crashed!")
        traceback.print_exc()
        sys.exit(1)
