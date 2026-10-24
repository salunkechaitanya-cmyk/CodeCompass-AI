
import streamlit as st
from google import genai


def answer_repository_question(question, context):
    """Answer a question using Gemini and repository context."""

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        raise ValueError(
            "GEMINI_API_KEY is missing. Add it in Streamlit Cloud Secrets."
        )

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is empty. Check your Streamlit Secrets."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are CodeCompass AI, a friendly coding assistant for beginners.

Answer the user's question using the supplied repository context.

Rules:
- Explain technical ideas in simple language.
- Use code examples when helpful.
- If the context does not contain the answer, say so honestly.
- Never pretend you inspected files that were not provided.
- Do not invent repository features.

REPOSITORY CONTEXT:
{context}

USER QUESTION:
{question}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )

        answer = response.text

        if not answer:
            return "Gemini returned an empty answer. Please try again."

        return answer

    except Exception as error:
        raise ValueError(
            f"Gemini could not generate an answer: {error}"
        ) from error
