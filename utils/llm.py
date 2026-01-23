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


def generate_text(prompt: str, temperature: float = 0.7, max_new_tokens: int = 3500) -> str:
    """
    Generate response using Llama 3.1 Instruct (chat style).
    
    IMPORTANT: Llama 3.1-8B has 8192 token context limit TOTAL (prompt + response).
    With optimized prompts (~1000 tokens), we have ~3500 tokens for response.
    """
    client = get_client()

    messages = [
        {
            "role": "system", 
            "content": "You are a professional travel planner. Always complete all sections fully."
        },
        {"role": "user", "content": prompt},
    ]

    try:
        response = client.chat.completions.create(
            messages=messages,
            temperature=temperature,
            max_tokens=max_new_tokens,
            stream=False
        )

        generated_text = response.choices[0].message["content"]

        finish_reason = getattr(response.choices[0], 'finish_reason', None)
        if finish_reason == "length":
            st.warning("⚠️ Response truncated. Try reducing trip days or simplifying prompt.")
        
        return generated_text
        
    except Exception as e:
        st.error(f"Error generating text: {str(e)}")
        raise