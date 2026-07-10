import base64
import json
import time
import traceback
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import requests
import llm_client
from pydantic import BaseModel

class ThumbnailVisionOutput(BaseModel):
    dominant_colors: str
    composition: str
    text_overlays: str
    mood: str



@dataclass
class ThumbnailDescription:
    url: str
    dominant_colors: str  # e.g. "dark background, blue code syntax, white text"
    composition: str  # e.g. "code editor screenshot taking 80% of frame, person in corner"
    text_overlays: str  # e.g. "Large red text: 'STRIPE' — smaller white: 'Full Tutorial'"
    mood: str  # e.g. "technical, dark, intimidating"
    fetch_successful: bool = True
    error: str = ""


@dataclass
class ThumbnailAnalysis:
    descriptions: List[ThumbnailDescription] = field(default_factory=list)
    combined_summary: str = ""  # one paragraph combining all thumbnail patterns
    dominant_pattern: str = ""  # what all thumbnails have in common
    contrast_opportunity: str = ""  # what visual approach would stand out against these
    analysis_successful: bool = False
    error_message: str = ""


def _fetch_image_as_base64(url: str, timeout_s: int = 10) -> Optional[str]:
    """
    Downloads an image from a URL and returns base64-encoded bytes, or None on failure.
    """
    try:
        response = requests.get(
            url,
            timeout=timeout_s,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if response.status_code != 200:
            print(f"[thumbnails] HTTP {response.status_code} for {url}")
            return None
        content_type = response.headers.get("Content-Type", "")
        if not content_type.lower().startswith("image/"):
            print(
                f"[thumbnails] unexpected Content-Type '{content_type}' for {url} — skipping"
            )
            return None
        out = base64.b64encode(response.content).decode("utf-8")
        return out
    except Exception as e:
        print(f"[thumbnails] fetch failed for {url}: {e}")
        return None


def _analyse_single_thumbnail(
    url: str,
    image_b64: str,
) -> ThumbnailDescription:
    """
    Calls Gemini vision on one base64 image and parses JSON fields into ThumbnailDescription.
    """
    from langchain_core.messages import HumanMessage

    prompt_text = (
        "Analyse this YouTube thumbnail image. Respond with ONLY a JSON object "
        "containing exactly these four string fields:\n"
        "- dominant_colors: describe the main colors and color scheme in under 15 words\n"
        "- composition: describe the layout and main visual elements in under 20 words\n"
        "- text_overlays: list any text visible on the thumbnail exactly as written, "
        "or 'none' if no text\n"
        "- mood: describe the emotional tone and style in under 10 words\n"
        "Do not include any explanation outside the JSON object."
    )

    message = HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
            },
            {
                "type": "text",
                "text": prompt_text
            }
        ]
    )

    try:
        structured_llm = llm_client.get_structured_llm(ThumbnailVisionOutput, temperature=0.1)
        res = structured_llm.invoke([message])
        return ThumbnailDescription(
            url=url,
            dominant_colors=res.dominant_colors,
            composition=res.composition,
            text_overlays=res.text_overlays,
            mood=res.mood,
            fetch_successful=True,
            error="",
        )
    except Exception as e:
        print(f"[thumbnails] vision analysis failed: {e}")
        return ThumbnailDescription(
            url=url,
            dominant_colors="Unknown",
            composition="Unknown",
            text_overlays="Unknown",
            mood="Unknown",
            fetch_successful=False,
            error=str(e),
        )


def _generate_combined_summary(
    descriptions: List[ThumbnailDescription],
) -> Tuple[str, str, str]:
    """
    Deterministic summary: combined paragraph, dominant pattern line, contrast tip.
    """
    parts: List[str] = []
    for i, d in enumerate(descriptions):
        if d.fetch_successful:
            parts.append(
                f"Thumbnail {i + 1}: {d.composition}. "
                f"Colors: {d.dominant_colors}. "
                f"Text: {d.text_overlays}. "
                f"Mood: {d.mood}."
            )
    combined_summary = " | ".join(parts) if parts else "No thumbnails successfully analysed."

    dark_count = 0
    code_count = 0
    text_overlay_count = 0
    for d in descriptions:
        dc = (d.dominant_colors or "").lower()
        mood = (d.mood or "").lower()
        comp = (d.composition or "").lower()
        to = (d.text_overlays or "").strip().lower()

        if "dark" in dc or "dark" in mood:
            dark_count += 1
        if "code" in comp or "screen" in comp:
            code_count += 1
        if to and to not in ("none", "unknown"):
            text_overlay_count += 1

    if dark_count >= 2 and code_count >= 2:
        dominant_pattern = (
            "Most competitor thumbnails use dark backgrounds with code editor "
            "screenshots and bold text overlays."
        )
    elif dark_count >= 2 and code_count < 2:
        dominant_pattern = (
            "Most competitor thumbnails use dark, moody color schemes with strong text overlays."
        )
    elif code_count >= 2 and dark_count < 2:
        dominant_pattern = (
            "Most competitor thumbnails feature code editor screenshots with technical compositions."
        )
    else:
        dominant_pattern = (
            "Competitor thumbnails vary in style without a clear dominant pattern."
        )

    dp_lower = dominant_pattern.lower()
    if "dark" in dp_lower and "code" in dp_lower:
        contrast_opportunity = (
            "Use a bright, light background showing the end-result product UI (not the code editor) "
            "with minimal or no text overlay — this will immediately stand out on the search results page."
        )
    elif "dark" in dp_lower:
        contrast_opportunity = (
            "Use a high-contrast bright color scheme (white or yellow background) with a clean, "
            "simple composition to contrast the dark thumbnails that dominate this search result."
        )
    elif "code" in dp_lower:
        contrast_opportunity = (
            "Show the finished product or outcome instead of code — a clean UI screenshot or a "
            "real-world result will visually differentiate from the code-heavy competitor thumbnails."
        )
    else:
        contrast_opportunity = (
            "Use a bold, single-focus composition with one strong visual element and a clear color "
            "accent to stand out from the varied competitor thumbnails."
        )

    return combined_summary, dominant_pattern, contrast_opportunity


def _fetch_and_analyse_single(url: str, idx: int, total: int) -> ThumbnailDescription:
    print(f"[thumbnails] fetching thumbnail {idx + 1}/{total}: {url[:60]}...")
    image_b64 = _fetch_image_as_base64(url)
    if image_b64 is None:
        return ThumbnailDescription(
            url=url,
            dominant_colors="Unknown",
            composition="Unknown",
            text_overlays="Unknown",
            mood="Unknown",
            fetch_successful=False,
            error="Image fetch failed",
        )
    print(f"[thumbnails] image fetched ({len(image_b64)} b64 chars) — running vision analysis for thumbnail {idx + 1}...")
    description = _analyse_single_thumbnail(url, image_b64)
    dc_preview = description.dominant_colors[:40]
    print(f"[thumbnails] thumbnail {idx + 1} — colors: {dc_preview}, mood: {description.mood}")
    return description


def analyse_thumbnails(
    thumbnail_urls: List[str],
) -> ThumbnailAnalysis:
    """
    Fetches up to 3 thumbnail images and analyses them concurrently using Gemini vision.
    Returns ThumbnailAnalysis with per-thumbnail descriptions and a combined summary.
    Falls back gracefully if images cannot be fetched or vision call fails.
    """
    if not thumbnail_urls:
        return ThumbnailAnalysis(
            analysis_successful=False,
            error_message="No thumbnail URLs provided.",
        )

    urls_to_analyse = thumbnail_urls[:3]
    total = len(urls_to_analyse)
    print(f"[thumbnails] analysing {total} thumbnails concurrently...")

    t0 = time.monotonic()
    descriptions: List[ThumbnailDescription] = [None] * total

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=total) as executor:
        future_to_index = {
            executor.submit(_fetch_and_analyse_single, url, idx, total): idx
            for idx, url in enumerate(urls_to_analyse)
        }
        for future in concurrent.futures.as_completed(future_to_index):
            idx = future_to_index[future]
            url = urls_to_analyse[idx]
            try:
                descriptions[idx] = future.result()
            except Exception as e:
                print(f"[thumbnails] worker crashed for {url}: {e}")
                descriptions[idx] = ThumbnailDescription(
                    url=url,
                    dominant_colors="Unknown",
                    composition="Unknown",
                    text_overlays="Unknown",
                    mood="Unknown",
                    fetch_successful=False,
                    error=str(e),
                )

    successful = [d for d in descriptions if d.fetch_successful]

    if not successful:
        return ThumbnailAnalysis(
            descriptions=descriptions,
            analysis_successful=False,
            error_message="All thumbnail fetches failed — no visual analysis available.",
        )

    combined_summary, dominant_pattern, contrast_opportunity = _generate_combined_summary(
        descriptions
    )

    elapsed = time.monotonic() - t0
    print(
        f"[thumbnails] analysis complete in {elapsed:.1f}s — "
        f"{len(successful)}/{len(descriptions)} thumbnails analysed successfully"
    )
    print(f"[thumbnails] dominant_pattern: {dominant_pattern[:80]}...")

    return ThumbnailAnalysis(
        descriptions=descriptions,
        combined_summary=combined_summary,
        dominant_pattern=dominant_pattern,
        contrast_opportunity=contrast_opportunity,
        analysis_successful=True,
        error_message="",
    )


def thumbnail_analysis_to_prompt_block(analysis: ThumbnailAnalysis) -> str:
    """
    Formats ThumbnailAnalysis into a plain-text block for injection
    into the strategist agent user prompt under the label
    'COMPETITOR THUMBNAIL VISUAL ANALYSIS'.
    """
    if not analysis.analysis_successful:
        return (
            "COMPETITOR THUMBNAIL VISUAL ANALYSIS:\n"
            "Visual analysis unavailable — thumbnail images could not be fetched.\n"
            "Base contrast rule on the thumbnail URLs provided.\n"
        )

    lines = ["COMPETITOR THUMBNAIL VISUAL ANALYSIS:"]

    for i, d in enumerate(analysis.descriptions):
        if d.fetch_successful:
            lines.append(f"Thumbnail {i + 1}:")
            lines.append(f"  Colors: {d.dominant_colors}")
            lines.append(f"  Composition: {d.composition}")
            lines.append(f"  Text overlays: {d.text_overlays}")
            lines.append(f"  Mood: {d.mood}")
        else:
            lines.append(
                f"Thumbnail {i + 1}: [fetch failed — URL: {d.url[:60]}]"
            )

    lines.append(f"\nDominant pattern across all thumbnails: {analysis.dominant_pattern}")
    lines.append(f"Contrast opportunity: {analysis.contrast_opportunity}")

    return "\n".join(lines)


if __name__ == "__main__":
    import os
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

    gemini_key = os.getenv("GEMINI_API_KEY")
    youtube_key = os.getenv("YOUTUBE_API_KEY")

    if not gemini_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
    elif not youtube_key:
        print("ERROR: YOUTUBE_API_KEY not found in .env")
    else:
        from competitor_scraper import scrape_competitor_intelligence

        test_queries = [
            "how to build SaaS with Next.js and Stripe",
            "Next.js Stripe subscription tutorial",
            "Stripe webhook handling Next.js tutorial",
        ]
        print("[test] running competitor scraper to get real thumbnail URLs...")
        intel = scrape_competitor_intelligence(test_queries, youtube_key)

        if not intel.scrape_successful:
            print(f"[test] scraper failed: {intel.error_message}")
        else:
            print(f"[test] got {len(intel.top_thumbnail_urls)} thumbnail URLs")
            print(f"[test] URLs: {intel.top_thumbnail_urls}")

            print("\n[test] running thumbnail analysis...")
            analysis = analyse_thumbnails(intel.top_thumbnail_urls)

            print(f"\n[test] analysis_successful: {analysis.analysis_successful}")
            print(f"[test] error_message: {analysis.error_message}")
            print(f"[test] descriptions count: {len(analysis.descriptions)}")

            for i, d in enumerate(analysis.descriptions):
                print(f"\n  Thumbnail {i + 1}:")
                print(f"    fetch_successful: {d.fetch_successful}")
                print(f"    dominant_colors: {d.dominant_colors}")
                print(f"    composition: {d.composition}")
                print(f"    text_overlays: {d.text_overlays}")
                print(f"    mood: {d.mood}")

            print(f"\n[test] dominant_pattern: {analysis.dominant_pattern}")
            print(f"[test] contrast_opportunity: {analysis.contrast_opportunity}")
            print(f"\n[test] prompt block preview:")
            print(thumbnail_analysis_to_prompt_block(analysis))
