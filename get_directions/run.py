#!/usr/bin/env -S uv run
# /// script
# dependencies = ["requests"]
# ///

import json
import sys
from pathlib import Path
from typing import Any

import requests


KNOWN_PARAMS = {"origin", "destination", "travel_mode", "departure_time", "arrival_time"}

# Only request the fields we display to avoid billing for unused data.
FIELD_MASK = (
    "routes.legs.steps.navigationInstruction,"
    "routes.legs.steps.localizedValues,"
    "routes.legs.localizedValues,"
    "routes.distanceMeters,"
    "routes.duration,"
    "routes.localizedValues"
)


def transform_step(step: dict[str, Any]) -> dict[str, Any]:
    nav = step.get("navigationInstruction")
    result: dict[str, Any] = {
        "instruction": nav.get("instructions") if nav is not None else None,
    }
    if "localizedValues" in step:
        localized = step["localizedValues"]
        distance = localized.get("distance")
        static_duration = localized.get("staticDuration")
        if distance is not None:
            result["distance"] = distance["text"]
        if static_duration is not None:
            result["duration"] = static_duration["text"]
    return result


def main() -> None:
    params = json.load(sys.stdin)
    unknown = set(params) - KNOWN_PARAMS
    if unknown:
        print(f"Unknown parameters: {', '.join(sorted(unknown))}", file=sys.stderr)
        sys.exit(1)

    if "origin" not in params:
        print("Missing required parameter: origin", file=sys.stderr)
        sys.exit(1)

    if "destination" not in params:
        print("Missing required parameter: destination", file=sys.stderr)
        sys.exit(1)

    config = json.loads(Path("../config.json").read_text())
    api_key = config["api_key"]

    travel_mode = params.get("travel_mode", "DRIVE")

    request_body: dict[str, Any] = {
        "origin": {"address": params["origin"]},
        "destination": {"address": params["destination"]},
        "travelMode": travel_mode,
    }

    # The API rejects routingPreference for non-DRIVE modes.
    if travel_mode == "DRIVE":
        request_body["routingPreference"] = "TRAFFIC_AWARE"

    if "departure_time" in params:
        request_body["departureTime"] = params["departure_time"]

    if "arrival_time" in params:
        request_body["arrivalTime"] = params["arrival_time"]

    response = requests.post(
        "https://routes.googleapis.com/directions/v2:computeRoutes",
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
    route = data["routes"][0]
    localized = route["localizedValues"]
    steps = [
        transformed
        for step in route["legs"][0]["steps"]
        if (transformed := transform_step(step))["instruction"] is not None
    ]
    json.dump(
        {
            "distance": localized["distance"]["text"],
            "duration": localized["duration"]["text"],
            "steps": steps,
        },
        sys.stdout,
    )


main()
