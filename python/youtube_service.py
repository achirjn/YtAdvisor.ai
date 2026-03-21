import re
from datetime import datetime, timezone
from statistics import median
from typing import Dict, List, Set

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

from .models import VideoData


def _chunked(items: List[str], size: int) -> List[List[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _safe_int(value: str | int | None) -> int:
    try:
        return int(value) if value is not None else 0
    except (TypeError, ValueError):
        return 0


def _age_days_from_published_at(published_at: str) -> int:
    try:
        published_dt = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except (TypeError, ValueError):
        return 0
    delta = datetime.now(timezone.utc) - published_dt
    return max(delta.days, 0)


def get_competitor_data(queries: List[str], api_key: str) -> List[VideoData]:
    youtube = build("youtube", "v3", developerKey=api_key)
    deduped_video_ids: List[str] = []
    seen_ids: Set[str] = set()

    for query in queries:
        search_response = (
            youtube.search()
            .list(
                part="id",
                q=query,
                type="video",
                maxResults=5,
            )
            .execute()
        )
        for item in search_response.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if video_id and video_id not in seen_ids:
                seen_ids.add(video_id)
                deduped_video_ids.append(video_id)

    if not deduped_video_ids:
        return []

    video_items: List[dict] = []
    for batch_ids in _chunked(deduped_video_ids, 50):
        videos_response = (
            youtube.videos()
            .list(
                part="snippet,statistics",
                id=",".join(batch_ids),
                maxResults=len(batch_ids),
            )
            .execute()
        )
        video_items.extend(videos_response.get("items", []))

    channel_ids: Set[str] = set()
    for item in video_items:
        channel_id = item.get("snippet", {}).get("channelId")
        if channel_id:
            channel_ids.add(channel_id)

    channel_subscribers: Dict[str, int] = {}
    for batch_channel_ids in _chunked(list(channel_ids), 50):
        channels_response = (
            youtube.channels()
            .list(
                part="statistics",
                id=",".join(batch_channel_ids),
                maxResults=len(batch_channel_ids),
            )
            .execute()
        )
        for channel_item in channels_response.get("items", []):
            channel_id = channel_item.get("id", "")
            subscriber_count = _safe_int(
                channel_item.get("statistics", {}).get("subscriberCount")
            )
            channel_subscribers[channel_id] = subscriber_count

    videos_by_id: Dict[str, VideoData] = {}
    for item in video_items:
        video_id = item.get("id", "")
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})

        channel_id = snippet.get("channelId", "")
        transcript_text = ""
        try:
            transcript_items = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join(
                segment.get("text", "") for segment in transcript_items
            )[:1500]
        except Exception:
            transcript_text = ""

        videos_by_id[video_id] = VideoData(
            video_id=video_id,
            title=snippet.get("title", ""),
            view_count=_safe_int(statistics.get("viewCount")),
            subscriber_count=channel_subscribers.get(channel_id, 0),
            age_days=_age_days_from_published_at(snippet.get("publishedAt", "")),
            category_id=snippet.get("categoryId", ""),
            transcript=transcript_text,
        )

    ordered_videos: List[VideoData] = []
    for video_id in deduped_video_ids:
        video_data = videos_by_id.get(video_id)
        if video_data:
            ordered_videos.append(video_data)
    return ordered_videos


def detect_monopoly(videos: List[VideoData]) -> bool:
    if not videos:
        return False
    median_subscribers = median(video.subscriber_count for video in videos)
    median_age_days = median(video.age_days for video in videos)
    return median_subscribers > 500_000 and median_age_days > 365


def detect_personality_driven(videos: List[VideoData]) -> bool:
    if not videos:
        return False

    personality_categories = {"22", "24"}
    category_matches = sum(1 for video in videos if video.category_id in personality_categories)
    category_ratio = category_matches / len(videos)

    pronouns = {"i", "me", "my", "we"}
    pronoun_count = 0
    total_words = 0

    for video in videos:
        words = re.findall(r"\b\w+\b", video.transcript.lower())
        total_words += len(words)
        pronoun_count += sum(1 for word in words if word in pronouns)

    if total_words == 0:
        return False

    pronoun_ratio = pronoun_count / total_words
    return category_ratio > 0.5 and pronoun_ratio > 0.05


def detect_fragmented(video_ids: List[str], api_key: str) -> bool:
    unique_ids: List[str] = []
    seen_ids: Set[str] = set()
    for video_id in video_ids:
        if video_id not in seen_ids:
            seen_ids.add(video_id)
            unique_ids.append(video_id)
        if len(unique_ids) == 3:
            break

    if len(unique_ids) < 3:
        return False

    youtube = build("youtube", "v3", developerKey=api_key)
    related_sets: List[Set[str]] = []

    for seed_video_id in unique_ids:
        try:
            related_response = (
                youtube.search()
                .list(
                    part="id",
                    relatedToVideoId=seed_video_id,
                    type="video",
                    maxResults=5,
                )
                .execute()
            )
        except Exception:
            return False

        related_ids = {
            item.get("id", {}).get("videoId")
            for item in related_response.get("items", [])
            if item.get("id", {}).get("videoId")
        }
        related_sets.append(related_ids)

    if len(related_sets) < 3:
        return False

    common_ids = set.intersection(*related_sets) if related_sets else set()
    return len(common_ids) == 0
