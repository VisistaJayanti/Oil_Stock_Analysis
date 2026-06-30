"""
visualization.py

Purpose
-------
Generate visualizations for Brent crude oil and Saudi petrochemical
company stock analysis.

Outputs
-------
figures/
    heatmap.png
    brent_trend.png
    company_trends.png
    brent_ranking.png
    scatter/
        SABIC.png
        Sipchem.png
        ...
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================================
# Paths
# ==========================================================

SCRIPT_DIR = Path(__file__).resolve().parent

PROCESSED_DIR = SCRIPT_DIR / "processed"

FIGURE_DIR = SCRIPT_DIR / "figures"
SCATTER_DIR = FIGURE_DIR / "scatter"

FIGURE_DIR.mkdir(parents=True, exist_ok=True)
SCATTER_DIR.mkdir(parents=True, exist_ok=True)

MASTER_FILE = PROCESSED_DIR / "master_dataset.csv"
PEARSON_FILE = PROCESSED_DIR / "pearson_correlation.csv"
RANKING_FILE = PROCESSED_DIR / "brent_ranking.csv"


# ==========================================================
# Load Data
# ==========================================================

def load_data():

    master = pd.read_csv(MASTER_FILE)
    pearson = pd.read_csv(PEARSON_FILE, index_col=0)
    ranking = pd.read_csv(RANKING_FILE)

    master["Date"] = pd.to_datetime(master["Date"])

    return master, pearson, ranking


# ==========================================================
# Heatmap
# ==========================================================

def plot_heatmap(corr):

    plt.figure(figsize=(10,8))

    plt.imshow(corr, aspect="auto")

    plt.colorbar(label="Correlation")

    plt.xticks(
        range(len(corr.columns)),
        corr.columns,
        rotation=45,
        ha="right"
    )

    plt.yticks(
        range(len(corr.columns)),
        corr.columns
    )

    plt.title("Pearson Correlation Matrix")

    plt.tight_layout()

    plt.savefig(
        FIGURE_DIR / "heatmap.png",
        dpi=300
    )

    plt.close()

    print("Saved heatmap.png")


# ==========================================================
# Brent Trend
# ==========================================================

def plot_brent(master):

    plt.figure(figsize=(12,5))

    plt.plot(
        master["Date"],
        master["Brent"],
        linewidth=2
    )

    plt.title("Brent Crude Oil Prices (2020-2026)")
    plt.xlabel("Date")
    plt.ylabel("USD / Barrel")

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        FIGURE_DIR / "brent_trend.png",
        dpi=300
    )

    plt.close()

    print("Saved brent_trend.png")


# ==========================================================
# Company Trends
# ==========================================================

def plot_companies(master):

    plt.figure(figsize=(15,7))

    companies = [
        c for c in master.columns
        if c not in ["Date", "Brent"]
    ]

    for company in companies:

        plt.plot(
            master["Date"],
            master[company],
            label=company,
            linewidth=1
        )

    plt.title("Saudi Petrochemical Company Stock Prices")

    plt.xlabel("Date")

    plt.ylabel("Closing Price")

    plt.legend(
        bbox_to_anchor=(1.02,1),
        loc="upper left"
    )

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        FIGURE_DIR / "company_trends.png",
        dpi=300
    )

    plt.close()

    print("Saved company_trends.png")


# ==========================================================
# Brent Ranking
# ==========================================================

def plot_ranking(ranking):

    plt.figure(figsize=(8,5))

    plt.barh(
        ranking["Company"],
        ranking["Correlation_with_Brent"]
    )

    plt.xlabel("Correlation with Brent")

    plt.title("Correlation with Brent Crude Oil")

    plt.tight_layout()

    plt.savefig(
        FIGURE_DIR / "brent_ranking.png",
        dpi=300
    )

    plt.close()

    print("Saved brent_ranking.png")


# ==========================================================
# Scatter Plots
# ==========================================================

def scatter_plots(master):

    companies = [
        c for c in master.columns
        if c not in ["Date","Brent"]
    ]

    for company in companies:

        plt.figure(figsize=(6,6))

        plt.scatter(
            master["Brent"],
            master[company],
            alpha=0.6
        )

        plt.xlabel("Brent Crude Price")

        plt.ylabel(company)

        plt.title(f"Brent vs {company}")

        plt.tight_layout()

        plt.savefig(
            SCATTER_DIR / f"{company}.png",
            dpi=300
        )

        plt.close()

    print("Saved scatter plots.")


# ==========================================================
# Rolling Correlation
# ==========================================================

def rolling_correlation(master):

    companies = [
        c for c in master.columns
        if c not in ["Date","Brent"]
    ]

    plt.figure(figsize=(15,6))

    for company in companies:

        rolling = master["Brent"].rolling(30).corr(
            master[company]
        )

        plt.plot(
            master["Date"],
            rolling,
            label=company
        )

    plt.title("30-Day Rolling Correlation with Brent")

    plt.xlabel("Date")

    plt.ylabel("Correlation")

    plt.legend(
        bbox_to_anchor=(1.02,1),
        loc="upper left"
    )

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        FIGURE_DIR / "rolling_correlation.png",
        dpi=300
    )

    plt.close()

    print("Saved rolling_correlation.png")


# ==========================================================
# Main
# ==========================================================

def main():

    master, pearson, ranking = load_data()

    plot_heatmap(pearson)

    plot_brent(master)

    plot_companies(master)

    plot_ranking(ranking)

    scatter_plots(master)

    rolling_correlation(master)

    print("\nVisualization Complete")


if __name__ == "__main__":
    main()