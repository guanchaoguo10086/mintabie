"""Memory manager — orchestrates memory injection into system prompts."""

from typing import Optional

from .store import format_user_profile, format_working_memory


class MemoryManager:
    """Manages memory injection into the agent's system prompt."""

    def __init__(self):
        self._last_user_profile_hash = ""
        self._last_working_memory_hash = ""

    def get_user_profile_text(self) -> str:
        text = format_user_profile()
        return text

    def get_working_memory_text(self) -> str:
        text = format_working_memory()
        return text

    def has_user_profile(self) -> bool:
        return bool(format_user_profile())

    def has_working_memory(self) -> bool:
        return bool(format_working_memory())

    def build_memory_section(self) -> str:
        parts = []
        up = self.get_user_profile_text()
        wm = self.get_working_memory_text()

        if up:
            parts.append(f"## About the User\n\n{up}")
        if wm:
            parts.append(f"## Working Memory\n\n{wm}")

        return "\n\n".join(parts
