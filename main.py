"""Mintabie — A minimal AI agent CLI.

Usage:
    python main.py                          # Interactive chat
    python main.py -q "What is Python?"     # Single query
    python main.py --resume <session_id>    # Resume session
"""

import argparse
import json
import logging
import os
import readline  # noqa: F401
import sys
import time
import uuid
from pathlib import Path

# Ensure tools are imported so they self-register
import tools  # noqa: F401

from agent import AIAgent
from config import MINTABIE_HOME, load_config
from session_store import SessionDB

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BANNER = """╔══════════════════════════════════════╗
║  Mintabie — minimal AI agent        ║
║  Type /help for commands             ║
╚══════════════════════════════════════╝"""


def main():
    parser = argparse.ArgumentParser(description="Mintabie — minimal AI agent")
    parser.add_argument("-q", "--query", help="Single query, non-interactive")
    parser.add_argument("--resume", help="Resume a session by ID")
    parser.add_argument("--model", help="Model to use (overrides config)")
    parser.add_argument("--quiet", action="store_true", help="Suppress banner")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    cfg = load_config()

    # Session DB
    db_path = MINTABIE_HOME / "sessions.db"
    session_db = SessionDB(str(db_path))

    # Session ID
    if args.resume:
        session_id = args.resume
        existing_session = session_db.get_session(session_id)
        if not existing_session:
            print(f"Session not found: {session_id}")
            sys.exit(1)
    else:
        session_id = str(uuid.uuid4())

    # Create agent
    agent = AIAgent(
        model=args.model or cfg["model"]["default"],
        base_url=cfg["model"]["base_url"],
        api_key=cfg["model"]["api_key"],
        provider_name=cfg["model"].get("provider", ""),
        session_id=session_id,
        session_db=session_db,
        quiet_mode=args.quiet or bool(args.query),
    )

    if args.query:
        # Single query mode
        result = agent.run_conversation(args.query)
        print(result["response"])
        agent.close()
        return

    # ── Interactive mode ──
    if not args.quiet:
        print(BANNER)
        print(f"  Session: {session_id[:8]}...")
        print(f"  Model:   {agent.model}")
        print()

    # Load conversation history if resuming
    history_messages = []
    if args.resume:
        db_msgs = session_db.get_messages(session_id)
        history_messages = _db_messages_to_openai(db_msgs)
        if history_messages and not args.quiet:
            print(f"  Resumed session with {len(history_messages)} messages in history")
            print()

    # Main input loop
    try:
        _interactive_loop(agent, history_messages)
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    finally:
        agent.close()


def _interactive_loop(agent: AIAgent, history_messages: list) -> None:
    """Run the interactive REPL."""
    conversation_history = history_messages

    while True:
        try:
            user_input = input(">>> ")
        except EOFError:
            print()
            break

        text = user_input.strip()
        if not text:
            continue

        # Slash commands
        if text.startswith("/"):
            handled = _handle_slash_command(text, agent)
            if handled == "quit":
                print("Goodbye!")
                break
            if handled:
                continue

        # Normal message
        print()
        start = time.time()
        result = agent.run_conversation(
            text,
            conversation_history=conversation_history,
        )
        elapsed = time.time() - start

        # Print response
        response = result["response"]
        if response:
            print(response)
            print()

        # Show stats
        iters = result["iterations"]
        print(f"  ── {iters} iteration{'s' if iters != 1 else ''}, {elapsed:.1f}s ──")
        print()

        # Update conversation history for next turn
        conversation_history = result["messages"]


def _handle_slash_command(text: str, agent: AIAgent) -> str:
    """Handle a slash command. Returns 'quit' to exit, True if handled, False otherwise."""
    cmd = text.split()[0].lower()
    rest = text[len(cmd):].strip()

    if cmd in ("/quit", "/exit", "/q"):
        return "quit"

    elif cmd == "/help":
        print("""Commands:
  /quit              Exit
  /new               Fresh session (reset history)
  /model [name]      Show or change model
  /provider [name]   Show or change provider
  /memory [target]   View memory entries
  /skills [name]     List or view a skill
  /help              Show this help
""")

    elif cmd == "/new":
        agent._cached_system_prompt = None
        print("Session reset. Starting fresh.\n")
        return True

    elif cmd == "/model":
        if rest:
            agent.model = rest
            agent._cached_system_prompt = None
            agent._resolve_api_endpoint()
            print(f"Model changed to: {rest}\n")
        else:
            print(f"Current model: {agent.model}\n")
        return True

    elif cmd == "/provider":
        if rest:
            msg = agent.switch_provider(rest)
            print(f"{msg}\n")
        else:
            print(f"Current provider: {agent.provider_name or 'openai'}\n")
        return True

    elif cmd == "/memory":
        from memory.store import get_user_profile, get_working_memory
        target = rest or "all"
        if target in ("all", "user"):
            entries = get_user_profile()
            print(f"User Profile ({len(entries)} entries):")
            for e in entries:
                print(f"  - {e['content'][:80]}")
        if target in ("all", "memory"):
            entries = get_working_memory()
            print(f"Working Memory ({len(entries)} entries):")
            for e in entries:
                print(f"  - {e['content'][:80]}")
        print()
        return True

    elif cmd == "/skills":
        from tools.skill_manager_tool import get_skills_list
        if rest:
            # View specific skill
            from tool_registry import registry
            result = registry.dispatch("skill_view", {"name": rest})
            data = json.loads(result)
            if data.get("success"):
                print(data["content"])
            else:
                print(f"Skill not found: {rest}")
        else:
            skills = get_skills_list()
            if skills:
                print(f"Loaded skills ({len(skills)}):")
                for s in skills:
                    desc = f" — {s['description']}" if s['description'] else ""
                    print(f"  - {s['name']}{desc}")
            else:
                print("No skills loaded.")
        print()
        return True

    else:
        print(f"Unknown command: {cmd}. Type /help for available commands.\n")
        return True

    return False


def _db_messages_to_openai(db_msgs: list) -> list:
    """Convert DB message rows to OpenAI-format message list."""
    messages = []
    for m in db_msgs:
        role = m["role"]
        if role == "system":
            continue

        msg = {"role": role}

        if role == "tool":
            msg["tool_call_id"] = m["tool_call_id"]
            msg["content"] = m["content"] or ""
            msg["name"] = m["name"] or ""
        elif m.get("tool_calls"):
            msg["content"] = m["content"] or None
            msg["tool_calls"] = json.loads(m["tool_calls"])
        else:
            msg["content"] = m["content"] or ""

        messages.append(msg)
    return messages


if __name__ == "__main__":
    main()
