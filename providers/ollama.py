"""Ollama provider for Mintabie."""

from .base import BaseProvider
from .openai import OpenAIProvider


class OllamaProvider(OpenAIProvider):
    """Provider for Ollama local models (OpenAI-compatible)."""

    def __init__(self, model: str, api_key: str = "", base_url: str = ""):
        if not base_url:
            base_url = "http://localhost:11434/v1"
        super().__init__(model, api_key, base_url)

    @property
    def name(self) -> str:
        return "ollama"

    def check_available(self) -> bool:
        """Ollama doesn't need an API key."""
        return True
