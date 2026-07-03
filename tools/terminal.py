"""terminal tool — run shell commands."""

import json
import logging
import subprocess
import shlex
import os

from tools.registry import registry

logger = logging.getLogger(__name__)


def run_terminal(args: dict, **kw) -> str:
    """Execute a shell command."""
    command = args.get("command", "")
    timeout = args.get("timeout", 180)
    workdir = args.get("workdir")

    if not command:
        return json.dumps({"error": "No command provided", "success": False})

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir or os.getcwd(),
        )
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr

        return json.dumps({
            "output": output,
            "exit_code": result.returncode,
            "success": result.returncode == 0,
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Command timed out after {timeout}s", "success": False})
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


registry.register(
    name="terminal",
    description="Run a shell command and capture output",
    schema={
        "name": "terminal",
        "description": "Execute a shell command and capture its output",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 180},
                "workdir": {"type": "string", "description": "Working directory"},
            },
            "required": ["command"],
        },
    },
    handler=run_terminal,
    toolset="core",
    emoji="🖥️",
)
