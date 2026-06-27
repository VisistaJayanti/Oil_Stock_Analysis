import os
import json
import yfinance as yf

# Create output folder
OUTPUT_FOLDER = "raw/stocks"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Saudi Petrochemical Companies
companies = {
    "SABIC": "2010.SR",
    "Tasnee": "2060.SR",
    "Yansab": "2290.SR",
    "Sipchem": "2310.SR",
    "Saudi_Kayan": "2350.SR",
    "Advanced": "2330.SR",
    "Petro_Rabigh": "2380.SR"
}

START_DATE = "2020-01-01"
END_DATE = "2025-12-31"

for company, ticker in companies.items():

    print(f"Downloading {company}...")

    df = yf.download(
        ticker,
        start=START_DATE,
        end=END_DATE,
        progress=False,
        auto_adjust=False
    )

    if df.empty:
        print(f"No data found for {company}")
        continue

    # Reset index so Date becomes a column
    df.reset_index(inplace=True)

    # Convert dates to string
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    # Convert dataframe to list of dictionaries
    records = df.to_dict(orient="records")

    output_file = os.path.join(OUTPUT_FOLDER, f"{company}.json")

    with open(output_file, "w") as f:
        json.dump(records, f, indent=4)

    print(f"Saved {company}.json")

print("Finished downloading all companies.")