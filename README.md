# Google Maps plugin

A Stavrobot plugin for searching places, retrieving details, and getting directions using the Google Places API (New) and Routes API.

## Tools

### search_places

Search for places by text query. Returns names, addresses, ratings, price levels, and a composite score that accounts for both rating and number of reviews (Bayesian average). Results are sorted by score.

**Parameters:**

- `query` (string, required) — search query, e.g. "pizza near Times Square" or "pharmacies in Berlin".
- `min_rating` (number, optional) — minimum rating filter (1.0 to 4.5, in 0.5 increments).
- `open_now` (boolean, optional) — only return places that are currently open.

**Score:** the composite score uses a Bayesian average to balance rating against review volume. A place with 4.8 stars and 3,000 reviews will score higher than one with 4.9 stars and 50 reviews, because the latter has less statistical confidence.

### place_details

Get detailed information about a specific place by its ID (as returned by `search_places`). Returns name, address, phone number, website, rating, review count, price level, opening hours, and up to 5 reviews with text truncated to 200 characters.

**Parameters:**

- `place_id` (string, required) — the place ID, as returned by `search_places`.

### get_directions

Get directions between two locations. Returns distance, duration, and turn-by-turn steps.

**Parameters:**

- `origin` (string, required) — origin address or place name.
- `destination` (string, required) — destination address or place name.
- `travel_mode` (string, optional) — `DRIVE`, `WALK`, `BICYCLE`, or `TRANSIT`. Defaults to `DRIVE`.
- `departure_time` (string, optional) — RFC 3339 timestamp for when to depart.
- `arrival_time` (string, optional) — RFC 3339 timestamp for desired arrival time. Only valid for `TRANSIT` travel mode.

## Installation

Tell Stavrobot to install this plugin:

```
install plugin https://github.com/stavrobot/plugin-googleplaces
```

## Configuration

You need a Google API key with the **Places API (New)** and **Routes API** enabled.

To obtain one:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Enable the **Places API (New)** and **Routes API** under APIs & Services.
4. Create an API key under Credentials.

Once you have the key, configure the plugin:

```
configure plugin google-places api_key <your-api-key>
```
