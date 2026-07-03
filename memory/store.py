"""Memory store — JSON file persistence for user profile and working memory."""

import json
import os
import time
from pathlib import Path
from typing import List, Optional

from config import MINTABIE_HOME

MEMORY_FILE = MINTABIE_HOME / "memories.json"

# Max entries per store before eviction kicks in
MAX_USER_PROFILE = 50
MAX_WORKING_MEMORY = 100


def _load_raw() -> dict:
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_raw(data: dict) -> None:
    MINTABIE_HOME.mkdir(parents=True, exist_ok=True)
    tmp = MEMORY_FILE.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.rename(MEMORY_FILE)


# ── User Profile ──────────────────────────────────────────────────────

def get_user_profile() -> List[dict]:
    data = _load_raw()
    return data.get("user_profile", [])


def add_user_profile(content: str) -> None:
    data = _load_raw()
    entries = data.get("user_profile", [])
    entries = [e for e in entries if e.get("content") != content]
    entries.append({"content": content, "created_at": time.time()})
    if len(entries) > MAX_USER_PROFILE:
        entries = entries[-MAX_USER_PROFILE:]
    data["user_profile"] = entries
    _save_raw(data)


def remove_user_profile(old_text: str) -> bool:
    data = _load_raw()
    entries = data.get("user_profile", [])
    before = len(entries)
    entries = [e for e in entries if old_text not in e.get("content", "")]
    if len(entries) == before:
        return False
    data["user_profile"] = entries
    _save_raw(data)
    return True


# ── Working Memory ────────────────────────────────────────────────────

def get_working_memory() -> List[dict]:
    data = _load_raw()
    return data.get("working_memory", [])


def add_working_memory(content: str) -> None:
    data = _load_raw()
    entries = data.get("working_memory", [])
    entries = [e for e in entries if e.get("content") != content]
    entries.append({"content": content, "created_at": time.time()})
    if len(entries) > MAX_WORKING_MEMORY:
        entries = entries[-MAX_WORKING_MEMORY:]
    data["working_memory"] = entries
    _save_raw(data)


def remove_working_memory(old_text: str) -> bool:
    data = _load_raw()
    entries = data.get("working_memory", [])
    before = len(entries)
    entries = [e for e in entries if old_text not in e.get("content", "")]
    if len(entries) == before:
        return False
    data["working_memory"] = entries
    _save_raw(data)
    return True


def replace_working_memory(old_text: str, new_content: str) -> bool:
    data = _load_raw()
    entries = data.get("working_memory", [])
    found = False
    for e in entries:
        if old_text in e.get("content", ""):
            e["content"] = new_content
            e["created_at"] = time.time()
            found = True
            break
    if not found:
        return False
    data["working_memory"] = entries
    _save_raw(data)
    return True


def replace_user_profile(old_text: str, new_content: str) -> bool:
    data = _load_raw()
    entries = data.get("user_profile", [])
    found = False
    for e in entries:
        if old_text in e.get("content", ""):
            e["content"] = new_content
            e["created_at"] = time.time()
            found = True
            break
    if not found:
        return False
    data["user_profile"] = entries
    _save_raw(data)
    return True


# ── Utility ───────────────────────────────────────────────────────────

def format_user_profile() -> str:
    entries = get_user_profile()
    if not entries:
        return ""
    lines = []
    for e in entries:
        lines.append(f"- {e['content']}")
    return "\n".join(lines)


def format_working_memory() -> str:
    entries = get_working_memory()
    if not entries:
        return ""
    lines = []
    for e in entries:
        lines.append(f"- {e['content']}")
    return "\n".join(lines)


def clear_all() -> None:
    _save_raw({"user_profile": [], "working_memory": []})
