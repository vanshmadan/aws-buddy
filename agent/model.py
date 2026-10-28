"""Which AI model is the agent's brain. Set MODEL_PROVIDER and MODEL_ID in your shell.

  MODEL_PROVIDER=gemini     + GEMINI_API_KEY     (Google, has a free tier)
  MODEL_PROVIDER=anthropic  + ANTHROPIC_API_KEY  (Claude API)
  MODEL_PROVIDER=bedrock    (default)            (Amazon Bedrock, uses the agent's AWS role)

MODEL_FALLBACKS (optional): comma-separated backup models, tried in order if the main one is
busy (free tiers return "503 high demand" or "429 quota" at busy times).
"""
import os

PROVIDER = os.environ.get("MODEL_PROVIDER", "bedrock")
MODEL_IDS = [os.environ["MODEL_ID"]] + [
    m.strip() for m in os.environ.get("MODEL_FALLBACKS", "").split(",") if m.strip()
]


def make_model(boto_session, model_id):
    if PROVIDER == "gemini":
        from google.genai import types
        from strands.models.gemini import GeminiModel
        return GeminiModel(
            client_args={
                "api_key": os.environ["GEMINI_API_KEY"],
                # fail in ~30 s with one retry, instead of silently retrying for minutes
                "http_options": types.HttpOptions(
                    timeout=30_000, retry_options=types.HttpRetryOptions(attempts=2)),
            },
            model_id=model_id, params={"temperature": 0})
    if PROVIDER == "anthropic":
        from strands.models.anthropic import AnthropicModel
        return AnthropicModel(client_args={"api_key": os.environ["ANTHROPIC_API_KEY"], "timeout": 30},
                              model_id=model_id, max_tokens=2048, params={"temperature": 0})
    from strands.models import BedrockModel
    return BedrockModel(model_id=model_id, boto_session=boto_session, temperature=0)


def is_busy_error(err):
    """True for 'try again later' errors (overloaded / rate limited / timed out)."""
    text = f"{type(err).__name__} {err}".lower()
    return any(k in text for k in ("503", "unavailable", "429", "resource_exhausted",
                                   "overloaded", "throttl", "timeout", "timed out"))
