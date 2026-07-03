"""Central tool registry for Mintabie agent.

Tools self-register via `registry.register()` at import time.
"""

import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Holds tool definitions with name, schema, handler, and metadata."""

    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(
        self,
        name: str,
        schema: dict,
        handler: callable,
        toolset: str = "core",
        emoji: str = "⚡",
        check_fn: callable = None,
        requires_env: list[str] = None,
        description: str = "",
    ) -> None:
        """Register a tool.

        Args:
            name: Tool name (used by LLM).
            schema: OpenAI-format function schema.
            handler: Callable(args: dict, **kw) -> str.
            toolset: Group name.
            emoji: Display emoji.
            check_fn: Callable() -> bool; if returns False, tool is hidden.
            requires_env: List of env var names this tool needs.
            description: Human-readable description.
        """
        if name in self._tools:
            logger.warning(f"Tool '{name}' already registered, overwriting")
        self._tools[name] = {
            "name": name,
            "schema": schema,
            "handler": handler,
            "toolset": toolset,
            "emoji": emoji,
            "check_fn": check_fn,
            "requires_env": requires_env or [],
            "description": description or schema.get("description", ""),
        }

    def get(self, name: str) -> dict | None:
        return self._tools.get(name)

    def get_all(self) -> dict[str, dict]:
        return dict(self._tools)

    def get_definitions(self, enabled_toolsets: set[str] | None = None) -> list[dict]:
        """Return OpenAI-format tool definitions, optionally filtered by toolsets.
        
        Returns tools in the format: {"type": "function", "function": {...}}
        """
        result = []
        for name, tool in self._tools.items():
            if enabled_toolsets and tool["toolset"] not in enabled_toolsets:
                continue
            if tool["check_fn"] and not tool["check_fn"]():
                continue
            # Wrap in OpenAI function format
            result.append({
                "type": "function",
                "function": tool["schema"],
            })
        return result

    def get_emoji(self, name: str, default: str = "⚡") -> str:
        tool = self._tools.get(name)
        return tool["emoji"] if tool else default

    def dispatch(self, name: str, args: dict, **kw) -> str:
        """Execute a tool by name with given args."""
        tool = self._tools.get(name)
        if not tool:
            return f'{{"error": "Unknown tool: {name}", "success": false}}'
        try:
            return tool["handler"](args, **kw)
        except Exception as e:
            logger.exception(f"Tool '{name}' failed")
            return f'{{"error": "{e}", "success": false}}'

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)


# Global singleton
registry = ToolRegistry()
