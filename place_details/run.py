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
    "reviews"
)


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
    return {
        "name": place.get("displayName", {}).get("text"),
        "address": place.get("formattedAddress"),
        "phone": place.get("internationalPhoneNumber"),
        "website": place.get("websiteUri"),
        "rating": place.get("rating"),
        "rating_count": place.get("userRatingCount"),
        "price_level": price_level.removeprefix("PRICE_LEVEL_") if price_level is not None else None,
        "open_now": open_now,
        "opening_hours": opening_hours,
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
