
import os
import streamlit as st
from huggingface_hub import InferenceClient


def get_hf_token():
    """Read the Hugging Face token from Streamlit Secrets or environment."""
    try:
        token = st.secrets.get("HF_TOKEN", "")
    except Exception:
        token = ""

    return token or os.getenv("HF_TOKEN", "")


def answer_repository_question(question, context):
    """Answer a CodeCompass question using an open-weight model."""

    if not isinstance(question, str) or not question.strip():
        return "Please enter a question."

    if isinstance(context, dict):
        context_text = "\n\n".join(
            f"File: {path}\n{content}"
            for path, content in context.items()
        )
    elif isinstance(context, list):
        context_text = "\n\n".join(str(item) for item in context)
    elif isinstance(context, str):
        context_text = context
    else:
        context_text = ""

    if not context_text.strip():
        return (
            "No repository context was provided. "
            "Please analyze a repository and try again."
        )

    token = get_hf_token()

    if not token:
        return (
            "Hugging Face token not found. "
            "Add HF_TOKEN to Streamlit Secrets."
        )

    # A model served by a compatible Hugging Face inference provider.
    model = os.getenv(
        "HF_MODEL",
        "Qwen/Qwen2.5-Coder-7B-Instruct",
    )

    try:
        client = InferenceClient(
            model=model,
            token=token,
            timeout=60,
        )

        response = client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are CodeCompass, a beginner-friendly "
                        "programming assistant. Answer using the "
                        "provided repository context. Explain code "
                        "clearly. If the context is insufficient, "
                        "say so instead of inventing details."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Question:\n{question}\n\n"
                        f"Repository context:\n{context_text[:18000]}"
                    ),
                },
            ],
            max_tokens=700,
            temperature=0.2,
        )

        answer = response.choices[0].message.content

        if not answer:
            return "The model returned an empty answer. Please try again."

        return answer

    except Exception as error:
        return (
            "The Hugging Face model request failed. Check that your "
            "token has inference permissions and that the selected "
            "model is available through your inference provider. "
            f"Details: {error}"
        )
