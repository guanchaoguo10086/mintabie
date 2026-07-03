"""patch tool — targeted find-and-replace edits."""

import json
import os

from tools.registry import registry


def patch_file(args: dict, **kw) -> str:
    """Find and replace text in a file."""
    path = args.get("path", "")
    old_string = args.get("old_string", "")
    new_string = args.get("new_string", "")
    replace_all = args.get("replace_all", False)

    if not path or not old_string:
        return json.dumps({"error": "path and old_string are required", "success": False})

    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        return json.dumps({"error": f"File not found: {path}", "success": False})

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if replace_all:
            new_content = content.replace(old_string, new_string)
        else:
            # Single replacement
            count = content.count(old_string)
            if count == 0:
                return json.dumps({"error": "old_string not found in file", "success": False})
            if count > 1:
                return json.dumps({
                    "error": f"Found {count} matches. Use replace_all=True or provide more context",
                    "success": False,
                })
            new_content = content.replace(old_string, new_string, 1)

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return json.dumps({"success": True, "path": path})
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


registry.register(
    name="patch",
    description="Find and replace text in a file",
    schema={
        "name": "patch",
        "description": "Make targeted find-and-replace edits in a file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "old_string": {"type": "string", "description": "Text to find"},
                "new_string": {"type": "string", "description": "Replacement text"},
                "replace_all": {"type": "boolean", "description": "Replace all occurrences", "default": False},
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    handler=patch_file,
    toolset="core",
    emoji="🔧",
)
