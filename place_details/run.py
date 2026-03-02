#!/usr/bin/env -S uv run
# /// script
# dependencies = ["requests"]
# ///

import json
import sys
from pathlib import Path
from typing import Any

import requests


KNOWN_PARAMS = {"place_id"}

# Bayesian average constants: C is the prior mean rating, m is the weight given to the
# prior (equivalent to the number of "virtual" reviews anchoring toward C). These values
# were chosen to reflect a reasonable prior for Google Places data.
BAYESIAN_PRIOR_MEAN = 4.2
BAYESIAN_PRIOR_WEIGHT = 200

# Only request the fields we display to avoid billing for unused data.
FIELD_MASK = (
    "displayName,"
    "formattedAddress,"
    "internationalPhoneNumber,"
    "websiteUri,"
    "rating,"
    "userRatingCount,"
    "priceLevel,"
    "currentOpeningHours,"
    "editorialSummary,"
    "reviews"
)


def compute_score(rating: float | None, rating_count: int | None) -> float | None:
    if rating is None or rating_count is None:
        return None
    score = (
        (rating_count / (rating_count + BAYESIAN_PRIOR_WEIGHT)) * rating
        + (BAYESIAN_PRIOR_WEIGHT / (rating_count + BAYESIAN_PRIOR_WEIGHT)) * BAYESIAN_PRIOR_MEAN
    )
    return round(score, 2)


def transform_review(review: dict[str, Any]) -> dict[str, Any]:
    text = review.get("text", {}).get("text")
    if text is not None and len(text) > 200:
        text = text[:200] + "..."
    return {
        "author": review.get("authorAttribution", {}).get("displayName"),
        "rating": review.get("rating"),
        "text": text,
        "relative_time": review.get("relativePublishTimeDescription"),
    }


def transform_place(place: dict[str, Any]) -> dict[str, Any]:
    open_now = None
    opening_hours = None
    if "currentOpeningHours" in place:
        open_now = place["currentOpeningHours"].get("openNow")
        descriptions = place["currentOpeningHours"].get("weekdayDescriptions")
        if descriptions is not None:
            opening_hours = descriptions

    reviews = None
    if "reviews" in place:
        reviews = [transform_review(r) for r in place["reviews"][:5]]

    price_level = place.get("priceLevel")
    rating = place.get("rating")
    rating_count = place.get("userRatingCount")
    return {
        "name": place.get("displayName", {}).get("text"),
        "address": place.get("formattedAddress"),
        "phone": place.get("internationalPhoneNumber"),
        "website": place.get("websiteUri"),
        "rating": rating,
        "rating_count": rating_count,
        "score": compute_score(rating, rating_count),
        "price_level": price_level.removeprefix("PRICE_LEVEL_") if price_level is not None else None,
        "open_now": open_now,
        "opening_hours": opening_hours,
        "editorial_summary": place.get("editorialSummary", {}).get("text"),
        "reviews": reviews,
    }


def main() -> None:
    params = json.load(sys.stdin)
    unknown = set(params) - KNOWN_PARAMS
    if unknown:
        print(f"Unknown parameters: {', '.join(sorted(unknown))}", file=sys.stderr)
        sys.exit(1)

    if "place_id" not in params:
        print("Missing required parameter: place_id", file=sys.stderr)
        sys.exit(1)

    config = json.loads(Path("../config.json").read_text())
    api_key = config["api_key"]

    place_id = params["place_id"]
    response = requests.get(
        f"https://places.googleapis.com/v1/places/{place_id}",
        headers={
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": FIELD_MASK,
        },
    )

    if not response.ok:
        print(f"HTTP {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    place = response.json()
    json.dump(transform_place(place), sys.stdout)


main()
