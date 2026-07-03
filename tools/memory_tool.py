"""memory tool — LLM-callable tool for managing persistent memory."""

import json
import logging

from memory.store import (
    add_user_profile,
    add_working_memory,
    remove_user_profile,
    remove_working_memory,
    replace_user_profile,
    replace_working_memory,
    get_user_profile,
    get_working_memory,
)
from tools.registry import registry

logger = logging.getLogger(__name__)


def memory_tool(args: dict, **kw) -> str:
    """Manage memory entries."""
    action = args.get("action", "")
    target = args.get("target", "memory")
    content = args.get("content", "")
    old_text = args.get("old_text", "")

    try:
        if action == "add":
            if target == "user":
                add_user_profile(content)
            else:
                add_working_memory(content)
            return json.dumps({"success": True, "action": "add", "target": target})

        elif action == "remove":
            if target == "user":
                ok = remove_user_profile(old_text)
            else:
                ok = remove_working_memory(old_text)
            return json.dumps({"success": ok, "action": "remove", "target": target})

        elif action == "replace":
            if target == "user":
                ok = replace_user_profile(old_text, content)
            else:
                ok = replace_working_memory(old_text, content)
            return json.dumps({"success": ok, "action": "replace", "target": target})

        elif action == "list":
            if target == "user":
                entries = get_user_profile()
            else:
                entries = get_working_memory()
            return json.dumps({"entries": entries, "success": True})

        else:
            return json.dumps({"error": f"Unknown action: {action}", "success": False})

    except Exception as e:
        logger.exception("memory_tool failed")
        return json.dumps({"error": str(e), "success": False})


registry.register(
    name="memory",
    description="Manage persistent memory (user profile + working memory)",
    schema={
        "name": "memory",
        "description": "Save, update, or retrieve persistent memory across sessions",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "remove", "replace", "list"],
                    "description": "What to do",
                },
                "target": {
                    "type": "string",
                    "enum": ["user", "memory"],
                    "description": "'user' for preferences, 'memory' for environment facts",
                },
                "content": {"type": "string", "description": "Content to save (for add/replace)"},
                "old_text": {"type": "string", "description": "Text to identify entry (for remove/replace)"},
            },
            "required": ["action"],
        },
    },
    handler=memory_tool,
    toolset="memory",
    emoji="🧠",
)
