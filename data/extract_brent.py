import json
import requests
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


API_KEY = "89I94F6F1BMT9MR1"
BASE_URL = "https://www.alphavantage.co/query"

START_DATE = "2020-01-01"
END_DATE = "2026-06-28"

RAW_PATH = Path("data/raw")
RAW_PATH.mkdir(parents=True, exist_ok=True)




def fetch_brent_data():
    """
    Fetch Brent crude oil data from Alpha Vantage.
    """

    params = {
        "function": "BRENT",
        "interval": "daily",
        "apikey": API_KEY
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code}")

    data = response.json()

    if "Error Message" in data:
        raise Exception(data["Error Message"])

    if "Information" in data:
        raise Exception(data["Information"])

    if "Note" in data:
        raise Exception("API rate limit exceeded.")

    return data




def extract_time_series(raw_data):
    """
    Extract Brent data and keep only the specified date range.
    """

    if "data" not in raw_data:
        raise Exception("No 'data' field found in API response.")

    cleaned = []

    for record in raw_data["data"]:

        value = record.get("value")

        # Skip missing values
        if value is None or value == ".":
            continue

        date = record["date"]

        # Keep only required dates
        if START_DATE <= date <= END_DATE:

            cleaned.append({
                "date": date,
                "value": float(value)
            })

    cleaned.sort(key=lambda x: x["date"])

    print(f"Extracted {len(cleaned)} records.")
    print(f"Date range: {cleaned[0]['date']} -> {cleaned[-1]['date']}")

    return cleaned




def save_json(data, filename):
    path = RAW_PATH / filename

    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Saved: {path}")



if __name__ == "__main__":

    print("Fetching Brent crude oil data...")

    raw_data = fetch_brent_data()

    save_json(raw_data, "brent_raw.json")

    print("Filtering data...")

    cleaned_data = extract_time_series(raw_data)

    save_json(cleaned_data, "brent_clean.json")

    print("\nDone!")
    print(f"Records saved: {len(cleaned_data)}")
    print(f"First record: {cleaned_data[0]}")
    print(f"Last record: {cleaned_data[-1]}")