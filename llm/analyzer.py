"""
analyzer.py

Purpose
-------
Coordinates the complete AI pipeline.

Pipeline:
User Question
      │
      ▼
Retriever
      │
      ▼
Prompt Builder
      │
      ▼
LLM Client
      │
      ▼
Final Answer
"""

from llm.retriever import load_all
from llm.prompt import build_prompt
from llm.llm_client import ask_llm


class MarketAnalyzer:
    """
    Main analysis class that coordinates:
    - Data Retrieval
    - Prompt Building
    - LLM Response
    """

    def __init__(self):
        """Load project datasets once."""

        print("Loading project datasets...")

        self.data = load_all()

        print("Datasets loaded successfully.")

    def analyze(self, question: str) -> str:
        """
        Analyze a user's question.

        Parameters
        ----------
        question : str

        Returns
        -------
        str
        """

        # -------------------------------------
        # Build Prompt
        # -------------------------------------

        prompt = build_prompt(
            question=question,
            data=self.data
        )

        # -------------------------------------
        # Ask LLM
        # -------------------------------------

        response = ask_llm(prompt)

        return response

    def reload_data(self):
        """
        Reload datasets if they have changed.
        """

        self.data = load_all()

        print("Datasets reloaded.")


# ==========================================================
# Convenience Function
# ==========================================================

_analyzer = MarketAnalyzer()


def analyze(question: str):
    """
    Shortcut function used by Streamlit.

    Example:
        answer = analyze("Which company follows Brent?")
    """

    return _analyzer.analyze(question)


# ==========================================================
# CLI Testing
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("Saudi Petrochemical AI Assistant")
    print("=" * 60)

    while True:

        question = input("\nAsk a question ('exit' to quit): ")

        if question.lower() in ["exit", "quit"]:
            break

        print("\nThinking...\n")

        answer = analyze(question)

        print(answer)