"""write_file tool — create or overwrite files."""

import json
import os

from tools.registry import registry


def write_file(args: dict, **kw) -> str:
    """Write content to a file."""
    path = args.get("path", "")
    content = args.get("content", "")

    if not path:
        return json.dumps({"error": "No path provided", "success": False})

    path = os.path.expanduser(path)
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return json.dumps({"success": True, "path": path})
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


registry.register(
    name="write_file",
    description="Write content to a file (creates parent directories)",
    schema={
        "name": "write_file",
        "description": "Create a new file or overwrite an existing one",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    handler=write_file,
    toolset="core",
    emoji="✏️",
)
