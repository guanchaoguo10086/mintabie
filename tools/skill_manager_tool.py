"""Skill manager tool stub for Mintabie."""

import json
import os
from pathlib import Path

from config import MINTABIE_HOME
from tools.registry import registry

SKILLS_DIR = MINTABIE_HOME / "skills"


def get_skills_list() -> list[dict]:
    """Return list of installed skills with name, path, description."""
    if not SKILLS_DIR.exists():
        return []

    skills = []
    for fpath in sorted(SKILLS_DIR.iterdir()):
        if fpath.suffix in (".md", ".skill.md") and fpath.is_file():
            name = fpath.stem.replace(".skill", "")
            desc = ""
            try:
                content = fpath.read_text(encoding="utf-8")
                if content.startswith("---"):
                    import yaml
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        meta = yaml.safe_load(parts[1]) or {}
                        name = meta.get("name", name)
                        desc = meta.get("description", "")
            except Exception:
                pass
            skills.append({"name": name, "path": str(fpath), "description": desc})
    return skills


def skill_view(args: dict, **kw) -> str:
    """View a skill's content."""
    name = args.get("name", "")
    if not name:
        return json.dumps({"error": "No skill name provided", "success": False})

    skills = get_skills_list()
    for s in skills:
        if s["name"] == name:
            try:
                content = Path(s["path"]).read_text(encoding="utf-8")
                return json.dumps({"content": content, "success": True})
            except Exception as e:
                return json.dumps({"error": str(e), "success": False})

    return json.dumps({"error": f"Skill not found: {name}", "success": False})


def skills_list(args: dict, **kw) -> str:
    """List all available skills."""
    skills = get_skills_list()
    return json.dumps({"skills": skills, "success": True})


registry.register(
    name="skill_view",
    description="View a skill's full content",
    schema={
        "name": "skill_view",
        "description": "Load a skill's full content",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Skill name to load"},
            },
            "required": ["name"],
        },
    },
    handler=skill_view,
    toolset="skills",
    emoji="📚",
)

registry.register(
    name="skills_list",
    description="List installed skills",
    schema={
        "name": "skills_list",
        "description": "List available skills",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Optional category filter"},
            },
            "required": [],
        },
    },
    handler=skills_list,
    toolset="skills",
    emoji="📋",
)
