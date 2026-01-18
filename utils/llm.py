import streamlit as st
from huggingface_hub import InferenceClient

MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"


@st.cache_resource
def get_client():
    """
    Create and cache the Hugging Face inference client.
    Reads token from Streamlit secrets.
    """
    token = st.secrets.get("HF_TOKEN", None)
    if not token:
        raise ValueError("HF_TOKEN not found in Streamlit secrets (.streamlit/secrets.toml).")

    return InferenceClient(model=MODEL_ID, token=token)


def generate_text(prompt: str, temperature: float = 0.7, max_new_tokens: int = 700) -> str:
    """
    Generate response using Llama 3.1 Instruct (chat style).
    """
    client = get_client()

    messages = [
        {"role": "system", "content": "You are a helpful travel planning assistant."},
        {"role": "user", "content": prompt},
    ]

    response = client.chat.completions.create(
        messages=messages,
        temperature=temperature,
        max_tokens=max_new_tokens
    )

    return response.choices[0].message["content"]
