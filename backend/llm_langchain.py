import os
from typing import Optional, Dict, Any


def get_openai_llm(model: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None):
    key = os.getenv("OPENAI_API_KEY")
    if key and hasattr(key, "isascii") and not key.isascii():
        raise ValueError("OPENAI_API_KEY contains non-ASCII characters; please provide a valid ASCII key.")
    from langchain_openai import ChatOpenAI
    params: Dict[str, Any] = {"model": model}
    if temperature is not None:
        params["temperature"] = float(temperature)
    if max_tokens is not None:
        params["max_tokens"] = int(max_tokens)
    return ChatOpenAI(**params)


def get_gemini_studio_llm(model: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None):
    # Uses Google AI Studio (Generative Language API)
    key = os.getenv("GOOGLE_API_KEY")
    if key and hasattr(key, "isascii") and not key.isascii():
        raise ValueError("GOOGLE_API_KEY contains non-ASCII characters; please provide a valid ASCII key.")
    from langchain_google_genai import ChatGoogleGenerativeAI
    params: Dict[str, Any] = {"model": model}
    if temperature is not None:
        params["temperature"] = float(temperature)
    if max_tokens is not None:
        params["max_output_tokens"] = int(max_tokens)
    # Requires GOOGLE_API_KEY in environment
    return ChatGoogleGenerativeAI(**params)


def get_gemini_vertex_llm(model: str, project: Optional[str] = None, location: Optional[str] = None,
                          temperature: Optional[float] = None, max_tokens: Optional[int] = None):
    # Uses Google Cloud Vertex AI
    from langchain_google_vertexai import ChatVertexAI
    params: Dict[str, Any] = {"model_name": model}
    if project:
        params["project"] = project
    if location:
        params["location"] = location
    if temperature is not None:
        params["temperature"] = float(temperature)
    if max_tokens is not None:
        params["max_output_tokens"] = int(max_tokens)
    return ChatVertexAI(**params)


def invoke_llm(provider: str, model: str, prompt: str, **kwargs) -> str:
    provider = (provider or "").lower()
    if provider in ("openai", "oai"):
        llm = get_openai_llm(model, kwargs.get("temperature"), kwargs.get("max_tokens"))
    elif provider in ("gemini_studio", "gemini", "google_genai", "google_ai_studio"):
        llm = get_gemini_studio_llm(model, kwargs.get("temperature"), kwargs.get("max_tokens"))
    elif provider in ("gemini_vertex", "vertex", "google_vertex"):
        llm = get_gemini_vertex_llm(
            model,
            kwargs.get("project") or os.getenv("GOOGLE_CLOUD_PROJECT"),
            kwargs.get("location") or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            kwargs.get("temperature"),
            kwargs.get("max_tokens"),
        )
    else:
        raise ValueError(f"Unknown provider '{provider}'. Expected one of: openai, gemini_studio, gemini_vertex")

    # Simple one-shot prompt
    result = llm.invoke(prompt)
    # Convert common LC output formats to plain string
    try:
        # ChatMessage with .content
        text = getattr(result, "content", None)
        if isinstance(text, str) and text:
            return text
    except Exception:
        pass
    return str(result)