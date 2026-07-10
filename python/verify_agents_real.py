import os
import sys
import traceback
import pprint
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables (such as GEMINI_API_KEY)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add the python directory of the workspace to sys.path so we can import the modules
sys.path.append(os.path.dirname(__file__))


try:
    from api_models import AgentContext, InitialRequest, CompetitorData
    import analyst_agent
    import strategist_agent
    import optimizer_agent
    import llm_client
    print("SUCCESS: Imported all modules successfully!")
except Exception as e:
    print("FAILED: Import failed!")
    traceback.print_exc()
    sys.exit(1)


def create_mock_context() -> AgentContext:
    return AgentContext(
        request=InitialRequest(
            video_idea="How to build a SaaS with Gemini 1.5 and FastAPI",
            creator_dna="Pragmatic developer, loves fast coding, clear explanations."
        ),
        competitors=CompetitorData(
            thumbnails=["thumb1.png", "thumb2.png"],
            top_comments="Amazing video! Learnt a lot. Could you show AWS RDS connection next? I got stuck there. The code on AWS was confusing."
        )
    )


def verify_analyst():
    print("\n--- Testing Analyst Agent (Fallback) ---")
    context = create_mock_context()
    
    # 1. Test fallback behavior by clearing the API key or injecting a bad API key
    original_key = os.environ.get("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = "INVALID_KEY_FOR_TESTING_FALLBACK"
    
    try:
        # Run agent
        result = analyst_agent.run_analyst_agent(
            context=context,
            graph_signals=None,
            median_subscriber_count=250000
        )
        
        # Verify schema keys
        expected_keys = set(analyst_agent.AnalystAgentOutput.model_fields.keys())
        actual_keys = set(result.keys())
        
        if expected_keys != actual_keys:
            print(f"FAILED: Analyst agent output keys do not match. Missing: {expected_keys - actual_keys}, Extra: {actual_keys - expected_keys}")
            sys.exit(1)
            
        # Verify specific expected default values in fallback
        assert result["market_truth"] == "Insufficient data"
        assert result["small_creator_verdict"] == "HARD"
        assert result["satisfaction_risk"] == 5
        print("SUCCESS: Analyst Agent fallback works correctly!")
        
    except Exception as e:
        print("FAILED: Analyst Agent fallback failed!")
        traceback.print_exc()
        sys.exit(1)
    finally:
        if original_key is not None:
            os.environ["GEMINI_API_KEY"] = original_key
        else:
            del os.environ["GEMINI_API_KEY"]


def verify_strategist():
    print("\n--- Testing Strategist Agent (Fallback) ---")
    context = create_mock_context()
    analyst_output = {
        "market_truth": "rewards quick setups",
        "dominant_force": "incumbents win",
        "competitor_weakness": "too slow in intro",
        "audience_craving": "fast setups",
        "content_gaps": [{"gap": "AWS RDS detail", "source": "Comments"}],
        "small_creator_verdict": "CAN_WIN",
        "small_creator_reason": "low subscriber counts overall",
        "algorithm_signal": "rewards high retention on start",
        "satisfaction_risk": 3,
        "content_archetype": "SEARCH_EVERGREEN",
        "channel_strength": "good experience",
        "channel_risk": "too theoretical"
    }
    
    # Test fallback behavior
    original_key = os.environ.get("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = "INVALID_KEY_FOR_TESTING_FALLBACK"
    
    try:
        result = strategist_agent.run_strategist_agent(
            context=context,
            analyst_output=analyst_output,
            thumbnail_analysis=None
        )
        
        expected_keys = set(strategist_agent.StrategistAgentOutput.model_fields.keys())
        actual_keys = set(result.keys())
        
        if expected_keys != actual_keys:
            print(f"FAILED: Strategist agent output keys do not match. Missing: {expected_keys - actual_keys}, Extra: {actual_keys - expected_keys}")
            sys.exit(1)
            
        assert result["suggested_title"] == "Insufficient data"
        assert result["title_alternatives"] == []
        print("SUCCESS: Strategist Agent fallback works correctly!")
        
    except Exception as e:
        print("FAILED: Strategist Agent fallback failed!")
        traceback.print_exc()
        sys.exit(1)
    finally:
        if original_key is not None:
            os.environ["GEMINI_API_KEY"] = original_key
        else:
            del os.environ["GEMINI_API_KEY"]


def verify_optimizer():
    print("\n--- Testing Optimizer Agent (Fallback) ---")
    context = create_mock_context()
    analyst_output = {
        "market_truth": "rewards quick setups",
        "dominant_force": "incumbents win",
        "competitor_weakness": "too slow in intro",
        "audience_craving": "fast setups",
        "content_gaps": [{"gap": "AWS RDS detail", "source": "Comments"}],
        "small_creator_verdict": "CAN_WIN",
        "small_creator_reason": "low subscriber counts overall",
        "algorithm_signal": "rewards high retention on start",
        "satisfaction_risk": 3,
        "content_archetype": "SEARCH_EVERGREEN",
        "channel_strength": "good experience",
        "channel_risk": "too theoretical"
    }
    strategist_output = {
        "suggested_title": "Fastest FastAPI + Gemini SaaS Boilerplate",
        "title_psychology": "direct search demand",
        "title_alternatives": [{"title": "Fastest API", "psychology_tag": "ASPIRATION"}],
        "thumbnail_concept": "Fast setup visual",
        "thumbnail_contrast_rule": "bright yellow contrast",
        "thumbnail_text_overlay": "Fast",
        "exact_hook_script": "Watch me build it.",
        "hook_psychology": "immediate action promise"
    }
    
    # Test fallback behavior
    original_key = os.environ.get("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = "INVALID_KEY_FOR_TESTING_FALLBACK"
    
    try:
        result = optimizer_agent.run_optimizer_agent(
            context=context,
            analyst_output=analyst_output,
            strategist_output=strategist_output
        )
        
        expected_keys = set(optimizer_agent.OptimizerAgentOutput.model_fields.keys())
        actual_keys = set(result.keys())
        
        if expected_keys != actual_keys:
            print(f"FAILED: Optimizer agent output keys do not match. Missing: {expected_keys - actual_keys}, Extra: {actual_keys - expected_keys}")
            sys.exit(1)
            
        assert result["final_verdict"] == "MODIFY"
        assert result["confidence"] == "LOW"
        assert result["retention_traps"][0]["moment"] == "Insufficient data"
        assert result["next_video_series"][0]["title"] == "Insufficient data"
        print("SUCCESS: Optimizer Agent fallback works correctly!")
        
    except Exception as e:
        print("FAILED: Optimizer Agent fallback failed!")
        traceback.print_exc()
        sys.exit(1)
    finally:
        if original_key is not None:
            os.environ["GEMINI_API_KEY"] = original_key
        else:
            del os.environ["GEMINI_API_KEY"]


def verify_real_calls():
    print("\n--- Testing Real API Calls ---")
    
    # Ensure GEMINI_API_KEY is present
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("FAILED: GEMINI_API_KEY is not set or loaded in the environment!")
        sys.exit(1)
    print(f"Using GEMINI_API_KEY: {api_key[:4]}...{api_key[-4:] if len(api_key) > 8 else ''}")
    
    context = create_mock_context()
    
    # 1. Analyst Agent real call
    print("\nCalling Analyst Agent (Real)...")
    try:
        analyst_result = analyst_agent.run_analyst_agent(
            context=context,
            graph_signals=None,
            median_subscriber_count=250000
        )
        
        print("\n[Analyst Agent Real Output]")
        pprint.pprint(analyst_result)
        
        # Verify schema keys
        expected_keys = set(analyst_agent.AnalystAgentOutput.model_fields.keys())
        actual_keys = set(analyst_result.keys())
        if expected_keys != actual_keys:
            print(f"FAILED: Analyst agent real output keys do not match. Missing: {expected_keys - actual_keys}, Extra: {actual_keys - expected_keys}")
            sys.exit(1)
            
        # Asserts:
        assert analyst_result["market_truth"] != "Insufficient data", "Analyst market_truth should not be 'Insufficient data'"
        assert analyst_result["small_creator_verdict"] in ("CAN_WIN", "HARD", "AVOID"), f"Analyst small_creator_verdict '{analyst_result['small_creator_verdict']}' not in ('CAN_WIN', 'HARD', 'AVOID')"
        assert len(analyst_result["content_gaps"]) >= 1, "Analyst content_gaps should have at least 1 item"
        for gap_item in analyst_result["content_gaps"]:
            # Since content_gaps elements are dicts after model_dump, we access by key
            assert gap_item.get("gap") != "Insufficient data", "Analyst content_gap should not be 'Insufficient data'"
        assert isinstance(analyst_result["satisfaction_risk"], int), f"Analyst satisfaction_risk {analyst_result['satisfaction_risk']} should be an int"
        
        print("SUCCESS: Analyst Agent real call checks passed!")
    except Exception as e:
        print("FAILED: Analyst Agent real call failed or check asserted false!")
        traceback.print_exc()
        sys.exit(1)
        
    # 2. Strategist Agent real call
    # Use the mock analyst output defined in verify_strategist()
    analyst_output = {
        "market_truth": "rewards quick setups",
        "dominant_force": "incumbents win",
        "competitor_weakness": "too slow in intro",
        "audience_craving": "fast setups",
        "content_gaps": [{"gap": "AWS RDS detail", "source": "Comments"}],
        "small_creator_verdict": "CAN_WIN",
        "small_creator_reason": "low subscriber counts overall",
        "algorithm_signal": "rewards high retention on start",
        "satisfaction_risk": 3,
        "content_archetype": "SEARCH_EVERGREEN",
        "channel_strength": "good experience",
        "channel_risk": "too theoretical"
    }
    
    print("\nCalling Strategist Agent (Real)...")
    try:
        strategist_result = strategist_agent.run_strategist_agent(
            context=context,
            analyst_output=analyst_output,
            thumbnail_analysis=None
        )
        
        print("\n[Strategist Agent Real Output]")
        pprint.pprint(strategist_result)
        
        # Verify schema keys
        expected_keys = set(strategist_agent.StrategistAgentOutput.model_fields.keys())
        actual_keys = set(strategist_result.keys())
        if expected_keys != actual_keys:
            print(f"FAILED: Strategist agent real output keys do not match. Missing: {expected_keys - actual_keys}, Extra: {actual_keys - expected_keys}")
            sys.exit(1)
            
        # Asserts:
        assert strategist_result["suggested_title"] != "Insufficient data", "Strategist suggested_title should not be 'Insufficient data'"
        assert strategist_result["title_psychology"] != "Insufficient data", "Strategist title_psychology should not be 'Insufficient data'"
        assert len(strategist_result["title_alternatives"]) >= 1, "Strategist title_alternatives should have at least 1 item"
        for variant in strategist_result["title_alternatives"]:
            assert variant.get("title") != "Insufficient data", "Strategist title alternative should not be 'Insufficient data'"
        
        print("SUCCESS: Strategist Agent real call checks passed!")
    except Exception as e:
        print("FAILED: Strategist Agent real call failed or check asserted false!")
        traceback.print_exc()
        sys.exit(1)
        
    # 3. Optimizer Agent real call
    # Use realistic analyst_output + strategist_output
    strategist_output = {
        "suggested_title": "Fastest FastAPI + Gemini SaaS Boilerplate",
        "title_psychology": "direct search demand",
        "title_alternatives": [{"title": "Fastest API", "psychology_tag": "ASPIRATION"}],
        "thumbnail_concept": "Fast setup visual",
        "thumbnail_contrast_rule": "bright yellow contrast",
        "thumbnail_text_overlay": "Fast",
        "exact_hook_script": "Watch me build it.",
        "hook_psychology": "immediate action promise"
    }
    
    print("\nCalling Optimizer Agent (Real)...")
    try:
        optimizer_result = optimizer_agent.run_optimizer_agent(
            context=context,
            analyst_output=analyst_output,
            strategist_output=strategist_output
        )
        
        print("\n[Optimizer Agent Real Output]")
        pprint.pprint(optimizer_result)
        
        # Verify schema keys
        expected_keys = set(optimizer_agent.OptimizerAgentOutput.model_fields.keys())
        actual_keys = set(optimizer_result.keys())
        if expected_keys != actual_keys:
            print(f"FAILED: Optimizer agent real output keys do not match. Missing: {expected_keys - actual_keys}, Extra: {actual_keys - expected_keys}")
            sys.exit(1)
            
        # Asserts:
        assert optimizer_result["idea_upgrade"] != "Insufficient data", "Optimizer idea_upgrade should not be 'Insufficient data'"
        assert optimizer_result["confidence_reason"] != "Analysis failed — retry recommended", "Optimizer confidence_reason should not be fallback value"
        assert optimizer_result["retention_traps"][0]["moment"] != "Insufficient data", "Optimizer retention_traps should not be fallback value"
        assert optimizer_result["next_video_series"][0]["title"] != "Insufficient data", "Optimizer next_video_series should not be fallback value"
        
        print("SUCCESS: Optimizer Agent real call checks passed!")
    except Exception as e:
        print("FAILED: Optimizer Agent real call failed or check asserted false!")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Test fallback path first
    verify_analyst()
    verify_strategist()
    verify_optimizer()
    
    # Test real calls path
    verify_real_calls()
    
    print("\nALL VERIFICATION TESTS (FALLBACK + REAL) PASSED SUCCESSFULLY!")
