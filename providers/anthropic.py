"""Anthropic provider for Mintabie."""

import json
import logging
from typing import Dict, List, Optional

import httpx

from .base import BaseProvider, ChatResult

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic's Messages API."""

    def __init__(self, model: str, api_key: str = "", base_url: str = ""):
        super().__init__(model, api_key, base_url)
        if not base_url:
            self.base_url = ANTHROPIC_API_URL

    @property
    def name(self) -> str:
        return "anthropic"

    def check_available(self) -> bool:
        return bool(self.api_key)

    def chat(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        system_prompt: str = "",
        stream: bool = False,
        max_tokens: int = 4096,
    ) -> ChatResult:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        # Convert OpenAI-format messages to Anthropic format
        anthropic_messages = []
        for m in messages:
            role = m["role"]
            if role == "system":
                continue
            if role == "tool":
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": m.get("tool_call_id", ""),
                        "content": m.get("content", ""),
                    }],
                })
            else:
                content = m.get("content", "")
                tc = m.get("tool_calls")
                if tc:
                    content_blocks = [{"type": "text", "text": content or ""}]
                    for t in tc:
                        fn = t.get("function", {})
                        content_blocks.append({
                            "type": "tool_use",
                            "id": t["id"],
                            "name": fn.get("name", ""),
                            "input": json.loads(fn.get("arguments", "{}")),
                        })
                    anthropic_messages.append({"role": role, "content": content_blocks})
                else:
                    anthropic_messages.append({"role": role, "content": content})

        body = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
        }

        if system_prompt:
            body["system"] = system_prompt

        if tools:
            anthropic_tools = []
            for t in tools:
                anthropic_tools.append({
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "input_schema": t["function"]["parameters"],
                })
            body["tools"] = anthropic_tools

        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(self.base_url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()

            content_blocks = data.get("content", [])
            text = ""
            tool_calls = []
            for block in content_blocks:
                if block.get("type") == "text":
                    text = block.get("text", "")
                elif block.get("type") == "tool_use":
                    tool_calls.append({
                        "id": block["id"],
                        "type": "function",
                        "function": {
                            "name": block["name"],
                            "arguments": json.dumps(block.get("input", {})),
                        },
                    })

            usage = data.get("usage", {})
            return ChatResult(
                content=text,
                tool_calls=tool_calls if tool_calls else None,
                finish_reason=data.get("stop_reason", ""),
                usage=usage,
                model=data.get("model", self.model),
                success=True,
            )
        except Exception as e:
            logger.exception("Anthropic provider failed")
            return ChatResult(error=str(e), success=False)
