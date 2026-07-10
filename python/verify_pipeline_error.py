import os
import sys
import traceback
from dotenv import load_dotenv

# Load env variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Ensure sys.path includes the python directory
sys.path.append(os.path.dirname(__file__))

try:
    import pipeline_graph
    from pipeline_graph import pipeline_app
    print("SUCCESS: Imported pipeline graph successfully!")
except Exception as e:
    print("FAILED: Import failed!")
    traceback.print_exc()
    sys.exit(1)


def test_scrape_failure_400():
    print("\n--- Testing Scraper Failure (400 Path) ---")
    
    # 1. Define mock failure function
    def mock_failed_scrape(queries, api_key):
        from competitor_scraper import CompetitorIntelligence
        return CompetitorIntelligence(
            scrape_successful=False,
            error_message="Simulated API rate limit exceeded."
        )

    # 2. Patch the function in pipeline_graph namespace
    original_scrape_func = pipeline_graph.scrape_competitor_intelligence
    pipeline_graph.scrape_competitor_intelligence = mock_failed_scrape

    try:
        initial_state = {
            "video_idea": "Test video idea",
            "creator_dna": "Test creator DNA",
        }
        
        # Invoke the graph
        result = pipeline_app.invoke(initial_state)
        
        # Print output state for visual confirmation
        print("Scraper Failure Output State:")
        print(f"  error: {result.get('error')}")
        print(f"  error_status_code: {result.get('error_status_code')}")
        
        # Asserts
        assert result.get("error") is not None
        assert "Simulated API rate limit exceeded." in result["error"]
        assert result.get("error_status_code") == 400
        
        print("SUCCESS: Scraper Failure 400 path verification passed!")
    except Exception as e:
        print("FAILED: Scraper Failure 400 path verification failed!")
        traceback.print_exc()
        sys.exit(1)
    finally:
        pipeline_graph.scrape_competitor_intelligence = original_scrape_func


def test_scraper_exception_500():
    print("\n--- Testing Scraper Exception (500 Path) ---")

    # 1. Define mock exception function
    def mock_exception_scrape(queries, api_key):
        raise ConnectionError("Timeout connecting to YouTube API server")

    # 2. Patch the function in pipeline_graph namespace
    original_scrape_func = pipeline_graph.scrape_competitor_intelligence
    pipeline_graph.scrape_competitor_intelligence = mock_exception_scrape

    try:
        initial_state = {
            "video_idea": "Test video idea",
            "creator_dna": "Test creator DNA",
        }
        
        # Invoke the graph
        result = pipeline_app.invoke(initial_state)

        # Print output state for visual confirmation
        print("Scraper Exception Output State:")
        print(f"  error: {result.get('error')}")
        print(f"  error_status_code: {result.get('error_status_code')}")

        # Asserts
        assert result.get("error") is not None
        assert "Timeout connecting to YouTube API server" in result["error"]
        assert result.get("error_status_code") == 500

        print("SUCCESS: Scraper Exception 500 path verification passed!")
    except Exception as e:
        print("FAILED: Scraper Exception 500 path verification failed!")
        traceback.print_exc()
        sys.exit(1)
    finally:
        pipeline_graph.scrape_competitor_intelligence = original_scrape_func


if __name__ == "__main__":
    test_scrape_failure_400()
    test_scraper_exception_500()
    print("\nALL ERROR PATH VERIFICATION TESTS PASSED!")
