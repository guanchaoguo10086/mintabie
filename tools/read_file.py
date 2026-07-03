"""read_file tool — read file contents with line numbers."""

import json
import os

from tools.registry import registry


def read_file(args: dict, **kw) -> str:
    """Read a file and return its contents with line numbers."""
    path = args.get("path", "")
    offset = args.get("offset", 1)
    limit = args.get("limit", 500)

    if not path:
        return json.dumps({"error": "No path provided", "success": False})

    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        return json.dumps({"error": f"File not found: {path}", "success": False})

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total = len(lines)
        start = max(0, offset - 1)
        end = min(total, start + limit)
        content = "".join(lines[start:end])

        return json.dumps({
            "content": content,
            "total_lines": total,
            "offset": offset,
            "success": True,
        })
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


registry.register(
    name="read_file",
    description="Read a file with line numbers",
    schema={
        "name": "read_file",
        "description": "Read a file and return its contents",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "offset": {"type": "integer", "description": "Starting line number (1-indexed)", "default": 1},
                "limit": {"type": "integer", "description": "Maximum lines to return", "default": 500},
            },
            "required": ["path"],
        },
    },
    handler=read_file,
    toolset="core",
    emoji="📖",
)
