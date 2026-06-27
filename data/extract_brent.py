import os
import requests
import json
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

API_KEY = "89I94F6F1BMT9MR1"

BASE_URL = "https://www.alphavantage.co/query"

# Where we will store raw data
RAW_PATH = Path("data/raw")
RAW_PATH.mkdir(parents=True, exist_ok=True)


def fetch_brent_data():
    """
    Fetch Brent crude oil data from Alpha Vantage API
    """

    params = {
        "function": "BRENT",
        "interval": "daily",
        "apikey": API_KEY
    }

    response = requests.get(BASE_URL, params=params)

    # Step 1: check request success
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code}")

    data = response.json()

    # Step 2: check API error responses
    if "Error Message" in data:
        raise Exception(f"API Error: {data['Error Message']}")

    if "Note" in data:
        raise Exception("API rate limit hit. Try again later.")

    if "Information" in data:
        raise Exception(f"API access issue: {data['Information']}")

    # Step 3: confirm expected keys exist
    print(f"[fetch_brent_data] API response keys: {list(data.keys())}")

    return data


def extract_time_series(raw_data):
    """
    Convert API response into clean time series format.
    Alpha Vantage BRENT endpoint returns data under the key 'data' (lowercase).
    """

    # Find the correct key — handles 'data', 'Data', 'Time Series', etc.
    time_series_key = None
    for key in raw_data.keys():
        if "Time Series" in key or "data" in key.lower():
            time_series_key = key
            break

    if time_series_key is None:
        raise Exception(
            f"Time series data not found in API response. "
            f"Available keys: {list(raw_data.keys())}"
        )

    time_series = raw_data[time_series_key]

    # Alpha Vantage BRENT returns a list of dicts: [{"date": "...", "value": "..."}]
    # Stock endpoints return a dict of dicts: {"2026-06-25": {"1. open": ...}}
    # Handle both formats
    cleaned = []

    if isinstance(time_series, list):
        # BRENT format — list of {"date": "...", "value": "..."}
        for record in time_series:
            value = record.get("value", None)
            if value is None or value == ".":
                continue
            cleaned.append({
                "date":  record["date"],
                "value": float(value)
            })

    elif isinstance(time_series, dict):
        # Stock format — dict of {"date": {"1. open": ..., "4. close": ...}}
        for date, values in time_series.items():
            # Try common value keys
            value = (
                values.get("value") or
                values.get("4. close") or
                values.get("close") or
                None
            )
            if value is None:
                continue
            cleaned.append({
                "date":  date,
                "value": float(value)
            })

    else:
        raise Exception(f"Unexpected time series format: {type(time_series)}")

    if not cleaned:
        raise Exception("Time series was found but contained no valid records.")

    # Sort by date ascending
    cleaned.sort(key=lambda x: x["date"])

    print(f"[extract_time_series] Extracted {len(cleaned)} records "
          f"from '{time_series_key}' ({cleaned[0]['date']} → {cleaned[-1]['date']})")

    return cleaned


def save_raw(data, filename="brent_raw.json"):
    """
    Save raw API response
    """
    path = RAW_PATH / filename

    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"[save_raw] Saved to {path}")
    return path


def save_clean(data, filename="brent_clean.json"):
    """
    Save cleaned dataset
    """
    path = RAW_PATH / filename

    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"[save_clean] Saved {len(data)} records to {path}")
    return path


if __name__ == "__main__":
    print("Fetching Brent crude data...")
    raw = fetch_brent_data()
    save_raw(raw)

    print("Extracting time series...")
    clean = extract_time_series(raw)
    save_clean(clean)

    print(f"Done. {len(clean)} records saved.")
    print(f"Latest: {clean[-1]}")