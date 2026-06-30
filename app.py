"""
app.py

Saudi Petrochemical Market Intelligence Dashboard

Run:
streamlit run app.py
"""

from pathlib import Path
import json
import pandas as pd
import streamlit as st

from llm.analyzer import analyze

# =====================================================
# Configuration
# =====================================================

st.set_page_config(
    page_title="Petrochemical Stock Analyzer",
    page_icon="📈",
    layout="wide"
)

# =====================================================
# Paths
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

PROCESSED = BASE_DIR / "data" / "processed"
RAW = BASE_DIR / "data" / "raw"
FIGURES = BASE_DIR / "data" / "figures"

MASTER = PROCESSED / "master_dataset.csv"
RANKING = PROCESSED / "brent_ranking.csv"
SUMMARY = PROCESSED / "summary_statistics.csv"

HORMUZ = RAW / "hormuz_data.json"

# =====================================================
# Load Data
# =====================================================

@st.cache_data
def load_data():

    master = pd.read_csv(MASTER)

    ranking = pd.read_csv(RANKING)

    summary = pd.read_csv(SUMMARY)

    with open(HORMUZ, "r", encoding="utf-8") as f:
        hormuz = json.load(f)

    return master, ranking, summary, hormuz


master, ranking, summary, hormuz = load_data()

# =====================================================
# Sidebar
# =====================================================

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "",
    [
        "Dashboard",
        "Correlation",
        "Visualizations",
        "Hormuz Strait Status",
        "AI Market Assistant"
    ]
)

# =====================================================
# Dashboard
# =====================================================

if page == "Dashboard":

    st.title("Petrochemical Stock Analyzer")

    st.markdown(
        """
This dashboard analyzes the relationship between

- Brent Crude Oil
- Saudi Petrochemical Companies
- Strait of Hormuz
- AI Financial Analysis
"""
    )

    latest = master.iloc[-1]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Latest Brent Price",
            f"${latest['Brent']:.2f}"
        )

    with col2:
        st.metric(
            "Companies",
            len(master.columns)-2
        )

    with col3:
        st.metric(
            "Highest Correlation",
            ranking.iloc[0]["Company"]
        )

    st.divider()

    st.subheader("Top Brent Correlations")

    st.dataframe(ranking)

# =====================================================
# Correlation
# =====================================================

elif page == "Correlation Analysis":

    st.title("Correlation Analysis")

    st.write("Pearson ranking between Brent crude oil and Saudi petrochemical companies.")

    st.dataframe(ranking)

    st.subheader("Summary Statistics")

    st.dataframe(summary)

# =====================================================
# Visualizations
# =====================================================

elif page == "Visualizations":

    st.title("Visualizations")

    st.subheader("Correlation Heatmap")

    st.image(FIGURES / "heatmap.png")

    st.subheader("Brent Price Trend")

    st.image(FIGURES / "brent_trend.png")

    st.subheader("Company Stock Trends")

    st.image(FIGURES / "company_trends.png")

    st.subheader("Correlation Ranking")

    st.image(FIGURES / "brent_ranking.png")

    st.subheader("Rolling Correlation")

    st.image(FIGURES / "rolling_correlation.png")

# =====================================================
# Hormuz
# =====================================================

elif page == "Strait of Hormuz":

    st.title("Strait of Hormuz Status")

    st.json(hormuz)

# =====================================================
# AI
# =====================================================

elif page == "AI Market Assistant":

    st.title("AI Financial Analyst")

    st.markdown(
        """
Ask questions such as:

- Which company is most correlated with Brent?

- Compare SABIC and Sipchem.

- Explain today's Hormuz situation.

- Summarize the Saudi petrochemical market.

- Which company appears least sensitive to oil prices?
"""
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input(
        "Ask about Brent, stocks or Hormuz..."
    )

    if question:

        st.session_state.messages.append(
            {
                "role":"user",
                "content":question
            }
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):

            with st.spinner("Analyzing market..."):

                answer = analyze(question)

                st.markdown(answer)

        st.session_state.messages.append(
            {
                "role":"assistant",
                "content":answer
            }
        )