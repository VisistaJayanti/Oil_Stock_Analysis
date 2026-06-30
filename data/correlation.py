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
# Pearson Correlation
# ==========================================================

def pearson_correlation(df):

    print("\nComputing Pearson correlation...")

    numeric_df = df.drop(columns=["Date"])

    pearson = numeric_df.corr(method="pearson")

    pearson.to_csv(PEARSON_FILE)

    print(f"Saved Pearson correlation matrix to:\n{PEARSON_FILE}")

    return pearson


# ==========================================================
# Spearman Correlation
# ==========================================================

def spearman_correlation(df):

    print("\nComputing Spearman correlation...")

    numeric_df = df.drop(columns=["Date"])

    spearman = numeric_df.corr(method="spearman")

    spearman.to_csv(SPEARMAN_FILE)

    print(f"Saved Spearman correlation matrix to:\n{SPEARMAN_FILE}")

    return spearman


# ==========================================================
# Brent Ranking
# ==========================================================

def brent_ranking(pearson):

    print("\nRanking companies by Brent correlation...")

    ranking = (
        pearson["Brent"]
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

    print("\nCompany Correlation with Brent")

    print(ranking)

    print("\nMost Correlated Company")

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

    # Pearson correlation
    pearson = pearson_correlation(df)

    # Spearman correlation
    spearman = spearman_correlation(df)

    # Rank companies
    ranking = brent_ranking(pearson)

    # Console report
    print_report(summary, ranking)


if __name__ == "__main__":
    main()