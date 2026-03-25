from typing import Optional

from creator_profile import CreatorProfile, DerivedCreatorProfile


def build_creator_profile(
    input_profile: Optional[CreatorProfile],
) -> DerivedCreatorProfile:
    if input_profile is None or input_profile.subscriber_count is None:
        return DerivedCreatorProfile(
            mode="generic",
            subscriber_count=None,
            avg_views=None,
            niche=None,
            channel_size_bucket="small",
            growth_stage="early",
            performance_ratio=1.0,
            competition_tolerance="low",
            strengths=[],
            weaknesses=[],
            interests=[],
            recent_videos=[],
        )

    subs = input_profile.subscriber_count
    avg_views = input_profile.avg_views if input_profile.avg_views is not None else 0

    # SAFE division
    if subs > 0:
        performance_ratio = avg_views / subs
    else:
        performance_ratio = 0.0

    # bucket logic (NO sharp jumps)
    if subs < 3000:
        bucket = "small"
        stage = "early"
    elif subs < 30000:
        bucket = "growing"
        stage = "mid"
    else:
        bucket = "large"
        stage = "established"

    if subs < 3000:
        tolerance = "low"
    elif subs < 30000:
        tolerance = "medium"
    else:
        tolerance = "high"

    performance_ratio = round(min(performance_ratio, 10), 2)

    return DerivedCreatorProfile(
        mode="personalized",
        subscriber_count=subs,
        avg_views=avg_views,
        niche=input_profile.niche,
        channel_size_bucket=bucket,
        growth_stage=stage,
        performance_ratio=performance_ratio,
        competition_tolerance=tolerance,
        strengths=input_profile.strengths or [],
        weaknesses=input_profile.weaknesses or [],
        interests=input_profile.interests or [],
        recent_videos=input_profile.recent_videos or [],
    )


def is_personalized(profile: DerivedCreatorProfile) -> bool:
    return profile.mode == "personalized"

