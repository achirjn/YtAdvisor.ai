import os
import sys
import time
import pprint
import traceback
from dotenv import load_dotenv

# Load env variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Ensure sys.path includes the python directory
sys.path.append(os.path.dirname(__file__))

try:
    from main import analyze_auto, AutoAnalyzeRequest
    from api_models import DimenziqAnalysisOutput
    print("SUCCESS: Imported all modules successfully!")
except Exception as e:
    print("FAILED: Import failed!")
    traceback.print_exc()
    sys.exit(1)


def run_verification():
    video_idea = "How to build a SaaS with Gemini 3.5 and FastAPI"
    creator_dna = "Pragmatic developer, loves fast coding, clear explanations."

    # Ensure api keys are set
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set in environment.")
        sys.exit(1)
    if not os.environ.get("YOUTUBE_API_KEY"):
        print("ERROR: YOUTUBE_API_KEY not set in environment.")
        sys.exit(1)

    print(f"\nTesting with Video Idea: '{video_idea}'")

    print("\n--- Running Live LangGraph Pipeline ---")
    t0 = time.monotonic()
    try:
        payload = AutoAnalyzeRequest(video_idea=video_idea, creator_dna=creator_dna)
        output = analyze_auto(payload)
        duration = time.monotonic() - t0
        print(f"Pipeline executed successfully in {duration:.1f}s")
    except Exception as e:
        print("FAILED: Live pipeline execution failed!")
        traceback.print_exc()
        sys.exit(1)

    # 1. Print output for visual confirmation
    print("\n[Pipeline Output Schema Presentation]")
    pprint.pprint(output.model_dump(), depth=3, compact=True)

    # 2. Assertions to verify real (non-fallback) output
    print("\n--- Verifying Output Integrity ---")
    try:
        assert isinstance(output, DimenziqAnalysisOutput), "Output is not an instance of DimenziqAnalysisOutput"
        
        # Verify key sections exist and are populated
        assert output.verdict is not None, "Verdict section is missing"
        assert output.market is not None, "Market section is missing"
        assert output.creative is not None, "Creative section is missing"
        assert output.execution is not None, "Execution section is missing"
        assert output.growth is not None, "Growth section is missing"

        # Check for non-fallback content values
        verdict = output.verdict
        print(f"  Verdict final_verdict: {verdict.final_verdict}")
        print(f"  Verdict confidence: {verdict.confidence}")
        verdict_value = verdict.final_verdict.value if hasattr(verdict.final_verdict, "value") else verdict.final_verdict
        assert verdict_value in ("GO", "NO_GO", "PIVOT", "MODIFY"), f"Invalid final verdict: {verdict_value}"
        assert len(verdict.confidence_reason.strip()) > 10, "Verdict confidence reason is too short or default"
        
        market = output.market
        print(f"  Market content archetype: {market.content_archetype}")
        assert len(market.dominant_force.strip()) > 5, "Market dominant force description is missing"
        assert len(market.content_gaps) > 0, "No content gaps were found by the analyst"
        
        creative = output.creative
        print(f"  Suggested title: {creative.suggested_title}")
        assert len(creative.suggested_title.strip()) > 5, "Suggested title is missing or default"
        assert len(creative.title_alternatives) > 0, "No title alternatives generated"
        
        execution = output.execution
        print(f"  Exact hook script: {execution.exact_hook_script[:60]}...")
        assert len(execution.exact_hook_script.strip()) > 10, "Exact hook script is missing"
        assert len(execution.retention_traps) > 0, "No retention traps identified"
        
        print("\nSUCCESS: All schema and non-fallback validation assertions passed!")
    except AssertionError as ae:
        print(f"FAILED: Output integrity assertion failed: {str(ae)}")
        sys.exit(1)

    print("\nSMOKE TEST COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    run_verification()
