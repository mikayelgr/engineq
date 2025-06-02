from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from internal.conf import Config


def decide_llm():
    """Decides which LLM to use based on the configuration."""

    return OpenAIModel(
        "gpt-4o-mini" if not Config().OLLAMA_MODEL_NAME else Config().OLLAMA_MODEL_NAME,
        provider=OpenAIProvider(base_url=Config().OLLAMA_API_URL if Config().OLLAMA_API_URL else None),
    )
