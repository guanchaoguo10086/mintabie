"""Skill manager — loads skills from ~/.mintabie/skills/ and provides them for injection."""

import logging
from pathlib import Path

from config import MINTABIE_HOME

logger = logging.getLogger(__name__)

SKILLS_DIR = MINTABIE_HOME / "skills"


def ensure_skills_dir() -> None:
    """Create the skills directory if it doesn't exist."""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)


def load_skill_names() -> list[str]:
    """Return a list of skill names from the skills directory."""
    if not SKILLS_DIR.exists():
        return []

    names = []
    for fpath in sorted(SKILLS_DIR.iterdir()):
        if fpath.suffix in (".md", ".skill.md") and fpath.is_file():
            name = fpath.stem.replace(".skill", "")
            try:
                content = fpath.read_text(encoding="utf-8")
                if content.startswith("---"):
                    import yaml
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        meta = yaml.safe_load(parts[1]) or {}
                        name = meta.get("name", name)
            except Exception:
                pass
            names.append(name)
    return names


def load_skill_content(name: str) -> str:
    """Load the full content of a skill by name."""
    if not SKILLS_DIR.exists():
        return ""

    for fpath in SKILLS_DIR.iterdir():
        if fpath.suffix in (".md", ".skill.md") and fpath.is_file():
            fname = fpath.stem.replace(".skill", "")
            if fname == name:
                return fpath.read_text(encoding="utf-8")
    return ""


def create_example_skill() -> None:
    """Create an example skill if none exist."""
    ensure_skills_dir()
    if not list(SKILLS_DIR.iterdir()):
        example = SKILLS_DIR / "example.skill.md"
        example.write_text(
            """---
name: example
description: "A simple example skill demonstrating the Mintabie skill format"
tags: [example, tutorial]
---

# Example Skill

## Steps
1. Identify the task
2. Break it into subtasks
3. Execute each step with available tools
4. Verify results

## Pitfalls
- Don't skip verification steps
- Always check error output before retrying
"""
        )
        logger.info(f"Created example skill at {example}")


# Auto-create example skill on import
ensure_skills_dir()
create_example_skill()
