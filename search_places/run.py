#!/usr/bin/env -S uv run
# /// script
# dependencies = ["requests"]
# ///

import json
import sys
from pathlib import Path
from typing import Any

import requests


KNOWN_PARAMS = {"query", "min_rating", "open_now"}

# Bayesian average constants: C is the prior mean rating, m is the weight given to the
# prior (equivalent to the number of "virtual" reviews anchoring toward C). These values
# were chosen to reflect a reasonable prior for Google Maps data.
BAYESIAN_PRIOR_MEAN = 4.2
BAYESIAN_PRIOR_WEIGHT = 200

# Only request the fields we display to avoid billing for unused data.
FIELD_MASK = (
    "places.id,"
    "places.displayName,"
    "places.formattedAddress,"
    "places.rating,"
    "places.userRatingCount,"
    "places.priceLevel,"
    "places.currentOpeningHours"
)


def compute_score(rating: float | None, rating_count: int | None) -> float | None:
    if rating is None or rating_count is None:
        return None
    score = (
        (rating_count / (rating_count + BAYESIAN_PRIOR_WEIGHT)) * rating
        + (BAYESIAN_PRIOR_WEIGHT / (rating_count + BAYESIAN_PRIOR_WEIGHT)) * BAYESIAN_PRIOR_MEAN
    )
    return round(score, 2)


def transform_place(place: dict[str, Any]) -> dict[str, Any]:
    open_now = None
    if "currentOpeningHours" in place:
        open_now = place["currentOpeningHours"].get("openNow")

    price_level = place.get("priceLevel")
    rating = place.get("rating")
    rating_count = place.get("userRatingCount")
    return {
        "id": place.get("id"),
        "name": place.get("displayName", {}).get("text"),
        "address": place.get("formattedAddress"),
        "rating": rating,
        "rating_count": rating_count,
        "price_level": price_level.removeprefix("PRICE_LEVEL_") if price_level is not None else None,
        "open_now": open_now,
        "score": compute_score(rating, rating_count),
    }


def main() -> None:
    params = json.load(sys.stdin)
    unknown = set(params) - KNOWN_PARAMS
    if unknown:
        print(f"Unknown parameters: {', '.join(sorted(unknown))}", file=sys.stderr)
        sys.exit(1)

    if "query" not in params:
        print("Missing required parameter: query", file=sys.stderr)
        sys.exit(1)

    config = json.loads(Path("../config.json").read_text())
    api_key = config["api_key"]

    request_body: dict[str, Any] = {"textQuery": params["query"]}
    if "min_rating" in params:
        request_body["minRating"] = params["min_rating"]
    if "open_now" in params:
        request_body["openNow"] = params["open_now"]

    response = requests.post(
        "https://places.googleapis.com/v1/places:searchText",
        headers={
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": FIELD_MASK,
            "Content-Type": "application/json",
        },
        json=request_body,
    )

    if not response.ok:
        print(f"HTTP {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    data = response.json()
    places = [transform_place(place) for place in data.get("places", [])]
    places.sort(key=lambda place: place["score"] if place["score"] is not None else -1, reverse=True)
    json.dump({"places": places}, sys.stdout)


main()
