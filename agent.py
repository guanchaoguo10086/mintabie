"""AIAgent — Mintabie's core conversation loop.

Orchestrates system prompt → LLM call → tool dispatch → result loop.
"""

import json
import logging
import os
import time
import uuid
from typing import Optional

import httpx

from config import MINTABIE_HOME, load_config
from memory.manager import MemoryManager
from prompt_builder import build_system_prompt
from session_store import SessionDB
from tool_registry import registry
from tools.skill_manager_tool import get_skills_list

logger = logging.getLogger(__name__)

# Default API endpoint
DEFAULT_BASE_URL = "http://10.217.21.87:8000/v1"


class AIAgent:
    """Core agent loop: system prompt → LLM → tools → loop."""

    def __init__(
        self,
        model: str = "gpt-4o",
        base_url: str = "",
        api_key: str = "",
        provider_name: str = "",
        session_id: str = "",
        session_db: Optional[SessionDB] = None,
        quiet_mode: bool = False,
        enabled_toolsets: set[str] | None = None,
    ):
        self.model = model
        self.base_url = base_url or DEFAULT_BASE_URL
        self.api_key = api_key
        self.provider_name = provider_name
        self.session_id = session_id or str(uuid.uuid4())
        self.session_db = session_db
        self.quiet_mode = quiet_mode
        self.enabled_toolsets = enabled_toolsets
        self._cached_system_prompt: str | None = None
        self._memory_manager = MemoryManager()
        self._iteration_count = 0
        self._cfg = load_config()

        # Resolve endpoint
        self._resolve_api_endpoint()

        # Ensure session exists in DB
        if self.session_db:
            self.session_db.create_session(self.session_id)

    def _resolve_api_endpoint(self) -> None:
        """Resolve the API endpoint based on config and env."""
        cfg = self._cfg
        # Try provider-specific base URL
        provider = self.provider_name or cfg["model"].get("provider", "")
        if provider and provider != "openai":
            providers_cfg = cfg.get("providers", {})
            pcfg = providers_cfg.get(provider, {})
            if pcfg.get("base_url"):
                self.base_url = pcfg["base_url"]
            if pcfg.get("api_key"):
                self.api_key = pcfg["api_key"]

        # Environment variable overrides
        if os.environ.get("OPENAI_BASE_URL"):
            self.base_url = os.environ["OPENAI_BASE_URL"]
        if os.environ.get("OPENAI_API_KEY"):
            self.api_key = os.environ["OPENAI_API_KEY"]

        # Ensure URL ends with /chat/completions
        self.api_url = self.base_url.rstrip("/")
        if not self.api_url.endswith("/chat/completions"):
            self.api_url = self.api_url.rstrip("/") + "/chat/completions"

    def switch_provider(self, provider_name: str, model: str = "") -> str:
        """Switch to a different provider. Returns status message."""
        cfg = self._cfg
        providers_cfg = cfg.get("providers", {})
        pcfg = providers_cfg.get(provider_name)
        if not pcfg:
            return f"Unknown provider: {provider_name}"

        self.provider_name = provider_name
        if model:
            self.model = model
        if pcfg.get("base_url"):
            self.base_url = pcfg["base_url"]
        if pcfg.get("api_key"):
            self.api_key = pcfg["api_key"]

        self._resolve_api_endpoint()
        self._cached_system_prompt = None
        return f"Switched to provider '{provider_name}' with model '{self.model}'"

    def _build_system_prompt(self, skills: list[str] | None = None) -> str:
        """Build or return cached system prompt."""
        if self._cached_system_prompt:
            return self._cached_system_prompt

        memory_text = self._memory_manager.build_memory_section()
        skills_list = get_skills_list() if skills is None else skills
        skill_names = [s["name"] for s in skills_list] if skills_list else []

        prompt = build_system_prompt(
            skills=skill_names,
            memory=memory_text,
        )
        self._cached_system_prompt = prompt
        return prompt

    def run_conversation(
        self,
        user_message: str,
        conversation_history: list | None = None,
    ) -> dict:
        """Run a full conversation turn.

        Returns: {
            "response": str,
            "messages": list (full message history for next turn),
            "iterations": int,
        }
        """
        messages = list(conversation_history) if conversation_history else []
        system_prompt = self._build_system_prompt()
        self._iteration_count = 0
        max_iterations = self._cfg["agent"]["max_iterations"]
        tool_delay = self._cfg["agent"]["tool_delay"]

        # Add user message
        messages.append({"role": "user", "content": user_message})

        # Save to DB
        if self.session_db:
            self.session_db.add_message(self.session_id, "user", user_message)

        # Main loop
        while self._iteration_count < max_iterations:
            self._iteration_count += 1

            # Call LLM
            response = self._call_llm(system_prompt, messages)
            if response is None:
                return {
                    "response": "Error: LLM call failed",
                    "messages": messages,
                    "iterations": self._iteration_count,
                }

            msg = response["choices"][0]["message"]
            assistant_msg = {"role": "assistant", "content": msg.get("content")}

            # Check for tool calls
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                # Text response — done
                assistant_msg["content"] = assistant_msg["content"] or ""
                messages.append(assistant_msg)

                if self.session_db:
                    self.session_db.add_message(
                        self.session_id, "assistant", assistant_msg["content"]
                    )
                return {
                    "response": assistant_msg["content"],
                    "messages": messages,
                    "iterations": self._iteration_count,
                }

            # Has tool calls
            assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)

            if self.session_db:
                self.session_db.add_message(
                    self.session_id,
                    "assistant",
                    assistant_msg["content"],
                    tool_calls=[
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": tc["function"],
                        }
                        for tc in tool_calls
                    ],
                )

            # Execute each tool call
            for tc in tool_calls:
                func_name = tc["function"]["name"]
                try:
                    func_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    func_args = {}

                result = registry.dispatch(func_name, func_args, task_id=tc["id"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

                if self.session_db:
                    self.session_db.add_message(
                        self.session_id,
                        "tool",
                        result,
                        tool_call_id=tc["id"],
                        name=func_name,
                    )

                if tool_delay > 0:
                    time.sleep(tool_delay)

        # Max iterations reached
        return {
            "response": "Max iterations reached.",
            "messages": messages,
            "iterations": self._iteration_count,
        }

    def _call_llm(self, system_prompt: str, messages: list) -> dict | None:
        """Call the LLM API and return the response."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        tool_defs = registry.get_definitions(self.enabled_toolsets)

        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "max_tokens": self._cfg["model"]["max_tokens"],
        }
        if tool_defs:
            body["tools"] = tool_defs
            body["tool_choice"] = "auto"

        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(self.api_url, headers=headers, json=body)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM call HTTP error: {e.response.status_code} {e.response.text[:500]}")
            return None
        except httpx.TimeoutException:
            logger.error("LLM call timed out")
            return None
        except Exception as e:
            logger.exception(f"LLM call failed: {e}")
            return None

    def close(self):
        """Clean up resources."""
        if self.session_db:
            self.session_db.close()
