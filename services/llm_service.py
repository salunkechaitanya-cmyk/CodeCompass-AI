
import os
import streamlit as st


def answer_repository_question(question, context):
    """
    Answer a question using repository context.
    Supports context as a dictionary, list, or string.
    """

    if not question or not str(question).strip():
        return "Please enter a question."

    if isinstance(context, dict):
        context_text = "\n\n".join(
            f"File: {path}\n{content}"
            for path, content in context.items()
        )
    elif isinstance(context, list):
        context_text = "\n\n".join(
            str(item) for item in context
        )
    elif isinstance(context, str):
        context_text = context
    else:
        context_text = ""

    if not context_text.strip():
        return (
            "No repository context was provided. "
            "Please analyze a repository and try again."
        )

    api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

    if not api_key:
        return (
            "Repository matches were found, but no AI API key is configured. "
            "Set OPENAI_API_KEY in your Streamlit secrets or environment."
        )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=(
                "You are CodeCompass, a beginner-friendly programming assistant. "
                "Answer questions using the supplied repository context. "
                "Explain technical concepts simply. If the context does not "
                "contain enough information, say so instead of inventing details."
            ),
            input=(
                f"User question:\n{question}\n\n"
                f"Repository context:\n{context_text[:20000]}"
            ),
        )

        return response.output_text

    except ImportError:
        return (
            "The OpenAI package is missing. Install it with: "
            "pip install openai"
        )
    except Exception as error:
        return f"AI answer failed: {error}"
