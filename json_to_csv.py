import json
import csv
import os

INPUT_FOLDER = "raw/stocks"
OUTPUT_FILE = "raw/stocks_csv/all_companies.csv"

os.makedirs("raw/stocks_csv", exist_ok=True)

all_records = []

for filename in os.listdir(INPUT_FOLDER):
    if filename.endswith(".json"):
        company_name = filename.replace(".json", "")  # e.g. "SABIC"
        
        with open(os.path.join(INPUT_FOLDER, filename)) as f:
            data = json.load(f)
        
        for record in data:
            record["Company"] = company_name  # Add company label
            all_records.append(record)
        
        print(f"Loaded {len(data)} rows from {filename}")

# Write combined CSV
headers = ["Company", "Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]

with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(all_records)

print(f"\nDone. Total rows: {len(all_records)} → {OUTPUT_FILE}")