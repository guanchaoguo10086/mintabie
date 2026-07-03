"""Tool implementations — auto-import triggers self-registration."""

# Import all tool modules so they self-register
import tools.terminal  # noqa: F401
import tools.read_file  # noqa: F401
import tools.write_file  # noqa: F401
import tools.patch  # noqa: F401
import tools.web_search  # noqa: F401
import tools.memory_tool  # noqa: F401
import tools.registry  # noqa: F401
import tools.skill_manager_tool  # noqa: F401
