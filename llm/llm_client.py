"""
llm_client.py

Purpose
-------
Communicates with the LLM.

This module ONLY sends prompts and receives responses.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# ==========================================
# Load API Key
# ==========================================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# ==========================================
# Ask LLM
# ==========================================

def ask_llm(prompt: str) -> str:
    """
    Send prompt to GPT and return response.

    Parameters
    ----------
    prompt : str

    Returns
    -------
    str
    """

    try:

        response = client.chat.completions.create(

            model="gpt-4.1",

            messages=[

                {
                    "role": "system",
                    "content":
                    (
                        "You are an expert financial analyst specializing "
                        "in Brent crude oil, Saudi petrochemical companies, "
                        "and geopolitical events affecting the energy market."
                    )
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            temperature=0.2,

            max_tokens=1000

        )

        return response.choices[0].message.content

    except Exception as e:

        return f"Error communicating with LLM:\n{e}"


# ==========================================
# Test
# ==========================================

if __name__ == "__main__":

    answer = ask_llm(
        "Which company has the highest correlation with Brent?"
    )

    print(answer)