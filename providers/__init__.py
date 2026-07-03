"""Provider abstractions for Mintabie."""

from .base import BaseProvider, ChatResult
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .ollama import OllamaProvider

__all__ = ["BaseProvider", "ChatResult", "OpenAIProvider", "AnthropicProvider", "OllamaProvider", "create_provider"]


def create_provider(name: str, model: str, api_key: str = "", base_url: str = "") -> BaseProvider:
    """Factory: create a provider by name."""
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
    }
    cls = providers.get(name)
    if not cls:
        raise ValueError(f"Unknown provider: {name}. Available: {list(providers.keys())}")
    return cls(model=model, api_key=api_key, base_url=base_url)
