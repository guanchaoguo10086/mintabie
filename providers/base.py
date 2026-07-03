"""Base provider interface for Mintabie."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ChatResult:
    """Result of a chat completion call."""
    content: str = ""
    tool_calls: Optional[List[Dict]] = None
    finish_reason: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    model: str = ""
    success: bool = True
    error: str = ""


class BaseProvider:
    """Abstract base class for LLM providers."""

    def __init__(self, model: str, api_key: str = "", base_url: str = ""):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    @property
    def name(self) -> str:
        """Provider name (e.g. 'openai', 'anthropic')."""
        raise NotImplementedError

    def chat(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        system_prompt: str = "",
        stream: bool = False,
        max_tokens: int = 4096,
    ) -> ChatResult:
        """Send a chat completion request. Override in subclass."""
        raise NotImplementedError

    def check_available(self) -> bool:
        """Check if this provider is usable (has API key, etc.)."""
        return bool(self.api_key
