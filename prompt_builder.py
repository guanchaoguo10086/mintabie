"""System prompt builder — assembles identity, environment, tools, and memory."""

import os
import platform
import socket
from pathlib import Path
from typing import List, Optional


def build_system_prompt(
    skills: Optional[List[str]] = None,
    user_profile: Optional[str] = None,
    memory: Optional[str] = None,
) -> str:
    """Build the complete system prompt for the agent.

    Structure:
      1. Identity
      2. Environment hints (OS, CWD, etc.)
      3. Capabilities (tool usage rules)
      4. Skills index
      5. Memory / User profile (injected by MemoryManager)
    """
    parts = [
        _identity_prompt(),
        _environment_hints(),
        _capabilities_prompt(),
    ]

    if skills:
        parts.append(_skills_index(skills))

    # memory already includes both user_profile and working_memory
    if memory:
        parts.append(memory)

    return "\n\n".join(parts)


def _identity_prompt() -> str:
    return """You are Mintabie, a minimal AI agent that helps with programming, system tasks, and general questions.
You have access to tools that let you interact with the environment.
Think step by step, use tools when needed, and provide clear answers."""


def _environment_hints() -> str:
    hostname = socket.gethostname()
    cwd = os.getcwd()
    os_info = f"{platform.system()} {platform.release()}"
    user = os.environ.get("USER", "unknown")
    return f"""## Environment

- **OS:** {os_info}
- **Host:** {hostname}
- **User:** {user}
- **CWD:** {cwd}
- **Shell:** bash

When the user asks you to build, run, or verify something, keep working until you have actually exercised the code or produced the requested result. Report what real execution returned."""


def _capabilities_prompt() -> str:
    return """## Capabilities

You have access to the following categories of tools:

1. **terminal** — Run shell commands (build, git, scripts, installs)
2. **read_file** — Read files with line numbers
3. **write_file** — Create or overwrite files
4. **patch** — Make targeted find-and-replace edits
5. **web_search** / **web_extract** — Search the web and extract page content

7. **memory** — Read, add, remove, and manage persistent cross-session memory
8. **user profile** — Mintabie remembers your preferences across sessions using the memory tool

### Rules
- Use tools when you need information you don't have.
- After creating or modifying files, verify the result if possible.
- If a tool call fails, try an alternative approach before giving up.
- Report back what actually happened — don't fabricate results.
- You can save important facts using the **memory** tool — use `memory` with action="add" and target="user" for user preferences, or target="memory" for environment facts."""


def _skills_index(skills: List[str]) -> str:
    if not skills:
        return ""
    items = "\n".join(f"  - {s}" for s in skills)
    return f"""## Loaded Skills

{items}"""
