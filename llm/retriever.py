"""
retriever.py

Purpose
-------
Load all processed datasets required by the LLM.

This module DOES NOT call any LLM.
It only loads and returns data.
"""

from pathlib import Path
import pandas as pd
import json

# ==========================================================
# Paths
# ==========================================================

SCRIPT_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = SCRIPT_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"

PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

MASTER_DATASET = PROCESSED_DIR / "master_dataset.csv"
SUMMARY_STATS = PROCESSED_DIR / "summary_statistics.csv"
PEARSON = PROCESSED_DIR / "pearson_correlation.csv"
SPEARMAN = PROCESSED_DIR / "spearman_correlation.csv"
BRENT_RANKING = PROCESSED_DIR / "brent_ranking.csv"

HORMUZ_FILE = RAW_DIR / "hormuz_data.json"


# ==========================================================
# Load Master Dataset
# ==========================================================

def load_master_dataset():

    df = pd.read_csv(MASTER_DATASET)

    return df


# ==========================================================
# Load Summary Statistics
# ==========================================================

def load_summary_statistics():

    df = pd.read_csv(SUMMARY_STATS)

    return df


# ==========================================================
# Load Pearson Correlation
# ==========================================================

def load_pearson():

    df = pd.read_csv(PEARSON, index_col=0)

    return df


# ==========================================================
# Load Spearman Correlation
# ==========================================================

def load_spearman():

    df = pd.read_csv(SPEARMAN, index_col=0)

    return df


# ==========================================================
# Load Brent Ranking
# ==========================================================

def load_brent_ranking():

    df = pd.read_csv(BRENT_RANKING)

    return df


# ==========================================================
# Load Hormuz JSON
# ==========================================================

def load_hormuz():

    with open(HORMUZ_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


# ==========================================================
# Load Everything
# ==========================================================

def load_all():

    return {
        "master_dataset": load_master_dataset(),
        "summary_statistics": load_summary_statistics(),
        "pearson": load_pearson(),
        "spearman": load_spearman(),
        "ranking": load_brent_ranking(),
        "hormuz": load_hormuz()
    }


# ==========================================================
# Test
# ==========================================================

if __name__ == "__main__":

    data = load_all()

    print("\nDatasets Loaded Successfully\n")

    print("Master Dataset:")
    print(data["master_dataset"].head())

    print("\nRanking:")
    print(data["ranking"])

    print("\nHormuz Snapshot:")
    print(data["hormuz"])