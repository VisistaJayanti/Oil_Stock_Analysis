import os
import json
import yfinance as yf
import pandas as pd

OUTPUT_FOLDER = "raw/stocks"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

companies = {
    "Saudi_Chemical_Holding_Company" : "2230.SR",
    "SABIC": "2010.SR",
    "Tasnee": "2060.SR",
    "Yansab": "2290.SR",
    "Sipchem": "2310.SR",
    "Saudi_Kayan": "2350.SR",
    "Advanced": "2330.SR",
    "Petro_Rabigh": "2380.SR"
}

START_DATE = "2020-01-01"
END_DATE = "2026-06-28"

for company, ticker in companies.items():

    print(f"Downloading {company} ({ticker})...")

    df = yf.download(
        ticker,
        start=START_DATE,
        end=END_DATE,
        progress=False,
        auto_adjust=False
    )

    if df.empty:
        print(f"  No data found for {company}. Skipping.")
        continue

    # Fix MultiIndex columns — flatten tuple columns to just the first level
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    # Reset index so Date becomes a column
    df.reset_index(inplace=True)

    # Convert dates to string
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    # Convert to list of dicts — all keys will now be plain strings
    records = df.to_dict(orient="records")

    output_file = os.path.join(OUTPUT_FOLDER, f"{company}.json")
    with open(output_file, "w") as f:
        json.dump(records, f, indent=4, default=str)

    print(f"  Saved → {output_file} ({len(records)} rows)")

print("\nFinished downloading all companies.")