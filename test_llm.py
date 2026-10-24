import streamlit as st
from services.llm_service import answer_repository_question

st.title("CodeCompass AI Connection Test")

if st.button("Test open-weight LLM"):
    with st.spinner("Asking the model..."):
        answer = answer_repository_question(
            question="What is a Python function? Explain simply.",
            context="Python functions are defined using the def keyword."
        )

    st.write(answer)