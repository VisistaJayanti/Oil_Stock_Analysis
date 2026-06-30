"""
prompt_builder.py

Purpose
-------
Builds the prompt that will be sent to the LLM.

This module does NOT call the LLM.
It only prepares the context.
"""

import json


def build_prompt(question: str, data: dict) -> str:
    """
    Builds a prompt for the LLM.

    Parameters
    ----------
    question : str
        User's question.

    data : dict
        Dictionary returned by retriever.load_all()

    Returns
    -------
    str
        Prompt ready to send to the LLM.
    """

    master = data["master_dataset"]
    ranking = data["ranking"]
    summary = data["summary_statistics"]
    pearson = data["pearson"]
    hormuz = data["hormuz"]

    # --------------------------------------------------
    # Latest Market Data
    # --------------------------------------------------

    latest = master.iloc[-1]

    latest_brent = latest["Brent"]

    latest_stocks = latest.drop(["Date", "Brent"]).to_dict()

    # --------------------------------------------------
    # Top Correlated Companies
    # --------------------------------------------------

    top3 = ranking.head(3)

    top3_text = "\n".join(
        [
            f"- {row['Company']}: {row.iloc[1]:.3f}"
            for _, row in top3.iterrows()
        ]
    )

    # --------------------------------------------------
    # Summary Statistics
    # --------------------------------------------------

    summary_text = summary.to_string(index=False)

    # --------------------------------------------------
    # Pearson Correlation Matrix
    # --------------------------------------------------

    pearson_text = pearson.round(2).to_string()

    # --------------------------------------------------
    # Hormuz Snapshot
    # --------------------------------------------------

    hormuz_text = json.dumps(
        hormuz,
        indent=2
    )

    # --------------------------------------------------
    # Latest Stock Prices
    # --------------------------------------------------

    stock_text = "\n".join(
        [
            f"{company}: {price:.2f}"
            for company, price in latest_stocks.items()
        ]
    )

    # --------------------------------------------------
    # Final Prompt
    # --------------------------------------------------

    prompt = f"""
You are an AI financial analyst specializing in
Saudi Arabian petrochemical companies.

You are provided with:

1. Historical Brent crude oil prices (2020–2026)

2. Historical stock prices for:

- Advanced Petrochemical
- Petro Rabigh
- SABIC
- Saudi Chemical
- Saudi Kayan
- Sipchem
- Tasnee
- Yansab

3. Pearson correlation analysis

4. Summary statistics

5. Latest Strait of Hormuz snapshot

Your role is to answer questions ONLY using the provided data.

If the information is unavailable,
say that it is unavailable rather than making assumptions.

Never fabricate financial information.

--------------------------------------------------
LATEST BRENT PRICE
--------------------------------------------------

{latest_brent:.2f}

--------------------------------------------------
LATEST STOCK PRICES
--------------------------------------------------

{stock_text}

--------------------------------------------------
TOP BRENT CORRELATIONS
--------------------------------------------------

{top3_text}

--------------------------------------------------
SUMMARY STATISTICS
--------------------------------------------------

{summary_text}

--------------------------------------------------
PEARSON CORRELATION MATRIX
--------------------------------------------------

{pearson_text}

--------------------------------------------------
LATEST HORMUZ SNAPSHOT
--------------------------------------------------

{hormuz_text}

--------------------------------------------------
USER QUESTION
--------------------------------------------------

{question}

Provide:

1. A concise answer.

2. Explain your reasoning using the provided data.

3. Mention uncertainty whenever appropriate.

Avoid making investment recommendations.
"""

    return prompt


# ======================================================
# Test
# ======================================================

if __name__ == "__main__":

    from llm.retriever import load_all

    data = load_all()

    prompt = build_prompt(
        question="Which company is most sensitive to Brent?",
        data=data
    )

    print(prompt)