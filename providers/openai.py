"""OpenAI-compatible provider for Mintabie."""

import json
import logging
from typing import Dict, List, Optional

import httpx

from .base import BaseProvider, ChatResult

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI-compatible API endpoints."""

    @property
    def name(self) -> str:
        return "openai"

    def chat(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        system_prompt: str = "",
        stream: bool = False,
        max_tokens: int = 4096,
    ) -> ChatResult:
        url = self.base_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url += "/chat/completions"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()

            choice = data["choices"][0]
            msg = choice["message"]
            usage = data.get("usage", {})

            return ChatResult(
                content=msg.get("content") or "",
                tool_calls=msg.get("tool_calls"),
                finish_reason=choice.get("finish_reason", ""),
                usage=usage,
                model=data.get("model", self.model),
                success=True,
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API error: {e.response.status_code} {e.response.text[:500]}")
            return ChatResult(error=f"HTTP {e.response.status_code}", success=False)
        except httpx.TimeoutException:
            return ChatResult(error="Request timed out", success=False)
        except Exception as e:
            logger.exception("OpenAI provider failed")
            return ChatResult(error=str(e), success=False)
