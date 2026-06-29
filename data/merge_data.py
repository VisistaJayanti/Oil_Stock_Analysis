
#Importing the packages 
from pathlib import Path
import pandas as pd




SCRIPT_DIR = Path(__file__).resolve().parent

RAW_DIR = SCRIPT_DIR / "raw"
STOCK_DIR = RAW_DIR / "stocks_csv"
PROCESSED_DIR = SCRIPT_DIR / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

BRENT_FILE = RAW_DIR / "brent_clean.csv"
STOCK_FILE = STOCK_DIR / "all_companies.csv"

OUTPUT_FILE = PROCESSED_DIR / "master_dataset.csv"




COMPANY_MAPPING = {
    "Advanced_Petrochemical_Company": "Advanced",
    "Petro_Rabigh": "Petro Rabigh",
    "SABIC": "SABIC",
    "Saudi_Kayan_Petrochemical_Company": "Saudi Kayan",
    "Sipchem": "Sipchem",
    "Tasnee": "Tasnee",
    "Yansab": "Yansab",
    "Saudi_Chemical_Holding_Company": "Saudi Chemical"
}




def load_brent():

    print("\nLoading Brent crude data...")

    brent = pd.read_csv(BRENT_FILE)

    brent["date"] = pd.to_datetime(
        brent["date"],
        format="%d/%m/%Y"
    )

    brent.rename(
        columns={
            "date": "Date",
            "value": "Brent"
        },
        inplace=True
    )

    brent["Date"] = brent["Date"].dt.strftime("%Y-%m-%d")

    brent["Brent"] = pd.to_numeric(brent["Brent"])

    print(f"Loaded {len(brent)} Brent records.")

    return brent




def load_stocks():

    print("\nLoading stock data...")

    stocks = pd.read_csv(STOCK_FILE)

    stocks["Company"] = stocks["Company"].replace(COMPANY_MAPPING)

    stocks["Date"] = pd.to_datetime(
        stocks["Date"]
    ).dt.strftime("%Y-%m-%d")

    stocks = stocks[
        ["Company", "Date", "Close"]
    ]

    print(f"Loaded {len(stocks)} stock records.")

    return stocks



def pivot_stocks(stock_df):

    print("\nPivoting stock prices...")

    pivot = stock_df.pivot_table(
        index="Date",
        columns="Company",
        values="Close",
        aggfunc="first"
    )

    pivot.reset_index(inplace=True)

    pivot.columns.name = None

    print(f"Created dataframe of shape {pivot.shape}")

    return pivot




def merge_datasets(brent_df, stock_df):

    print("\nMerging datasets...")

    merged = pd.merge(
        brent_df,
        stock_df,
        on="Date",
        how="inner"
    )

    merged = merged.sort_values("Date")

    merged.reset_index(drop=True, inplace=True)

    print(f"Merged dataset shape: {merged.shape}")

    return merged



def quality_report(df):

    print("\n" + "=" * 60)
    print("MASTER DATASET SUMMARY")
    print("=" * 60)

    print(f"Rows          : {len(df)}")
    print(f"Columns       : {len(df.columns)}")

    print(f"\nDate Range")
    print(f"{df['Date'].min()}  -->  {df['Date'].max()}")

    print("\nColumns")

    for col in df.columns:
        print(f"• {col}")

    print("\nMissing Values")

    print(df.isnull().sum())

    print("\nFirst Five Rows")

    print(df.head())

    print("=" * 60)


# ==========================================================
# Save
# ==========================================================

def save_dataset(df):

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"\nMaster dataset saved to:\n{OUTPUT_FILE}")


# ==========================================================
# Main
# ==========================================================

def main():

    brent = load_brent()

    stocks = load_stocks()

    stocks = pivot_stocks(stocks)

    master = merge_datasets(
        brent,
        stocks
    )

    quality_report(master)

    save_dataset(master)


if __name__ == "__main__":
    main()