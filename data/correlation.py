"""
correlation.py

Purpose
-------
Perform statistical analysis on the master dataset.

Outputs
-------
summary_statistics.csv
pearson_correlation.csv
spearman_correlation.csv
daily_returns.csv
pearson_returns.csv
brent_ranking.csv
"""

from pathlib import Path
import pandas as pd

# ==========================================================
# Paths
# ==========================================================

SCRIPT_DIR = Path(__file__).resolve().parent

PROCESSED_DIR = SCRIPT_DIR / "processed"

MASTER_FILE = PROCESSED_DIR / "master_dataset.csv"

SUMMARY_FILE = PROCESSED_DIR / "summary_statistics.csv"
PEARSON_FILE = PROCESSED_DIR / "pearson_correlation.csv"
SPEARMAN_FILE = PROCESSED_DIR / "spearman_correlation.csv"
RETURNS_FILE = PROCESSED_DIR / "daily_returns.csv"
RETURNS_CORR_FILE = PROCESSED_DIR / "pearson_returns.csv"
RANKING_FILE = PROCESSED_DIR / "brent_ranking.csv"


# ==========================================================
# Load Dataset
# ==========================================================

def load_dataset():

    print("\nLoading master dataset...")

    df = pd.read_csv(MASTER_FILE)

    print(f"Loaded {len(df)} rows.")
    print(f"Columns: {list(df.columns)}")

    return df


# ==========================================================
# Summary Statistics
# ==========================================================

def generate_summary(df):

    print("\nGenerating summary statistics...")

    numeric_df = df.drop(columns=["Date"])

    summary = numeric_df.describe().transpose()

    summary.to_csv(SUMMARY_FILE)

    print(f"Saved summary statistics to:\n{SUMMARY_FILE}")

    return summary


# ==========================================================
# Pearson Correlation (Prices)
# ==========================================================

def pearson_correlation(df):

    print("\nComputing Pearson correlation (Prices)...")

    numeric_df = df.drop(columns=["Date"])

    corr = numeric_df.corr(method="pearson")

    corr.to_csv(PEARSON_FILE)

    print(f"Saved Pearson correlation matrix to:\n{PEARSON_FILE}")

    return corr


# ==========================================================
# Spearman Correlation
# ==========================================================

def spearman_correlation(df):

    print("\nComputing Spearman correlation...")

    numeric_df = df.drop(columns=["Date"])

    corr = numeric_df.corr(method="spearman")

    corr.to_csv(SPEARMAN_FILE)

    print(f"Saved Spearman correlation matrix to:\n{SPEARMAN_FILE}")

    return corr


# ==========================================================
# Daily Returns
# ==========================================================

def calculate_returns(df):

    print("\nCalculating daily percentage returns...")

    returns = df.copy()

    numeric_cols = returns.columns.drop("Date")

    returns[numeric_cols] = (
        returns[numeric_cols]
        .pct_change()
        * 100
    )

    returns = returns.dropna()

    returns.to_csv(RETURNS_FILE, index=False)

    print(f"Saved daily returns to:\n{RETURNS_FILE}")

    return returns


# ==========================================================
# Pearson Correlation (Returns)
# ==========================================================

def pearson_returns(returns_df):

    print("\nComputing Pearson correlation (Returns)...")

    numeric_df = returns_df.drop(columns=["Date"])

    corr = numeric_df.corr(method="pearson")

    corr.to_csv(RETURNS_CORR_FILE)

    print(f"Saved return correlation matrix to:\n{RETURNS_CORR_FILE}")

    return corr


# ==========================================================
# Brent Ranking
# ==========================================================

def brent_ranking(return_corr):

    print("\nRanking companies by Brent return correlation...")

    ranking = (
        return_corr["Brent"]
        .drop("Brent")
        .sort_values(ascending=False)
        .reset_index()
    )

    ranking.columns = ["Company", "Correlation_with_Brent"]

    ranking.to_csv(RANKING_FILE, index=False)

    print(f"Saved Brent ranking to:\n{RANKING_FILE}")

    return ranking


# ==========================================================
# Console Report
# ==========================================================

def print_report(summary, ranking):

    print("\n" + "=" * 60)
    print("STATISTICAL ANALYSIS REPORT")
    print("=" * 60)

    print("\nSummary Statistics")

    print(summary[["mean", "std", "min", "max"]])

    print("\nCorrelation of Daily Returns with Brent")

    print(ranking)

    print("\nMost Sensitive Company")

    print(
        f"{ranking.iloc[0]['Company']} "
        f"({ranking.iloc[0]['Correlation_with_Brent']:.3f})"
    )

    print("=" * 60)


# ==========================================================
# Main
# ==========================================================

def main():

    # Load data
    df = load_dataset()

    # Summary statistics
    summary = generate_summary(df)

    # Correlation using prices
    pearson_prices = pearson_correlation(df)

    # Spearman
    spearman = spearman_correlation(df)

    # Daily Returns
    returns = calculate_returns(df)

    # Correlation using returns
    pearson_returns_corr = pearson_returns(returns)

    # Rank companies using return correlation
    ranking = brent_ranking(pearson_returns_corr)

    # Print report
    print_report(summary, ranking)


if __name__ == "__main__":
    main()