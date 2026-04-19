"""
QWEN3-CODER ULTIMATE v7.0 — GOD MODE + INTELLIGENCE ENGINE + IDE BRIDGE
Autor: José Victor
v7.0 adds: ToolValidator (zero-hallucination), PromptEngine (few-shot SQLite),
ContextManagerPro (semantic windowing), VSCodeBridge (real IDE integration).
v6.0: ReasoningEngine (CoT/ToT/Reflection), AgentPlanner, CodeAnalyzer,
SecurityScanner, RefactorEngine, TestGenerator, AgentPool (parallel),
CriticAgent (auto-review), MemoryAgent (cross-session), RAG, Browser,
TDD Loop, MCP, Ollama, Context7, Multi-Provider, 90+ Tools.
"""

import os, json, datetime, subprocess, re, time, difflib, tempfile, shutil, base64, logging
import glob as glob_lib, threading, hashlib, sqlite3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

# ── COMPANION MODULES ─────────────────────────────────────────────────────────
try:
    from qwen_rag import RAGSystem
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

try:
    from qwen_browser import BrowserAutomation
    BROWSER_AVAILABLE = True
except ImportError:
    BROWSER_AVAILABLE = False

# ── v6.0 INTELLIGENCE MODULES ─────────────────────────────────────────────────
try:
    from core.reasoning_engine import ReasoningEngine
    REASONING_AVAILABLE = True
except ImportError:
    REASONING_AVAILABLE = False

try:
    from core.agent_planner import AgentPlanner, TaskStatus
    PLANNER_AVAILABLE = True
except ImportError:
    PLANNER_AVAILABLE = False

try:
    from tools.code_analyzer import CodeAnalyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False

try:
    from tools.security_scanner import SecurityScanner
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

try:
    from tools.refactor_engine import RefactorEngine
    REFACTOR_AVAILABLE = True
except ImportError:
    REFACTOR_AVAILABLE = False

try:
    from tools.test_generator import TestGenerator
    TESTGEN_AVAILABLE = True
except ImportError:
    TESTGEN_AVAILABLE = False

try:
    from agents.agent_pool import AgentPool, AgentRole, AgentTask
    POOL_AVAILABLE = True
except ImportError:
    POOL_AVAILABLE = False

try:
    from agents.critic_agent import CriticAgent, Strictness
    CRITIC_AVAILABLE = True
except ImportError:
    CRITIC_AVAILABLE = False

try:
    from agents.memory_agent import MemoryAgent
    MEMORY_AGENT_AVAILABLE = True
except ImportError:
    MEMORY_AGENT_AVAILABLE = False

# ── v7.0 RELIABILITY MODULES ──────────────────────────────────────────────────
try:
    from core.tool_validator import ToolValidator
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False

try:
    from core.prompt_engine import PromptEngine
    PROMPT_ENGINE_AVAILABLE = True
except ImportError:
    PROMPT_ENGINE_AVAILABLE = False

try:
    from core.context_manager_pro import ContextManagerPro
    CTX_PRO_AVAILABLE = True
except ImportError:
    CTX_PRO_AVAILABLE = False

try:
    from ui.vscode_bridge import create_vscode_bridge
    VSCODE_BRIDGE_AVAILABLE = True
except ImportError:
    VSCODE_BRIDGE_AVAILABLE = False

# ── v8.0 INFRASTRUCTURE MODULES ───────────────────────────────────────────────
try:
    from core.hooks_engine import HooksEngine, HookEvent
    HOOKS_AVAILABLE = True
except ImportError:
    HOOKS_AVAILABLE = False

try:
    from core.plan_mode import PlanMode, BLOCKED_IN_PLAN_MODE
    PLAN_MODE_AVAILABLE = True
except ImportError:
    PLAN_MODE_AVAILABLE = False

try:
    from core.checkpoint import CheckpointSystem
    CHECKPOINT_AVAILABLE = True
except ImportError:
    CHECKPOINT_AVAILABLE = False

try:
    from core.structured_output import StructuredOutput
    STRUCTURED_OUTPUT_AVAILABLE = True
except ImportError:
    STRUCTURED_OUTPUT_AVAILABLE = False

try:
    from core.cron_scheduler import CronScheduler
    CRON_AVAILABLE = True
except ImportError:
    CRON_AVAILABLE = False

try:
    from tools.worktree_manager import WorktreeManager
    WORKTREE_AVAILABLE = True
except ImportError:
    WORKTREE_AVAILABLE = False

try:
    from tools.github_integration import GitHubIntegration
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

try:
    from ui.web_ui import run_with_qwen
    WEBUI_AVAILABLE = True
except ImportError:
    WEBUI_AVAILABLE = False

# ── v9.0 CLAUDE CODE DNA MODULES ──────────────────────────────────────────────
try:
    from core.dream_system import DreamSystem
    DREAM_AVAILABLE = True
except ImportError:
    DREAM_AVAILABLE = False

try:
    from core.speculative_executor import SpeculativeExecutor, BatchTool, TOOL_CONCURRENCY
    SPECULATIVE_AVAILABLE = True
except ImportError:
    SPECULATIVE_AVAILABLE = False

try:
    from core.kairos import Kairos
    KAIROS_AVAILABLE = True
except ImportError:
    KAIROS_AVAILABLE = False

try:
    from core.session_state import SessionManager as SessionStateManager
    SESSION_STATE_AVAILABLE = True
except ImportError:
    SESSION_STATE_AVAILABLE = False

try:
    from core.context_collapse import ContextCollapse
    COLLAPSE_AVAILABLE = True
except ImportError:
    COLLAPSE_AVAILABLE = False

try:
    from core.buddy import Buddy
    BUDDY_AVAILABLE = True
except ImportError:
    BUDDY_AVAILABLE = False

try:
    from core.permissions import PermissionManager, PermissionMode, from_cli_args as permissions_from_cli
    PERMISSIONS_AVAILABLE = True
except ImportError:
    PERMISSIONS_AVAILABLE = False

try:
    from core.production_hardening import HardenedAPIClient, RetryPolicy, CircuitBreaker, ErrorBudget, RateLimiter
    HARDENING_AVAILABLE = True
except ImportError:
    HARDENING_AVAILABLE = False

try:
    from agents.task_agent import TaskAgent, TaskResult
    TASK_AGENT_AVAILABLE = True
except ImportError:
    TASK_AGENT_AVAILABLE = False

# ── LOGGING CONFIG ────────────────────────────────────────────────────────────
logging.basicConfig(
    filename="qwen_debug.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    filemode="a"
)
logger = logging.getLogger(__name__)

# ── RICH ──────────────────────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.live import Live
    from rich.table import Table
    from rich.prompt import Confirm, Prompt
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# ── OPTIONAL ──────────────────────────────────────────────────────────────────
try:
    import requests; REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup; BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from duckduckgo_search import DDGS; DDG_AVAILABLE = True
except ImportError:
    DDG_AVAILABLE = False

try:
    import tiktoken; TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

try:
    import pyperclip; PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

# ── CONTEXT7 ─────────────────────────────────────────────────────────────────
CONTEXT7_KEY = "ctx7sk-911c91e5-879e-405f-8558-b80f43785606"
CONTEXT7_URL = "https://context7.com/api/v2"

# ── MODEL ROUTING ─────────────────────────────────────────────────────────────
ROUTING_RULES = {
    "reasoning": {
        "keywords": ["por que","why","analise","analyze","explain","explique","understand",
                     "architecture","arquitetura","design pattern","trade-off","compare"],
        "model":    "deepseek-ai/DeepSeek-R1",
    },
    "fast": {
        "keywords": ["/tree","/list","/memory","/mcp","/config","/models","/tools"],
        "model":    "Qwen/Qwen2.5-Coder-32B-Instruct",
    },
    "default": {
        "model": "qwen/qwen3-coder:free",  # Qwen3-Coder-480B — sempre
    },
}

THINKING_TRIGGERS = [
    "/plan", "/debug", "/review", "/think", "por que", "why", "analyze",
    "arquitetura", "refactor", "optimize", "security", "segurança",
]

# ── PATHS ─────────────────────────────────────────────────────────────────────
CONFIG_FILE  = "qwen_config.json"
HISTORY_FILE = "qwen_history.json"
MEMORY_FILE  = "qwen_memory.json"
MCP_CONFIG   = "qwen_mcp.json"
UNDO_FILE    = "qwen_undo.json"
QWEN_MD      = "QWEN.md"
SESSIONS_DIR = Path("qwen_sessions")

DEFAULT_CONFIG = {
    "hf_token":           os.getenv("HF_TOKEN", ""),
    "together_token":     os.getenv("TOGETHER_TOKEN", ""),
    "model":              "Qwen/Qwen3-Coder-480B-A35B-Instruct",
    "temperature":        0.2,
    "max_tokens":         8192,
    "max_history":        60,
    "safe_mode":          True,
    "parallel_tools":     True,
    "auto_compress":      True,
    "compress_threshold": 40,
    "show_diff":          True,
    "auto_copy":          False,
    "auto_context":       True,
    "model_routing":      True,
    "thinking_mode":      True,
    "ollama_model":       "qwen2.5-coder:7b",
    "ollama_url":         "http://localhost:11434",
    "browser_headless":   False,
    "hooks":              {"pre_tool": "", "post_tool": "", "on_start": "", "on_exit": ""},
}

AVAILABLE_MODELS = {
    "qwen-480b":  "Qwen/Qwen3-Coder-480B-A35B-Instruct",
    "qwen-32b":   "Qwen/Qwen2.5-Coder-32B-Instruct",
    "deepseek":   "deepseek-ai/DeepSeek-Coder-V2-Instruct",
    "llama-70b":  "meta-llama/Llama-3.3-70B-Instruct",
    "mistral-7b": "mistralai/Mistral-7B-Instruct-v0.3",
    "phi-4":      "microsoft/phi-4",
}

DANGEROUS_PATTERNS = [
    r"rm\s+-[rf]{1,2}\s*/", r"del\s+/[sfq]", r"format\s+[a-zA-Z]:",
    r"DROP\s+(TABLE|DATABASE)", r"TRUNCATE\s+TABLE", r"sudo\s+rm",
    r"mkfs", r"dd\s+if=", r"chmod\s+777", r"shutdown", r"reboot",
    r"> /dev/(sd|hd|nvme)", r"git\s+(push\s+--force|reset\s+--hard|clean\s+-fd)",
]

class C:
    CY='\033[96m'; BL='\033[94m'; GR='\033[92m'; YL='\033[93m'
    RD='\033[91m'; BD='\033[1m';  DM='\033[2m';  EN='\033[0m'; MG='\033[95m'

# ── AUTO-CONTEXT ──────────────────────────────────────────────────────────────
class AutoContext:
    """Detects project type and injects relevant context into the system prompt."""

    CONTEXT_FILES = [
        "QWEN.md", "CLAUDE.md", ".cursorrules", "README.md",
        "package.json", "pyproject.toml", "Cargo.toml", "go.mod",
        "requirements.txt", ".env.example", "docker-compose.yml",
        "Makefile", ".github/workflows/ci.yml",
    ]

    def detect(self, cwd: str = ".") -> dict:
        info = {"type": "unknown", "files": {}, "stack": [], "qwen_md": ""}
        p = Path(cwd)

        # Read QWEN.md / CLAUDE.md
        for fname in ("QWEN.md", "CLAUDE.md", ".cursorrules"):
            fp = p / fname
            if fp.exists():
                info["qwen_md"] = fp.read_text(encoding="utf-8", errors="replace")[:3000]
                break

        # Detect stack
        stack_markers = {
            "Python":     ["requirements.txt", "pyproject.toml", "setup.py", "*.py"],
            "FastAPI":    ["requirements.txt"],
            "Django":     ["manage.py"],
            "Node.js":    ["package.json"],
            "React":      ["src/App.tsx", "src/App.jsx"],
            "Next.js":    ["next.config.js", "next.config.ts"],
            "Rust":       ["Cargo.toml"],
            "Go":         ["go.mod"],
            "Docker":     ["Dockerfile", "docker-compose.yml"],
        }
        for tech, markers in stack_markers.items():
            for m in markers:
                if list(p.glob(m)):
                    info["stack"].append(tech)
                    break

        # Read key context files
        for fname in self.CONTEXT_FILES:
            fp = p / fname
            if fp.exists() and fp.is_file():
                try:
                    content = fp.read_text(encoding="utf-8", errors="replace")[:2000]
                    info["files"][fname] = content
                except Exception:
                    pass

        info["type"] = info["stack"][0] if info["stack"] else "unknown"
        return info

    def build_context_block(self, info: dict) -> str:
        parts = []
        if info.get("qwen_md"):
            parts.append(f"## PROJECT INSTRUCTIONS (QWEN.md)\n{info['qwen_md']}")
        if info.get("stack"):
            parts.append(f"## DETECTED STACK\n{', '.join(info['stack'])}")
        for fname, content in info.get("files", {}).items():
            if fname in ("QWEN.md", "CLAUDE.md", ".cursorrules"):
                continue
            parts.append(f"## {fname}\n```\n{content[:800]}\n```")
        return "\n\n".join(parts)


def build_system_prompt(config: dict, context_block: str = "") -> str:
    """Builds the system prompt with explicit file access instructions."""
    model = config.get("model", "Qwen").split("/")[-1]
    safe  = "ON" if config.get("safe_mode") else "OFF"
    cwd   = os.getcwd()
    ctx   = f"\n\n---\n{context_block}" if context_block else ""
    
    return f"""You are **Qwen3-CODER ULTIMATE v9.0** — the most powerful AI coding assistant with DIRECT tool access.
Model: {model} | Safe: {safe} | Date: {datetime.date.today()} | Dir: {cwd}
Respond ALWAYS in the same language the user writes in (Portuguese → Portuguese, English → English).

## REGRA ABSOLUTA — USE FERRAMENTAS, NUNCA INVENTE
- NUNCA diga "não consigo", "não sei", "não tenho acesso" se existe uma ferramenta para isso.
- "que horas são?" → chame `get_current_time` IMEDIATAMENTE.
- "veja o arquivo X" → chame `read_file` IMEDIATAMENTE.
- "estrutura do projeto" → chame `file_tree` IMEDIATAMENTE.
- "busque X" → chame `search_web` ou `search_in_files` IMEDIATAMENTE.
- "rode esse código" → chame `run_command` IMEDIATAMENTE.
- Se não sabe algo que uma ferramenta pode responder: USE A FERRAMENTA. Não peça desculpas.

## FERRAMENTAS DISPONÍVEIS (use proativamente)
| Pergunta do usuário | Ferramenta |
|---|---|
| que horas / data são? | `get_current_time` |
| veja arquivo X | `read_file` |
| estrutura / tree | `file_tree` |
| busque função Y | `search_in_files` |
| corrija erro em Z | `read_file` → `edit_file` |
| rode testes | `run_command` |
| busque na web | `search_web` |
| info do sistema | `system_info` |

## 🛠️ TOOL USAGE STRATEGY
| User asks for... | You should use... |
|-----------------|-------------------|
| "veja o arquivo X" / "open X" | `read_file(path="X")` |
| "o que tem na pasta?" / "list files" | `list_directory(path=".")` |
| "onde está a função Y?" / "find Y" | `search_in_files(pattern="def Y", file_pattern="*.py")` |
| "mostre a estrutura" / "tree" | `file_tree(path=".", max_depth=3)` |
| "corrija o erro em Z" / "fix Z" | `read_file(path="Z")` → analyze → `edit_file` or `write_file` |
| "busque por 'TODO'" | `find_todos(path=".")` or `search_in_files(pattern="TODO")` |
| "arquivos recentes" | Suggest user check manually or use OS commands |

## 🔄 WORKFLOW FOR LOCAL CODE FIXES
1. User mentions file/error → 2. READ the file with `read_file` → 3. Analyze the issue → 
4. Propose fix with code snippet → 5. Apply with `edit_file`/`write_file` (with diff approval if safe_mode) → 
6. Verify with `run_command` if needed → 7. Report success with summary

## 📁 FILE PATHS — USER CONTEXT
- Current working directory: {cwd}
- User is on Windows (paths use \\ or /)
- Common project files: QWEN.md, pyproject.toml, package.json, requirements.txt, main.py, app.py, index.js

## 💬 RESPONSE STYLE
- Be proactive: "Vou ler o arquivo X para analisar..." / "Let me read file X to analyze..."
- Show file previews when helpful: "Conteúdo de `main.py` (linhas 1-20): ```python ... ```"
- After fixing: "✅ Correção aplicada. Diferenças: [diff resumido]"
- Offer next steps: "Quer que eu rode `python main.py` para testar?"
- Use Portuguese when user writes in Portuguese, English otherwise.

## ⚠️ SAFETY (if safe_mode=ON)
- Always show diff before writing files
- Ask approval for dangerous operations (rm, DROP, sudo, format, etc.)
- Never execute untrusted code without warning the user

## 🧠 THINKING MODE FOR COMPLEX TASKS
For complex requests: Plan → Act → Verify → Report
1. Understand the goal
2. List required tools/steps
3. Execute step by step
4. Validate results
5. Summarize outcome

{ctx}"""


# ── TOKEN COUNTER ─────────────────────────────────────────────────────────────
class TokenCounter:
    def __init__(self):
        self._enc = None
        if TIKTOKEN_AVAILABLE:
            try:
                self._enc = tiktoken.get_encoding("cl100k_base")
            except Exception:
                pass

    def count(self, text: str) -> int:
        if self._enc:
            return len(self._enc.encode(text))
        return len(text) // 4  # fallback approximation

    def count_messages(self, messages: list) -> int:
        total = 0
        for m in messages:
            total += self.count(str(m.get("content", "")))
            if m.get("tool_calls"):
                total += self.count(json.dumps(m["tool_calls"]))
        return total


# ── UNDO SYSTEM ───────────────────────────────────────────────────────────────
class UndoSystem:
    """Tracks file changes and supports undo."""

    def __init__(self):
        self._stack: list = []

    def snapshot(self, path: str):
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self._stack.append({"path": path, "content": content, "ts": time.time()})
            except Exception:
                pass

    def undo(self) -> Optional[str]:
        if not self._stack:
            return "Nothing to undo."
        entry = self._stack.pop()
        try:
            with open(entry["path"], "w", encoding="utf-8") as f:
                f.write(entry["content"])
            return f"✅ Undone: {entry['path']} (restored to state from {datetime.datetime.fromtimestamp(entry['ts']):%H:%M:%S})"
        except Exception as e:
            return f"Undo failed: {e}"

    def history(self) -> str:
        if not self._stack:
            return "Undo stack is empty."
        return "\n".join(
            f"[{i+1}] {e['path']} at {datetime.datetime.fromtimestamp(e['ts']):%H:%M:%S}"
            for i, e in enumerate(reversed(self._stack[-10:]))
        )


# ── MEMORY SYSTEM ─────────────────────────────────────────────────────────────
class MemorySystem:
    def __init__(self):
        self.data: dict = self._load()

    def _load(self) -> dict:
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def save(self, key: str, content: str, type: str = "reference") -> str:
        self.data[key] = {"content": content, "type": type, "at": datetime.datetime.now().isoformat()}
        self._save()
        return f"✅ Saved: '{key}'"

    def recall(self, query: str) -> str:
        q = query.lower()
        scored = []
        for k, v in self.data.items():
            text = (k + " " + v["content"]).lower()
            score = sum(1 for word in q.split() if word in text)
            if score:
                scored.append((score, k, v))
        scored.sort(reverse=True)
        if not scored:
            return f"No memories matching: {query}"
        return "\n\n".join(f"**{k}** [{v['type']}] (score:{s})\n{v['content']}" for s, k, v in scored[:5])

    def list_all(self) -> str:
        if not self.data:
            return "Memory is empty."
        rows = []
        for k, v in self.data.items():
            rows.append(f"- [{v['type']}] **{k}**: {v['content'][:80]}")
        return "\n".join(rows)


# ── MCP CLIENT ────────────────────────────────────────────────────────────────
class MCPClient:
    def __init__(self):
        self.servers: dict   = {}
        self.processes: dict = {}
        self.extra_tools: list = []
        self._lock = threading.Lock()
        self._load_config()

    def _load_config(self):
        if not os.path.exists(MCP_CONFIG):
            with open(MCP_CONFIG, "w") as f:
                json.dump({"mcpServers": {}}, f, indent=2)
        try:
            with open(MCP_CONFIG) as f:
                self.servers = json.load(f).get("mcpServers", {})
        except Exception:
            self.servers = {}

    def start_all(self) -> list:
        started = []
        for name, cfg in self.servers.items():
            try:
                cmd = [cfg["command"]] + cfg.get("args", [])
                env = {**os.environ, **cfg.get("env", {})}
                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, env=env)
                self.processes[name] = proc
                self._rpc(name, "initialize", {"protocolVersion": "2024-11-05",
                                               "clientInfo": {"name": "QwenUltimate", "version": "4.1"},
                                               "capabilities": {}})
                result = self._rpc(name, "tools/list", {})
                for t in (result or {}).get("tools", []):
                    self.extra_tools.append({
                        "type": "function",
                        "function": {
                            "name":        f"mcp__{name}__{t['name']}",
                            "description": f"[MCP:{name}] {t.get('description','')}",
                            "parameters":  t.get("inputSchema", {"type":"object","properties":{}})
                        },
                        "_mcp_server": name, "_mcp_tool": t["name"]
                    })
                started.append(name)
            except Exception as e:
                print(f"{C.YL}⚠ MCP '{name}': {e}{C.EN}")
        return started

    def _rpc(self, server: str, method: str, params: dict, id: int = 1) -> Optional[dict]:
        proc = self.processes.get(server)
        if not proc:
            return None
        try:
            with self._lock:
                proc.stdin.write(json.dumps({"jsonrpc":"2.0","method":method,"params":params,"id":id}) + "\n")
                proc.stdin.flush()
                return json.loads(proc.stdout.readline()).get("result")
        except Exception:
            return None

    def call_tool(self, server: str, tool: str, args: dict) -> str:
        r = self._rpc(server, "tools/call", {"name": tool, "arguments": args}, id=99)
        if r:
            return "\n".join(c.get("text","") for c in r.get("content",[]) if c.get("type")=="text")
        return "MCP: no result."

    def stop_all(self):
        for p in self.processes.values():
            try: p.terminate()
            except Exception: pass

    def status(self) -> str:
        if not self.servers:
            return "No MCP servers. Edit qwen_mcp.json."
        return "\n".join(f"  {'🟢' if n in self.processes else '🔴'} {n}" for n in self.servers)


# ── APPROVAL & DIFF ───────────────────────────────────────────────────────────
class ApprovalSystem:
    def __init__(self, config: dict, console):
        self.config  = config
        self.console = console
        self._always_allow: set = set()

    def is_dangerous(self, tool: str, args: dict) -> bool:
        if tool == "delete_file":
            return True
        if tool in ("run_command", "background_run"):
            cmd = args.get("command", "")
            return any(re.search(p, cmd, re.IGNORECASE) for p in DANGEROUS_PATTERNS)
        if tool == "git_operation":
            xtra = args.get("args", "")
            return any(k in xtra for k in ("--force","--hard","-D","-fd"))
        return False

    def request(self, tool: str, args: dict) -> bool:
        if not self.config.get("safe_mode", True):
            return True
        sig = hashlib.md5(f"{tool}{json.dumps(args, sort_keys=True)}".encode()).hexdigest()
        if sig in self._always_allow:
            return True
        if self.console:
            self.console.print(f"\n[bold yellow]⚠ AÇÃO PERIGOSA: {tool}[/bold yellow]")
            self.console.print(f"[yellow]{json.dumps(args, ensure_ascii=False)[:400]}[/yellow]")
            choice = Prompt.ask("Aprovar?", choices=["s","n","sempre"], default="s")
        else:
            print(f"\n{C.YL}⚠ {tool}: {json.dumps(args)[:300]}{C.EN}")
            choice = input("Aprovar? [s/n/sempre]: ").strip().lower() or "s"
        if choice == "sempre":
            self._always_allow.add(sig)
            return True
        return choice in ("s","y","sim","yes","")


class DiffEngine:
    def __init__(self, config: dict, console):
        self.config  = config
        self.console = console

    def show_and_approve(self, path: str, old: str, new: str) -> bool:
        diff = list(difflib.unified_diff(
            old.splitlines(keepends=True), new.splitlines(keepends=True),
            fromfile=f"a/{path}", tofile=f"b/{path}", lineterm=""
        ))
        if not diff:
            return True
        if not self.config.get("show_diff", True):
            return True
        if self.console:
            self.console.print(Syntax("".join(diff), "diff", theme="monokai"))
        else:
            for line in diff:
                col = C.GR if line.startswith("+") and not line.startswith("+++") else \
                      C.RD if line.startswith("-") and not line.startswith("---") else \
                      C.CY if line.startswith("@@") else ""
                print(f"{col}{line}{C.EN}")
        if not self.config.get("safe_mode", True):
            return True
        if self.console:
            return Confirm.ask("Aplicar?", default=True)
        return input("Aplicar? [S/n]: ").strip().lower() in ("","s","y","sim","yes")


# ── CONTEXT MANAGER ───────────────────────────────────────────────────────────
class ContextManager:
    def __init__(self, config: dict, client, model: str):
        self.config = config
        self.client = client
        self.model  = model

    def should_compress(self, history: list) -> bool:
        return (self.config.get("auto_compress", True) and
                sum(1 for m in history if m["role"]=="user") > self.config.get("compress_threshold", 40))

    def compress(self, history: list) -> list:
        if len(history) < 8:
            return history
        sys_msg, recent, middle = history[0], history[-10:], history[1:-10]
        if not middle:
            return history
        body = "\n".join(f"{m['role'].upper()}: {str(m.get('content',''))[:400]}" for m in middle)
        try:
            r = self.client.chat.completions.create(
                model=self.model, stream=False, max_tokens=512, temperature=0.1,
                messages=[
                    {"role":"system","content":"Summarize this chat history in <200 words, preserving all technical decisions, code written, and key context."},
                    {"role":"user","content":body[:6000]}
                ]
            )
            summary = r.choices[0].message.content
            compressed = [sys_msg, {"role":"system","content":f"[COMPRESSED HISTORY]\n{summary}"}] + recent
            print(f"{C.DM}📦 Compressed: {len(history)}→{len(compressed)} msgs{C.EN}")
            return compressed
        except Exception:
            return history


# ── BACKGROUND PROCESS MANAGER ────────────────────────────────────────────────
class BackgroundManager:
    def __init__(self):
        self._procs: dict = {}

    def run(self, command: str, name: str, cwd: str = ".") -> str:
        try:
            log_path = f"qwen_bg_{name}.log"
            with open(log_path, "w") as log:
                proc = subprocess.Popen(command, shell=True, cwd=cwd,
                                        stdout=log, stderr=subprocess.STDOUT)
            self._procs[name] = proc
            return f"✅ Background '{name}' started (PID {proc.pid}) → log: {log_path}"
        except Exception as e:
            return f"Error: {e}"

    def status(self, name: str) -> str:
        proc = self._procs.get(name)
        if not proc:
            return f"No background process '{name}'"
        rc = proc.poll()
        if rc is None:
            return f"'{name}' running (PID {proc.pid})"
        return f"'{name}' finished (exit {rc})"

    def tail_log(self, name: str, lines: int = 30) -> str:
        log_path = f"qwen_bg_{name}.log"
        if not os.path.exists(log_path):
            return f"No log for '{name}'"
        with open(log_path, encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        return "".join(all_lines[-lines:])

    def kill(self, name: str) -> str:
        proc = self._procs.get(name)
        if not proc:
            return f"Not found: {name}"
        proc.terminate()
        return f"✅ Killed '{name}'"

    def list_all(self) -> str:
        if not self._procs:
            return "No background processes."
        lines = []
        for name, proc in self._procs.items():
            rc = proc.poll()
            status = f"running (PID {proc.pid})" if rc is None else f"done (exit {rc})"
            lines.append(f"  {name}: {status}")
        return "\n".join(lines)


# ── MULTI-AGENT ───────────────────────────────────────────────────────────────
class MultiAgent:
    def __init__(self, client, model: str, all_tools: list, executor):
        self.client    = client
        self.model     = model
        self.all_tools = all_tools
        self.executor  = executor

    def run(self, task: str, context: str = "", max_steps: int = 5) -> str:
        history = [
            {"role": "system", "content": f"You are a specialized sub-agent. Complete the given task concisely using tools. Context: {context[:1000]}"},
            {"role": "user",   "content": task}
        ]
        for _ in range(max_steps):
            try:
                r = self.client.chat.completions.create(
                    model=self.model, messages=history, max_tokens=4096,
                    temperature=0.1, tools=self.all_tools, tool_choice="auto", stream=False
                )
                msg = r.choices[0].message
                if msg.tool_calls:
                    history.append({
                        "role": "assistant", "content": msg.content or "",
                        "tool_calls": [{"id":tc.id,"type":"function","function":{"name":tc.function.name,"arguments":tc.function.arguments}} for tc in msg.tool_calls]
                    })
                    for tc in msg.tool_calls:
                        try:
                            args = json.loads(tc.function.arguments)
                        except Exception:
                            args = {}
                        result = self.executor.execute(tc.function.name, args)
                        history.append({"role":"tool","tool_call_id":tc.id,"content":result})
                else:
                    return msg.content or "(no response)"
            except Exception as e:
                return f"Sub-agent error: {e}"
        return "(max steps reached)"

    def run_parallel(self, tasks: list[dict]) -> list[str]:
        results = [""] * len(tasks)
        with ThreadPoolExecutor(max_workers=min(len(tasks), 4)) as pool:
            futures = {pool.submit(self.run, t["task"], t.get("context","")): i for i, t in enumerate(tasks)}
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    results[idx] = f"Error: {e}"
        return results


# ── OLLAMA CLIENT ────────────────────────────────────────────────────────────
class OllamaClient:
    """Local model client via Ollama."""

    def __init__(self, config: dict):
        self.url   = config.get("ollama_url", "http://localhost:11434")
        self.model = config.get("ollama_model", "qwen2.5-coder:7b")

    def is_available(self) -> bool:
        if not REQUESTS_AVAILABLE:
            return False
        try:
            r = requests.get(f"{self.url}/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def chat(self, messages: list, max_tokens: int = 2048) -> str:
        try:
            r = requests.post(
                f"{self.url}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False,
                      "options": {"num_predict": max_tokens}},
                timeout=120
            )
            return r.json()["message"]["content"]
        except Exception as e:
            return f"Ollama error: {e}"

    def list_models(self) -> list:
        try:
            r = requests.get(f"{self.url}/api/tags", timeout=5)
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    def pull(self, model: str) -> str:
        try:
            r = requests.post(f"{self.url}/api/pull",
                json={"name": model}, timeout=300, stream=True)
            return f"✅ Pulled: {model}"
        except Exception as e:
            return f"Pull error: {e}"


# ── TDD LOOP ──────────────────────────────────────────────────────────────────
class TDDLoop:
    """Autonomous TDD: write tests → write code → run → fix until green."""

    def __init__(self, executor, client, model: str, all_tools: list):
        self.executor  = executor
        self.client    = client
        self.model     = model
        self.all_tools = all_tools

    def run(self, task: str, test_framework: str = "auto", max_iter: int = 10) -> str:
        history = [
            {"role": "system", "content": (
                "You are a TDD expert. Follow this strict cycle:\n"
                "1. Write failing tests first (test file)\n"
                "2. Write minimal implementation to pass\n"
                "3. Run the tests with run_command\n"
                "4. If failing: read error, fix code, run again\n"
                "5. Repeat until ALL tests pass\n"
                "6. Report: DONE + test results\n"
                f"Framework: {test_framework}. Be concise, use tools directly."
            )},
            {"role": "user", "content": f"TDD task: {task}"}
        ]

        for i in range(max_iter):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model, messages=history, max_tokens=4096,
                    temperature=0.1, tools=self.all_tools, tool_choice="auto", stream=False
                )
                msg = resp.choices[0].message

                if msg.tool_calls:
                    history.append({
                        "role": "assistant", "content": msg.content or "",
                        "tool_calls": [
                            {"id": tc.id, "type": "function",
                             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                            for tc in msg.tool_calls
                        ]
                    })
                    for tc in msg.tool_calls:
                        try:
                            args = json.loads(tc.function.arguments)
                        except Exception:
                            args = {}
                        result = self.executor.execute(tc.function.name, args)
                        print(f"  [TDD] {tc.function.name} → {result[:100]}")
                        history.append({"role": "tool", "tool_call_id": tc.id, "content": result})

                        # Detect green
                        low = result.lower()
                        if ("passed" in low or "ok" in low) and "failed" not in low and "error" not in low:
                            if "test" in tc.function.name or "run_command" == tc.function.name:
                                return f"✅ TDD DONE in {i+1} iterations!\n{result}"
                else:
                    # Final message
                    return f"TDD ({i+1} iters):\n{msg.content}"

            except Exception as e:
                return f"TDD error at iter {i+1}: {e}"

        return f"TDD: max iterations ({max_iter}) reached. Check qwen_history.json for full context."


# ── TOOL EXECUTOR ─────────────────────────────────────────────────────────────
class ToolExecutor:
    def __init__(self, memory: MemorySystem, mcp: MCPClient, approval: ApprovalSystem,
                 diff_eng: DiffEngine, undo: UndoSystem, bg: BackgroundManager,
                 config: dict, rag=None, browser=None, ollama=None,
                 code_analyzer=None, security_scanner=None, refactor_engine=None,
                 test_generator=None, agent_pool=None, critic_agent=None, memory_agent=None,
                 reasoning_engine=None, agent_planner=None):
        self.memory          = memory
        self.mcp             = mcp
        self.approval        = approval
        self.diff_eng        = diff_eng
        self.undo            = undo
        self.bg              = bg
        self.config          = config
        self.rag             = rag
        self.browser         = browser
        self.ollama          = ollama
        self.code_analyzer   = code_analyzer
        self.security_scanner = security_scanner
        self.refactor_engine = refactor_engine
        self.test_generator  = test_generator
        self.agent_pool      = agent_pool
        self.critic_agent    = critic_agent
        self.memory_agent    = memory_agent
        self.reasoning_engine = reasoning_engine
        self.agent_planner   = agent_planner
        self.tdd             = None  # set after init (needs client ref)
        self.god_mode        = None  # set after init (needs config)

    def execute(self, name: str, args: dict) -> str:
        # ── Permissions gate ──────────────────────────────────────────────────
        perms = getattr(self, "_permissions", None)
        if perms:
            allowed = perms.prompt_and_check(name, args)
            if not allowed:
                return f"[PERMISSION DENIED] Tool '{name}' was blocked by permission policy."

        # ── Spawn sub-agent (Task tool) ───────────────────────────────────────
        if name == "spawn_task":
            ta = getattr(self, "_task_agent", None)
            if ta:
                result = ta.spawn(
                    task      = args.get("task", ""),
                    context   = args.get("context", ""),
                    tools     = args.get("tools"),
                    max_turns = args.get("max_turns", 20),
                )
                return (
                    f"[TaskAgent {result.task_id}] {'OK' if result.success else 'FAIL'} "
                    f"| {result.turns} turns | {result.tool_calls} tool calls | {result.duration_s:.1f}s\n\n"
                    f"{result.output}"
                )
            return "TaskAgent not available."

        # ── v8.0: Hooks — PreToolUse ──────────────────────────────────────────
        hooks = getattr(self, "_hooks_engine", None)
        if hooks:
            hr = hooks.fire("PreToolUse", {"tool_name": name, "args": args})
            if hr.blocked:
                return f"[Hook blocked] {hr.message}"

        # ── v8.0: Plan Mode gate ──────────────────────────────────────────────
        plan = getattr(self, "_plan_mode", None)
        if plan and plan.active:
            allowed, msg = plan.check_tool(name, args)
            if not allowed:
                plan.add_planned_step(name, args)
                return msg

        # ── v8.0: Checkpoint — snapshot before writes ─────────────────────────
        checkpoint = getattr(self, "_checkpoint", None)
        WRITE_TOOLS = {"write_file", "edit_file", "delete_file", "bulk_write",
                       "copy_file", "move_file", "regex_replace"}
        if checkpoint and name in WRITE_TOOLS:
            path = args.get("path") or args.get("source") or args.get("destination", "")
            if path:
                checkpoint.before_edit(path, name)

        # Legacy pre-tool hook
        hook_cmd = self.config.get("hooks", {}).get("pre_tool", "")
        if hook_cmd:
            subprocess.run(f"{hook_cmd} {name}", shell=True, capture_output=True)
        try:
            if name.startswith("mcp__"):
                parts = name.split("__", 2)
                if len(parts) == 3:
                    return self.mcp.call_tool(parts[1], parts[2], args)

            GOD_TOOLS = {
                "raw_shell","force_write","force_delete","force_read","kill_process",
                "process_list","system_info","network_scan","extract_archive",
                "compress_files","env_set","clipboard_read","clipboard_write",
                "open_file_os","find_files",
            }
            if name in GOD_TOOLS:
                if self.god_mode is None:
                    return "❌ God Mode not initialized."
                if self.config.get("safe_mode", True):
                    return "❌ God Mode bloqueado: safe_mode=true. Mude para false no config."
                return self.god_mode.execute(name, args)

            if self.approval.is_dangerous(name, args):
                if not self.approval.request(name, args):
                    return f"❌ Negado pelo usuário."

            dispatch = {
                "get_current_time": lambda a: datetime.datetime.now().strftime(a.get("format", "%Y-%m-%d %H:%M:%S %Z") or "%Y-%m-%d %H:%M:%S") + f" (UTC{datetime.datetime.now().astimezone().strftime('%z')})",
                "read_file":       self._read_file,
                "write_file":      self._write_file,
                "edit_file":       self._edit_file,
                "delete_file":     self._delete_file,
                "copy_file":       self._copy_file,
                "move_file":       self._move_file,
                "list_directory":  self._list_directory,
                "search_in_files": self._search_in_files,
                "regex_replace":   self._regex_replace,
                "bulk_write":      self._bulk_write,
                "diff_files":      self._diff_files,
                "file_tree":       self._file_tree,
                "find_todos":      self._find_todos,
                "run_command":     self._run_command,
                "background_run":  self._background_run,
                "bg_status":       self._bg_status,
                "bg_tail":         self._bg_tail,
                "bg_kill":         self._bg_kill,
                "execute_code":    self._execute_code,
                "web_search":      self._web_search,
                "fetch_url":       self._fetch_url,
                "http_request":    self._http_request,
                "read_image":      self._read_image,
                "sqlite_query":    self._sqlite_query,
                "git_operation":   self._git_operation,
                "github_cli":      self._github_cli,
                "memory_save":     lambda a: self.memory.save(a["key"], a["content"], a.get("type","reference")),
                "memory_recall":   lambda a: self.memory.recall(a["query"]),
                "memory_list":     lambda _: self.memory.list_all(),
                "create_project":  self._create_project,
                "install_package": self._install_package,
                "env_get":         self._env_get,
                "undo":            lambda _: self.undo.undo(),
                "undo_history":    lambda _: self.undo.history(),
                # ── RAG ───────────────────────────────────────────────────
                "rag_index":       self._rag_index,
                "rag_search":      self._rag_search,
                "rag_stats":       lambda _: self.rag.stats() if self.rag else "RAG not available.",
                "rag_clear":       lambda _: self.rag.clear() if self.rag else "RAG not available.",
                # ── BROWSER ───────────────────────────────────────────────
                "browser_open":        self._browser_open,
                "browser_click":       self._browser_click,
                "browser_type":        self._browser_type,
                "browser_screenshot":  self._browser_screenshot,
                "browser_get_text":    self._browser_get_text,
                "browser_get_links":   self._browser_get_links,
                "browser_run_js":      self._browser_run_js,
                "browser_get_inputs":  self._browser_get_inputs,
                "browser_scroll":      self._browser_scroll,
                "browser_wait_for":    self._browser_wait_for,
                "browser_close":       lambda _: self.browser.close() if self.browser else "Browser not available.",
                # ── CONTEXT7 ──────────────────────────────────────────────
                "context7_search":     self._context7_search,
                "context7_get_docs":   self._context7_get_docs,
                # ── OLLAMA ────────────────────────────────────────────────
                "ollama_chat":         self._ollama_chat,
                "ollama_models":       lambda _: "\n".join(self.ollama.list_models()) if self.ollama else "Ollama not available.",
                "ollama_pull":         lambda a: self.ollama.pull(a["model"]) if self.ollama else "Ollama not available.",
                # ── TDD ───────────────────────────────────────────────────
                "tdd_run":             self._tdd_run,
                # ── v6.0 CODE INTELLIGENCE ───────────────────────────────
                "analyze_code":        self._analyze_code,
                "analyze_directory":   self._analyze_directory,
                "security_scan":       self._security_scan,
                "refactor_rename":     self._refactor_rename,
                "refactor_extract_fn": self._refactor_extract_fn,
                "refactor_extract_var":self._refactor_extract_var,
                "refactor_inline_var": self._refactor_inline_var,
                "generate_tests":      self._generate_tests,
                "fill_coverage_gaps":  self._fill_coverage_gaps,
                "run_tests":           self._run_tests_tool,
                # ── v6.0 AGENTS ──────────────────────────────────────────
                "agent_run":           self._agent_run,
                "agent_pipeline":      self._agent_pipeline,
                "agent_multi_review":  self._agent_multi_review,
                "critic_review":       self._critic_review,
                "critic_gate":         self._critic_gate,
                # ── v6.0 MEMORY AGENT ────────────────────────────────────
                "mem_agent_remember":  self._mem_agent_remember,
                "mem_agent_recall":    self._mem_agent_recall,
                "mem_agent_stats":     lambda _: self.memory_agent.stats() if self.memory_agent else "MemoryAgent N/A.",
                # ── v6.0 REASONING ───────────────────────────────────────
                "reason":              self._reason_tool,
                "plan_task":           self._plan_task_tool,
            }
            fn = dispatch.get(name)
            result = str(fn(args)) if fn else f"Unknown tool: {name}"
        except Exception as e:
            result = f"Tool error [{name}]: {type(e).__name__}: {e}"

        hook_cmd = self.config.get("hooks", {}).get("post_tool", "")
        if hook_cmd:
            subprocess.run(f"{hook_cmd} {name}", shell=True, capture_output=True)
        return result

    def _read_file(self, a: dict) -> str:
        path, s, e = a["path"], a.get("start_line"), a.get("end_line")
        if not os.path.exists(path):
            return f"Not found: {path}"
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        if s or e:
            lines = lines[(s or 1)-1 : e]
        return "".join(f"{i+1:4d} | {l}" for i, l in enumerate(lines, (s or 1))) or "(empty)"

    def _write_file(self, a: dict) -> str:
        path, content = a["path"], a["content"]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        if os.path.exists(path):
            with open(path, encoding="utf-8", errors="replace") as f:
                old = f.read()
            if not self.diff_eng.show_and_approve(path, old, content):
                return "❌ Cancelled."
            self.undo.snapshot(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Written {content.count(chr(10))+1} lines → {path}"

    def _edit_file(self, a: dict) -> str:
        path, old_s, new_s = a["path"], a["old_string"], a["new_string"]
        if not os.path.exists(path):
            return f"Not found: {path}"
        with open(path, encoding="utf-8") as f:
            content = f.read()
        if old_s not in content:
            return f"String not found. Use read_file to get exact content."
        if content.count(old_s) > 1:
            return f"Found {content.count(old_s)} occurrences — be more specific."
        new_content = content.replace(old_s, new_s, 1)
        if not self.diff_eng.show_and_approve(path, content, new_content):
            return "❌ Cancelled."
        self.undo.snapshot(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"✅ Edited {path}"

    def _delete_file(self, a: dict) -> str:
        path = a["path"]
        if not os.path.exists(path):
            return f"Not found: {path}"
        if os.path.isdir(path) and a.get("recursive"):
            shutil.rmtree(path)
        elif os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        return f"✅ Deleted: {path}"

    def _copy_file(self, a: dict) -> str:
        Path(a["dest"]).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(a["src"], a["dest"]) if os.path.isfile(a["src"]) else shutil.copytree(a["src"], a["dest"])
        return f"✅ Copied → {a['dest']}"

    def _move_file(self, a: dict) -> str:
        shutil.move(a["src"], a["dest"])
        return f"✅ Moved → {a['dest']}"

    def _list_directory(self, a: dict) -> str:
        path, pattern = a.get("path","."), a.get("pattern")
        hidden = a.get("hidden", False)
        if pattern:
            matches = sorted(glob_lib.glob(os.path.join(path, pattern), recursive=True))
            return "\n".join(matches[:300]) or "No matches."
        try:
            entries = []
            for item in sorted(Path(path).iterdir()):
                if not hidden and item.name.startswith("."):
                    continue
                icon = "📁" if item.is_dir() else "📄"
                size = f" ({item.stat().st_size:,}b)" if item.is_file() else ""
                entries.append(f"{icon} {item.name}{size}")
            return "\n".join(entries) or "(empty)"
        except PermissionError:
            return f"Permission denied: {path}"

    def _search_in_files(self, a: dict) -> str:
        pat  = a["pattern"]
        path = a.get("path",".")
        fpat = a.get("file_pattern","*")
        flags = re.IGNORECASE if a.get("ignore_case", True) else 0
        try:
            rx = re.compile(pat, flags)
        except re.error as e:
            return f"Invalid regex: {e}"
        results = []
        for fp in glob_lib.glob(os.path.join(path,"**",fpat), recursive=True)[:500]:
            if not os.path.isfile(fp):
                continue
            try:
                with open(fp, encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if rx.search(line):
                            results.append(f"{fp}:{i}: {line.rstrip()}")
                        if len(results) >= 200:
                            break
            except Exception:
                pass
        return "\n".join(results) if results else f"No matches for '{pat}'"

    def _regex_replace(self, a: dict) -> str:
        pattern  = a["pattern"]
        repl     = a["replacement"]
        path     = a.get("path",".")
        fpat     = a.get("file_pattern","*.py")
        flags    = re.IGNORECASE if a.get("ignore_case", False) else 0
        dry_run  = a.get("dry_run", False)
        try:
            rx = re.compile(pattern, flags)
        except re.error as e:
            return f"Invalid regex: {e}"
        changed = []
        for fp in glob_lib.glob(os.path.join(path,"**",fpat), recursive=True)[:200]:
            if not os.path.isfile(fp):
                continue
            try:
                with open(fp, encoding="utf-8", errors="replace") as f:
                    content = f.read()
                new_content = rx.sub(repl, content)
                if new_content != content:
                    if not dry_run:
                        self.undo.snapshot(fp)
                        with open(fp, "w", encoding="utf-8") as f:
                            f.write(new_content)
                    count = len(rx.findall(content))
                    changed.append(f"  {fp} ({count} replacements)")
            except Exception:
                pass
        mode = "[DRY RUN] " if dry_run else ""
        return f"{mode}Replaced in {len(changed)} files:\n" + "\n".join(changed) if changed else "No matches found."

    def _bulk_write(self, a: dict) -> str:
        files = a.get("files", {})
        written = []
        for path, content in files.items():
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            if os.path.exists(path):
                self.undo.snapshot(path)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            written.append(path)
        return f"✅ Wrote {len(written)} files:\n" + "\n".join(f"  {p}" for p in written)

    def _diff_files(self, a: dict) -> str:
        def rt(x):
            return open(x, encoding="utf-8", errors="replace").read() if os.path.exists(x) else x
        diff = list(difflib.unified_diff(
            rt(a["path_a"]).splitlines(keepends=True), rt(a["path_b"]).splitlines(keepends=True),
            fromfile=a["path_a"], tofile=a["path_b"]
        ))
        return "".join(diff) if diff else "Identical."

    def _file_tree(self, a: dict) -> str:
        path    = a.get("path",".")
        max_d   = a.get("max_depth", 3)
        hidden  = a.get("hidden", False)
        lines   = []
        def walk(p: Path, depth: int, prefix: str):
            if depth > max_d:
                return
            try:
                entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
            except PermissionError:
                return
            for i, item in enumerate(entries):
                if not hidden and item.name.startswith("."):
                    continue
                is_last = (i == len(entries) - 1)
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{item.name}")
                if item.is_dir():
                    ext = "    " if is_last else "│   "
                    walk(item, depth+1, prefix+ext)
        lines.append(str(path))
        walk(Path(path), 1, "")
        return "\n".join(lines)

    def _find_todos(self, a: dict) -> str:
        path  = a.get("path",".")
        fpat  = a.get("file_pattern","*")
        tags  = a.get("tags", ["TODO","FIXME","HACK","BUG","NOTE","XXX"])
        pat   = re.compile(r"(" + "|".join(tags) + r")[:\s](.+)", re.IGNORECASE)
        results = []
        for fp in glob_lib.glob(os.path.join(path,"**",fpat), recursive=True)[:300]:
            if not os.path.isfile(fp):
                continue
            try:
                with open(fp, encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        m = pat.search(line)
                        if m:
                            results.append(f"{fp}:{i}: [{m.group(1).upper()}] {m.group(2).strip()}")
            except Exception:
                pass
        return "\n".join(results) if results else "No TODOs found."

    def _run_command(self, a: dict) -> str:
        env = {**os.environ, **(a.get("env") or {})}
        try:
            r = subprocess.run(
                a["command"], shell=True, cwd=a.get("cwd","."),
                timeout=a.get("timeout",30), capture_output=True,
                text=True, encoding="utf-8", errors="replace", env=env
            )
            parts = []
            if r.stdout.strip(): parts.append(f"STDOUT:\n{r.stdout.strip()}")
            if r.stderr.strip(): parts.append(f"STDERR:\n{r.stderr.strip()}")
            parts.append(f"Exit: {r.returncode}")
            return "\n".join(parts) or "(no output)"
        except subprocess.TimeoutExpired:
            return f"Timeout ({a.get('timeout',30)}s)"
        except Exception as e:
            return f"Error: {e}"

    def _background_run(self, a: dict) -> str:
        return self.bg.run(a["command"], a.get("name", f"job_{int(time.time())}"), a.get("cwd","."))

    def _bg_status(self, a: dict) -> str:
        name = a.get("name")
        return self.bg.list_all() if not name else self.bg.status(name)

    def _bg_tail(self, a: dict) -> str:
        return self.bg.tail_log(a["name"], a.get("lines",30))

    def _bg_kill(self, a: dict) -> str:
        return self.bg.kill(a["name"])

    def _execute_code(self, a: dict) -> str:
        code, lang = a["code"], a["language"]
        suffix = {"python":".py","javascript":".js","typescript":".ts","bash":".sh"}.get(lang,".txt")
        runner = {"python":"python","javascript":"node","typescript":"npx ts-node","bash":"bash"}.get(lang, lang)
        with tempfile.NamedTemporaryFile(suffix=suffix, mode="w", delete=False, encoding="utf-8") as f:
            f.write(code); tmp = f.name
        try:
            r = subprocess.run(f"{runner} {tmp}", shell=True, capture_output=True,
                               text=True, timeout=30, encoding="utf-8", errors="replace")
            parts = [f"[{lang.upper()}]"]
            if r.stdout.strip(): parts.append(r.stdout.strip())
            if r.stderr.strip(): parts.append(f"STDERR: {r.stderr.strip()}")
            parts.append(f"Exit: {r.returncode}")
            return "\n".join(parts)
        except subprocess.TimeoutExpired:
            return "Timeout (30s)"
        finally:
            os.unlink(tmp)

    def _web_search(self, a: dict) -> str:
        query, n = a["query"], a.get("num_results",5)
        if DDG_AVAILABLE:
            try:
                with DDGS() as d:
                    rs = list(d.text(query, max_results=n))
                return "\n---\n".join(f"**{r['title']}**\n{r['href']}\n{r['body']}" for r in rs) or "No results."
            except Exception:
                pass
        if REQUESTS_AVAILABLE:
            try:
                r = requests.get("https://api.duckduckgo.com/",
                    params={"q":query,"format":"json","no_redirect":"1","no_html":"1"},
                    headers={"User-Agent":"QwenBot/4.1"}, timeout=10)
                data = r.json()
                parts = []
                if data.get("Abstract"):
                    parts.append(f"**{data.get('Heading','')}**\n{data['Abstract']}\n{data.get('AbstractURL','')}")
                for item in data.get("RelatedTopics",[])[:n]:
                    if isinstance(item,dict) and item.get("Text"):
                        parts.append(f"- {item['Text']}\n  {item.get('FirstURL','')}")
                return "\n\n".join(parts) if parts else "No results."
            except Exception as e:
                return f"Search error: {e}"
        return "Install: pip install duckduckgo-search requests"

    def _fetch_url(self, a: dict) -> str:
        if not REQUESTS_AVAILABLE:
            return "Install: pip install requests"
        try:
            r = requests.get(a["url"], headers={"User-Agent":"QwenBot/4.1"}, timeout=15)
            r.raise_for_status()
            if a.get("extract_text", True):
                if BS4_AVAILABLE:
                    soup = BeautifulSoup(r.text, "html.parser")
                    for tag in soup(["script","style","nav","footer","aside","header"]):
                        tag.decompose()
                    return soup.get_text(separator="\n", strip=True)[:10000]
                return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text)).strip()[:10000]
            return r.text[:10000]
        except Exception as e:
            return f"Fetch error: {e}"

    def _http_request(self, a: dict) -> str:
        if not REQUESTS_AVAILABLE:
            return "Install: pip install requests"
        try:
            r = requests.request(a["method"], a["url"],
                headers=a.get("headers"), json=a.get("body"), params=a.get("params"), timeout=15)
            try:
                return json.dumps(r.json(), indent=2, ensure_ascii=False)[:5000]
            except Exception:
                return r.text[:5000]
        except Exception as e:
            return f"HTTP error: {e}"

    def _read_image(self, a: dict) -> str:
        path = a["path"]
        if not os.path.exists(path):
            return f"Not found: {path}"
        try:
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            ext = Path(path).suffix.lower().lstrip(".")
            mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png","gif":"gif","webp":"webp"}.get(ext,"jpeg")
            size = os.path.getsize(path)
            return f"[IMAGE: {path}, {size:,} bytes, base64 ready for vision models]\ndata:image/{mime};base64,{data[:100]}... (truncated, full data available)"
        except Exception as e:
            return f"Image read error: {e}"

    def _sqlite_query(self, a: dict) -> str:
        db   = a.get("database",":memory:")
        sql  = a["query"]
        params = a.get("params",[])
        try:
            conn = sqlite3.connect(db)
            conn.row_factory = sqlite3.Row
            cur  = conn.cursor()
            cur.execute(sql, params)
            if sql.strip().upper().startswith("SELECT"):
                rows = cur.fetchall()
                if not rows:
                    return "(no rows)"
                cols = [d[0] for d in cur.description]
                result = " | ".join(cols) + "\n" + "-"*60
                for row in rows[:50]:
                    result += "\n" + " | ".join(str(v) for v in row)
                return result
            else:
                conn.commit()
                return f"✅ Affected rows: {cur.rowcount}"
        except Exception as e:
            return f"SQL error: {e}"
        finally:
            try: conn.close()
            except Exception: pass

    def _git_operation(self, a: dict) -> str:
        op, xtra, cwd = a["operation"], a.get("args",""), a.get("cwd",".")
        cmd_map = {
            "status":   "git status",
            "diff":     f"git diff {xtra}",
            "log":      f"git log --oneline --graph --decorate -20 {xtra}",
            "add":      f"git add {xtra or '.'}",
            "commit":   f'git commit -m "{xtra}"',
            "push":     f"git push {xtra}",
            "pull":     f"git pull {xtra}",
            "branch":   f"git branch {xtra}",
            "checkout": f"git checkout {xtra}",
            "clone":    f"git clone {xtra}",
            "init":     "git init",
            "stash":    f"git stash {xtra}",
            "tag":      f"git tag {xtra}",
            "merge":    f"git merge {xtra}",
            "rebase":   f"git rebase {xtra}",
        }
        return self._run_command({"command": cmd_map.get(op, f"git {op} {xtra}"), "cwd": cwd})

    def _github_cli(self, a: dict) -> str:
        return self._run_command({"command":f"gh {a['command']}","cwd":a.get("cwd","."),"timeout":60})

    def _create_project(self, a: dict) -> str:
        name, ptype = a["name"], a["type"]
        base = Path(a.get("path",".")) / name
        templates = {
            "python": {
                f"{name}/__init__.py": "",
                f"{name}/main.py": f'"""Main module."""\n\ndef main() -> None:\n    print("Hello from {name}!")\n\nif __name__ == "__main__":\n    main()\n',
                "tests/__init__.py": "",
                "tests/test_main.py": f'from {name}.main import main\n\ndef test_main() -> None:\n    main()\n',
                "requirements.txt": "pytest\nmypy\nruff\n",
                "pyproject.toml": f'[project]\nname = "{name}"\nversion = "0.1.0"\n\n[tool.ruff]\nline-length = 100\n',
                ".gitignore": "__pycache__/\n*.pyc\n.venv/\n.env\ndist/\n.mypy_cache/\n.ruff_cache/\n",
                "README.md": f"# {name}\n\n## Install\n```bash\npip install -e .\n```\n\n## Run\n```bash\npython -m {name}\n```\n",
                "QWEN.md": f"# {name} — Project Context\n\nStack: Python\nMain module: {name}/main.py\nTests: tests/\n",
            },
            "fastapi": {
                "app/__init__.py": "",
                "app/main.py": 'from fastapi import FastAPI\nfrom app.routers import health\n\napp = FastAPI(title="API", version="1.0.0")\napp.include_router(health.router)\n',
                "app/routers/__init__.py": "",
                "app/routers/health.py": 'from fastapi import APIRouter\n\nrouter = APIRouter(prefix="/health", tags=["health"])\n\n@router.get("/")\nasync def health_check():\n    return {"status": "ok"}\n',
                "app/models/__init__.py": "",
                "tests/__init__.py": "",
                "tests/test_health.py": 'from fastapi.testclient import TestClient\nfrom app.main import app\n\nclient = TestClient(app)\n\ndef test_health():\n    r = client.get("/health/")\n    assert r.status_code == 200\n',
                "requirements.txt": "fastapi\nuvicorn[standard]\nhttpx\npytest\npytest-asyncio\n",
                ".gitignore": "__pycache__/\n*.pyc\n.venv/\n.env\n",
                "README.md": f"# {name}\n\n```bash\nuvicorn app.main:app --reload\n```\n",
                "QWEN.md": f"# {name}\n\nStack: FastAPI + Python\nEntry: app/main.py\nRouters: app/routers/\nTests: pytest tests/\n",
            },
            "react": {
                "src/App.tsx": 'import { useState } from "react";\n\nexport default function App(): JSX.Element {\n  const [count, setCount] = useState(0);\n  return (\n    <div>\n      <h1>Hello World!</h1>\n      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>\n    </div>\n  );\n}\n',
                "src/main.tsx": 'import React from "react";\nimport ReactDOM from "react-dom/client";\nimport App from "./App";\n\nReactDOM.createRoot(document.getElementById("root")!).render(\n  <React.StrictMode><App /></React.StrictMode>\n);\n',
                "src/index.css": "body { margin: 0; font-family: system-ui, sans-serif; }\n",
                "index.html": f'<!DOCTYPE html>\n<html lang="pt">\n<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{name}</title></head>\n<body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body>\n</html>\n',
                "package.json": json.dumps({"name":name,"version":"0.0.1","scripts":{"dev":"vite","build":"tsc && vite build","preview":"vite preview","lint":"eslint . --ext ts,tsx"},"devDependencies":{"@types/react":"^18","@vitejs/plugin-react":"^4","typescript":"^5","vite":"^5"},"dependencies":{"react":"^18","react-dom":"^18"}}, indent=2),
                "tsconfig.json": json.dumps({"compilerOptions":{"target":"ES2020","lib":["ES2020","DOM","DOM.Iterable"],"jsx":"react-jsx","strict":True,"module":"ESNext","moduleResolution":"bundler","noEmit":True},"include":["src"]}, indent=2),
                "vite.config.ts": 'import { defineConfig } from "vite";\nimport react from "@vitejs/plugin-react";\n\nexport default defineConfig({ plugins: [react()] });\n',
                ".gitignore": "node_modules/\ndist/\n.env\n.env.local\n",
                "QWEN.md": f"# {name}\n\nStack: React + TypeScript + Vite\nDev: npm run dev\nBuild: npm run build\n",
            },
        }
        scaffold = templates.get(ptype, templates["python"])
        created  = []
        for rel, content in scaffold.items():
            full = base / rel
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8")
            created.append(str(full))
        return f"✅ {ptype} '{name}' created ({len(created)} files):\n" + "\n".join(f"  {f}" for f in created)

    def _install_package(self, a: dict) -> str:
        mgr = a.get("manager","pip")
        cmds = {
            "pip":   f"pip install {a['package']}",
            "npm":   f"npm install {'--save-dev ' if a.get('dev') else ''}{a['package']}",
            "yarn":  f"yarn add {'--dev ' if a.get('dev') else ''}{a['package']}",
            "cargo": f"cargo add {a['package']}",
            "go":    f"go get {a['package']}",
        }
        return self._run_command({"command":cmds.get(mgr,f"pip install {a['package']}"),"cwd":a.get("cwd","."),"timeout":120})

    def _env_get(self, a: dict) -> str:
        key = a["key"]
        if key.lower() == "all":
            return "\n".join(f"{k}={v[:80]}" for k,v in sorted(os.environ.items()))
        val = os.environ.get(key)
        return f"{key}={val}" if val else f"{key} not set"

    # ── RAG METHODS ───────────────────────────────────────────────────────────
    def _rag_index(self, a: dict) -> str:
        if not self.rag:
            return "RAG not available. pip install chromadb sentence-transformers"
        return self.rag.index_directory(a.get("path", "."), force=a.get("force", False))

    def _rag_search(self, a: dict) -> str:
        if not self.rag:
            return "RAG not available."
        return self.rag.search(a["query"], n=a.get("n", 6), file_filter=a.get("file_filter", ""))

    # ── BROWSER METHODS ───────────────────────────────────────────────────────
    def _b(self):
        if not self.browser:
            raise RuntimeError("Browser not available. pip install playwright && playwright install chromium")
        return self.browser

    def _browser_open(self, a: dict) -> str:
        return self._b().open(a["url"], a.get("wait", "networkidle"))

    def _browser_click(self, a: dict) -> str:
        return self._b().click(a["selector"], a.get("timeout", 5000))

    def _browser_type(self, a: dict) -> str:
        return self._b().type_text(a["selector"], a["text"], a.get("clear", True))

    def _browser_screenshot(self, a: dict) -> str:
        return self._b().screenshot(a.get("path", ""), a.get("full_page", False))

    def _browser_get_text(self, a: dict) -> str:
        return self._b().get_text(a.get("selector", "body"), a.get("limit", 5000))

    def _browser_get_links(self, a: dict) -> str:
        return self._b().get_links(a.get("filter", ""))

    def _browser_run_js(self, a: dict) -> str:
        return self._b().run_js(a["code"])

    def _browser_get_inputs(self, _) -> str:
        return self._b().get_inputs()

    def _browser_scroll(self, a: dict) -> str:
        return self._b().scroll(a.get("direction", "down"), a.get("amount", 500))

    def _browser_wait_for(self, a: dict) -> str:
        return self._b().wait_for(a["selector"], a.get("timeout", 10000))

    # ── CONTEXT7 METHODS ──────────────────────────────────────────────────────
    def _context7_search(self, a: dict) -> str:
        if not REQUESTS_AVAILABLE:
            return "Install: pip install requests"
        try:
            r = requests.get(
                f"{CONTEXT7_URL}/libs/search",
                params={"libraryName": a["library"], "query": a.get("query", "")},
                headers={"Authorization": f"Bearer {CONTEXT7_KEY}"},
                timeout=10
            )
            results = r.json().get("results", [])[:5]
            return "\n\n".join(
                f"**{x['title']}** (id: `{x['id']}`)\n"
                f"{x.get('description','')}\n"
                f"Tokens: {x.get('totalTokens',0):,} | Stars: {x.get('stars',0):,} | Score: {x.get('benchmarkScore',0)}"
                for x in results
            ) or "No results."
        except Exception as e:
            return f"Context7 search error: {e}"

    def _context7_get_docs(self, a: dict) -> str:
        if not REQUESTS_AVAILABLE:
            return "Install: pip install requests"
        try:
            lib_id = a["library_id"]   # e.g. "/microsoft/playwright"
            r = requests.get(
                f"{CONTEXT7_URL}{lib_id}",
                params={"query": a.get("query", ""), "tokens": a.get("tokens", 6000)},
                headers={"Authorization": f"Bearer {CONTEXT7_KEY}"},
                timeout=20
            )
            return r.text[:10000]
        except Exception as e:
            return f"Context7 docs error: {e}"

    # ── OLLAMA METHODS ────────────────────────────────────────────────────────
    def _ollama_chat(self, a: dict) -> str:
        if not self.ollama:
            return "Ollama not initialized."
        if not self.ollama.is_available():
            return "Ollama not running. Start with: ollama serve"
        msgs = [{"role": "user", "content": a["prompt"]}]
        if a.get("system"):
            msgs.insert(0, {"role": "system", "content": a["system"]})
        return self.ollama.chat(msgs, a.get("max_tokens", 2048))

    # ── TDD METHOD ────────────────────────────────────────────────────────────
    def _tdd_run(self, a: dict) -> str:
        if not self.tdd:
            return "TDD not initialized."
        return self.tdd.run(
            a["task"],
            test_framework=a.get("framework", "auto"),
            max_iter=a.get("max_iterations", 10)
        )

    # ── v6.0 CODE INTELLIGENCE TOOLS ─────────────────────────────────────────
    def _analyze_code(self, a: dict) -> str:
        if not self.code_analyzer:
            return "CodeAnalyzer not available."
        return self.code_analyzer.report(a.get("path", "."))

    def _analyze_directory(self, a: dict) -> str:
        if not self.code_analyzer:
            return "CodeAnalyzer not available."
        return self.code_analyzer.report(a.get("path", "."))

    def _security_scan(self, a: dict) -> str:
        if not self.security_scanner:
            return "SecurityScanner not available."
        path = a.get("path", ".")
        import os as _os
        if _os.path.isfile(path):
            return self.security_scanner.quick_scan(path)
        result = self.security_scanner.scan_directory(path)
        return result["report"]

    def _refactor_rename(self, a: dict) -> str:
        if not self.refactor_engine:
            return "RefactorEngine not available."
        r = self.refactor_engine.rename_symbol(
            a["old_name"], a["new_name"],
            file_pattern=a.get("file_pattern", "*.py"),
            whole_word=a.get("whole_word", True),
        )
        return self.refactor_engine.format_result(r)

    def _refactor_extract_fn(self, a: dict) -> str:
        if not self.refactor_engine:
            return "RefactorEngine not available."
        r = self.refactor_engine.extract_function(
            a["path"], int(a["start_line"]), int(a["end_line"]),
            a["function_name"], a.get("params", []),
        )
        return self.refactor_engine.format_result(r)

    def _refactor_extract_var(self, a: dict) -> str:
        if not self.refactor_engine:
            return "RefactorEngine not available."
        r = self.refactor_engine.extract_variable(
            a["path"], int(a["line"]), a["expression"], a["var_name"]
        )
        return self.refactor_engine.format_result(r)

    def _refactor_inline_var(self, a: dict) -> str:
        if not self.refactor_engine:
            return "RefactorEngine not available."
        r = self.refactor_engine.inline_variable(a["path"], a["var_name"])
        return self.refactor_engine.format_result(r)

    def _generate_tests(self, a: dict) -> str:
        if not self.test_generator:
            return "TestGenerator not available."
        gen = self.test_generator.generate_test_file(
            a["path"],
            framework=a.get("framework", "pytest"),
            output_dir=a.get("output_dir", "tests"),
        )
        return self.test_generator.format_result(gen)

    def _fill_coverage_gaps(self, a: dict) -> str:
        if not self.test_generator:
            return "TestGenerator not available."
        return self.test_generator.fill_coverage_gaps(
            a["path"],
            test_dir=a.get("test_dir", "tests"),
            framework=a.get("framework", "pytest"),
        )

    def _run_tests_tool(self, a: dict) -> str:
        if not self.test_generator:
            return "TestGenerator not available."
        result = self.test_generator.run_tests(
            a.get("path", "tests"),
            framework=a.get("framework", "pytest"),
        )
        if "error" in result:
            return f"❌ {result['error']}"
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        return f"{status} | {result.get('total',0)} tests | {result.get('failed',0)} failed\n{result.get('output','')[-1500:]}"

    # ── v6.0 AGENT TOOLS ─────────────────────────────────────────────────────
    def _agent_run(self, a: dict) -> str:
        if not self.agent_pool:
            return "AgentPool not available."
        role_str = a.get("role", "coder")
        try:
            role = AgentRole(role_str)
        except Exception:
            role = AgentRole.CODER
        result = self.agent_pool.run_single(a["task"], role=role, context=a.get("context", ""))
        return f"[{role.value.upper()} agent] {'✅' if result.success else '❌'} ({result.elapsed:.1f}s)\n{result.output}"

    def _agent_pipeline(self, a: dict) -> str:
        if not self.agent_pool:
            return "AgentPool not available."
        roles_raw = a.get("roles", ["planner", "coder", "reviewer"])
        roles = []
        for r in roles_raw:
            try:
                roles.append(AgentRole(r))
            except Exception:
                roles.append(AgentRole.CODER)
        result = self.agent_pool.pipeline(a["task"], context=a.get("context", ""), roles=roles)
        return f"Pipeline ({len(result.results)} stages, {result.total_time:.1f}s):\n{result.merged}"

    def _agent_multi_review(self, a: dict) -> str:
        if not self.agent_pool:
            return "AgentPool not available."
        code = a.get("code", "")
        if not code and a.get("path"):
            import os as _os
            if _os.path.exists(a["path"]):
                with open(a["path"], encoding="utf-8") as f:
                    code = f.read()
        return self.agent_pool.multi_review(code, a.get("path", ""))

    def _critic_review(self, a: dict) -> str:
        if not self.critic_agent:
            return "CriticAgent not available."
        code = a.get("code", "")
        if not code and a.get("path"):
            import os as _os
            if _os.path.exists(a["path"]):
                with open(a["path"], encoding="utf-8") as f:
                    code = f.read()
        result = self.critic_agent.review_and_revise(
            code, task_context=a.get("context", ""),
            language=a.get("language", "python"),
            max_iterations=a.get("max_iterations", 2),
        )
        return self.critic_agent.format_report(result)

    def _critic_gate(self, a: dict) -> str:
        if not self.critic_agent:
            return "CriticAgent not available."
        code = a.get("code", "")
        approved, final_code = self.critic_agent.gate(
            code, task_context=a.get("context", ""),
            language=a.get("language", "python"),
        )
        if approved:
            return f"✅ Code approved by CriticAgent.\n\n{final_code}"
        return f"❌ Code not approved — see revision:\n\n{final_code}"

    # ── v6.0 MEMORY AGENT TOOLS ───────────────────────────────────────────────
    def _mem_agent_remember(self, a: dict) -> str:
        if not self.memory_agent:
            return "MemoryAgent not available."
        return self.memory_agent.remember(
            a["content"], type=a.get("type", "fact"),
            importance=float(a.get("importance", 1.0)),
        )

    def _mem_agent_recall(self, a: dict) -> str:
        if not self.memory_agent:
            return "MemoryAgent not available."
        return self.memory_agent.recall_formatted(a["query"], top_k=a.get("top_k", 6))

    # ── v6.0 REASONING TOOLS ─────────────────────────────────────────────────
    def _reason_tool(self, a: dict) -> str:
        if not self.reasoning_engine:
            return "ReasoningEngine not available."
        result = self.reasoning_engine.reason(
            problem=a["problem"],
            context=a.get("context", ""),
            use_tot=a.get("use_tot", False),
            reflect=a.get("reflect", True),
            cot_steps=a.get("cot_steps", 3),
        )
        conf = result.get("confidence", {})
        return (
            f"🧠 Reasoning complete ({result['elapsed']}s) | "
            f"Confidence: {conf.get('score',0)}/100 ({conf.get('level','?')})\n\n"
            f"{result['answer']}"
        )

    def _plan_task_tool(self, a: dict) -> str:
        if not self.agent_planner:
            return "AgentPlanner not available."
        tasks = self.agent_planner.decompose(a["goal"], context=a.get("context", ""))
        return self.agent_planner.render_plan()


# ── UNRESTRICTED EXECUTOR (GOD MODE) ─────────────────────────────────────────
class UnrestrictedExecutor:
    """Power tools with no approval gates. safe_mode=false only.
    Handles raw shell, force file ops, process management, system info, network."""

    def __init__(self, config: dict):
        self.config = config

    def execute(self, name: str, args: dict) -> str:
        dispatch = {
            "raw_shell":       self._raw_shell,
            "force_write":     self._force_write,
            "force_delete":    self._force_delete,
            "force_read":      self._force_read,
            "kill_process":    self._kill_process,
            "process_list":    self._process_list,
            "system_info":     self._system_info,
            "network_scan":    self._network_scan,
            "extract_archive": self._extract_archive,
            "compress_files":  self._compress_files,
            "env_set":         self._env_set,
            "clipboard_read":  self._clipboard_read,
            "clipboard_write": self._clipboard_write,
            "open_file_os":    self._open_file_os,
            "find_files":      self._find_files,
        }
        fn = dispatch.get(name)
        if not fn:
            return f"Unknown god-mode tool: {name}"
        try:
            return str(fn(args))
        except Exception as e:
            return f"[GOD MODE] Error in {name}: {type(e).__name__}: {e}"

    def _raw_shell(self, a: dict) -> str:
        """Execute any shell command directly, elevated if possible."""
        cmd     = a["command"]
        cwd     = a.get("cwd", ".")
        timeout = a.get("timeout", 60)
        stdin_input = a.get("stdin", None)

        try:
            result = subprocess.run(
                cmd, shell=True, cwd=cwd, timeout=timeout,
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                input=stdin_input
            )
            parts = []
            if result.stdout.strip():
                parts.append(f"STDOUT:\n{result.stdout.strip()}")
            if result.stderr.strip():
                parts.append(f"STDERR:\n{result.stderr.strip()}")
            parts.append(f"Exit: {result.returncode}")
            return "\n".join(parts) or "(no output)"
        except subprocess.TimeoutExpired:
            return f"Timeout after {timeout}s"

    def _force_write(self, a: dict) -> str:
        """Write file without any diff or approval."""
        path    = a["path"]
        content = a["content"]
        backup  = a.get("backup", False)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        if backup and os.path.exists(path):
            shutil.copy2(path, f"{path}.bak")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        lines = content.count("\n") + 1
        return f"✅ Force written {lines} lines → {path}"

    def _force_delete(self, a: dict) -> str:
        """Delete file or directory immediately, no confirmation."""
        path    = a["path"]
        pattern = a.get("pattern")
        deleted = []
        if pattern:
            for fp in glob_lib.glob(os.path.join(path, pattern), recursive=True):
                try:
                    os.remove(fp) if os.path.isfile(fp) else shutil.rmtree(fp)
                    deleted.append(fp)
                except Exception as e:
                    deleted.append(f"FAILED:{fp}:{e}")
            return f"✅ Deleted {len(deleted)} items"
        if not os.path.exists(path):
            return f"Not found: {path}"
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return f"✅ Deleted: {path}"

    def _force_read(self, a: dict) -> str:
        """Read any file including binary, no size limits."""
        path     = a["path"]
        encoding = a.get("encoding", "utf-8")
        binary   = a.get("binary", False)
        limit    = a.get("limit", 50000)
        if not os.path.exists(path):
            return f"Not found: {path}"
        if binary:
            with open(path, "rb") as f:
                data = f.read(limit)
            return base64.b64encode(data).decode()
        with open(path, encoding=encoding, errors="replace") as f:
            return f.read(limit)

    def _kill_process(self, a: dict) -> str:
        """Kill process by PID or name."""
        import signal
        pid  = a.get("pid")
        name = a.get("name")
        force = a.get("force", False)

        if pid:
            sig = signal.SIGKILL if (force and os.name != "nt") else signal.SIGTERM
            try:
                os.kill(int(pid), sig)
                return f"✅ Killed PID {pid}"
            except Exception as e:
                return f"Kill PID {pid} failed: {e}"

        if name:
            cmd = f"taskkill /F /IM {name}" if os.name == "nt" else f"pkill {'--signal KILL' if force else ''} {name}"
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return r.stdout.strip() or r.stderr.strip() or f"Sent kill to {name}"

        return "Provide pid or name."

    def _process_list(self, a: dict) -> str:
        """List running processes with CPU/memory info."""
        filter_name = a.get("filter", "")
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
                try:
                    info = p.info
                    if filter_name and filter_name.lower() not in info["name"].lower():
                        continue
                    mem = info["memory_info"].rss // 1024 // 1024 if info["memory_info"] else 0
                    procs.append(f"{info['pid']:6d} | {info['name'][:30]:30s} | {info['cpu_percent']:5.1f}% | {mem:5d}MB | {info['status']}")
                except Exception:
                    pass
            header = f"{'PID':6s} | {'NAME':30s} | {'CPU':5s} | {'MEM':5s} | STATUS"
            return header + "\n" + "-"*70 + "\n" + "\n".join(procs[:50])
        except ImportError:
            # Fallback to tasklist/ps
            cmd = "tasklist /FO CSV /NH" if os.name == "nt" else "ps aux --sort=-%mem"
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            lines = r.stdout.strip().splitlines()
            if filter_name:
                lines = [l for l in lines if filter_name.lower() in l.lower()]
            return "\n".join(lines[:40])

    def _system_info(self, a: dict) -> str:
        """Detailed system info: CPU, RAM, disk, GPU, network interfaces."""
        sections = a.get("sections", ["all"])
        info     = []

        try:
            import psutil, platform
            if "all" in sections or "os" in sections:
                info.append(f"OS: {platform.system()} {platform.release()} {platform.machine()}")
                info.append(f"Python: {platform.python_version()}")
                info.append(f"CWD: {os.getcwd()}")

            if "all" in sections or "cpu" in sections:
                cpu = psutil.cpu_percent(interval=1)
                info.append(f"CPU: {psutil.cpu_count()} cores | {cpu:.1f}% usage")
                freq = psutil.cpu_freq()
                if freq:
                    info.append(f"CPU Freq: {freq.current:.0f}MHz (max {freq.max:.0f}MHz)")

            if "all" in sections or "ram" in sections:
                vm = psutil.virtual_memory()
                info.append(f"RAM: {vm.used//1024//1024:,}MB / {vm.total//1024//1024:,}MB ({vm.percent:.1f}% used)")
                sw = psutil.swap_memory()
                info.append(f"Swap: {sw.used//1024//1024:,}MB / {sw.total//1024//1024:,}MB")

            if "all" in sections or "disk" in sections:
                for part in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        info.append(f"Disk {part.device}: {usage.used//1024//1024//1024:.1f}GB / {usage.total//1024//1024//1024:.1f}GB ({usage.percent:.1f}%)")
                    except Exception:
                        pass

            if "all" in sections or "network" in sections:
                for name, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family == 2:  # AF_INET
                            info.append(f"Net {name}: {addr.address}")

            if "all" in sections or "gpu" in sections:
                try:
                    r = subprocess.run("nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader",
                                       shell=True, capture_output=True, text=True, timeout=5)
                    if r.returncode == 0 and r.stdout.strip():
                        info.append(f"GPU: {r.stdout.strip()}")
                except Exception:
                    info.append("GPU: nvidia-smi not available")

        except ImportError:
            # Fallback without psutil
            info.append(f"OS: {os.name} | CWD: {os.getcwd()}")
            r = subprocess.run("systeminfo" if os.name == "nt" else "uname -a",
                               shell=True, capture_output=True, text=True)
            info.append(r.stdout[:1000])

        return "\n".join(info)

    def _network_scan(self, a: dict) -> str:
        """Network diagnostics: ping, port check, interface info."""
        target = a.get("target", "8.8.8.8")
        ports  = a.get("ports", [])
        mode   = a.get("mode", "ping")
        results = []

        if mode in ("ping", "all"):
            cmd = f"ping -n 3 {target}" if os.name == "nt" else f"ping -c 3 {target}"
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            results.append(f"PING {target}:\n{r.stdout.strip()}")

        if ports or mode in ("ports", "all"):
            import socket
            for port in (ports or [22, 80, 443, 3000, 8000, 8080, 5432, 3306]):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    code = sock.connect_ex((target, int(port)))
                    sock.close()
                    status = "OPEN" if code == 0 else "CLOSED"
                    results.append(f"Port {port}: {status}")
                except Exception:
                    results.append(f"Port {port}: ERROR")

        if mode in ("dns", "all"):
            try:
                import socket
                ip = socket.gethostbyname(target)
                results.append(f"DNS {target} → {ip}")
            except Exception as e:
                results.append(f"DNS failed: {e}")

        return "\n".join(results) if results else "No results."

    def _extract_archive(self, a: dict) -> str:
        """Extract zip, tar.gz, tar.bz2, 7z archives."""
        import zipfile, tarfile
        src  = a["path"]
        dest = a.get("dest", os.path.dirname(src) or ".")
        Path(dest).mkdir(parents=True, exist_ok=True)

        if src.endswith(".zip"):
            with zipfile.ZipFile(src) as z:
                z.extractall(dest)
                names = z.namelist()
            return f"✅ Extracted {len(names)} files → {dest}"

        if any(src.endswith(e) for e in (".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".tar")):
            with tarfile.open(src) as t:
                names = t.getnames()
                t.extractall(dest)
            return f"✅ Extracted {len(names)} files → {dest}"

        # Fallback to system command (7z, unrar, etc.)
        r = subprocess.run(f"7z x {src} -o{dest} -y", shell=True, capture_output=True, text=True)
        if r.returncode == 0:
            return f"✅ Extracted via 7z → {dest}"
        return f"Unknown format or 7z not available: {src}"

    def _compress_files(self, a: dict) -> str:
        """Compress files/dirs into archive."""
        import zipfile
        output  = a["output"]
        sources = a.get("sources", [a.get("path", ".")])
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
            for src in sources:
                if os.path.isfile(src):
                    z.write(src)
                elif os.path.isdir(src):
                    for fp in glob_lib.glob(os.path.join(src, "**", "*"), recursive=True):
                        if os.path.isfile(fp):
                            z.write(fp)
        size = os.path.getsize(output)
        return f"✅ Compressed → {output} ({size:,} bytes)"

    def _env_set(self, a: dict) -> str:
        """Set environment variable in current process."""
        key = a["key"]
        val = a["value"]
        os.environ[key] = str(val)
        return f"✅ {key}={val}"

    def _clipboard_read(self, _) -> str:
        try:
            import pyperclip
            return pyperclip.paste()
        except Exception:
            r = subprocess.run("powershell Get-Clipboard" if os.name == "nt" else "xclip -o",
                               shell=True, capture_output=True, text=True)
            return r.stdout.strip()

    def _clipboard_write(self, a: dict) -> str:
        text = a["text"]
        try:
            import pyperclip
            pyperclip.copy(text)
            return f"✅ Clipboard set ({len(text)} chars)"
        except Exception:
            cmd = f'echo {text} | clip' if os.name == "nt" else f'echo {text} | xclip -sel clip'
            subprocess.run(cmd, shell=True)
            return "✅ Clipboard set"

    def _open_file_os(self, a: dict) -> str:
        """Open file/URL with default OS application."""
        path = a["path"]
        import subprocess as sp, platform as _platform
        _sys = _platform.system()
        if _sys == "Windows":
            os.startfile(path)
        elif _sys == "Darwin":
            sp.run(["open", path])
        else:
            sp.run(["xdg-open", path])
        return f"✅ Opened: {path}"

    def _find_files(self, a: dict) -> str:
        """Find files by name pattern, size, or modified date."""
        root     = a.get("root", ".")
        pattern  = a.get("pattern", "*")
        min_size = a.get("min_size_kb", 0) * 1024
        max_size = a.get("max_size_kb", 0) * 1024 * 1024
        days     = a.get("modified_days")
        results  = []
        now      = time.time()

        for fp in glob_lib.glob(os.path.join(root, "**", pattern), recursive=True):
            if not os.path.isfile(fp):
                continue
            try:
                st = os.stat(fp)
                if min_size and st.st_size < min_size:
                    continue
                if max_size and st.st_size > max_size:
                    continue
                if days and (now - st.st_mtime) > days * 86400:
                    continue
                results.append(f"{fp} ({st.st_size:,}b)")
            except Exception:
                pass

        return "\n".join(results[:200]) if results else "No files found."


def build_godmode_tools() -> list:
    """God Mode tool schemas — no approval gates."""
    return [
        _tool("raw_shell",       "Execute ANY shell command directly. No approval, full output.",
              {"command":{"type":"string"},"cwd":{"type":"string"},"timeout":{"type":"integer"},"stdin":{"type":"string"}}, ["command"]),
        _tool("force_write",     "Write file immediately, no diff, no approval. Optional backup.",
              {"path":{"type":"string"},"content":{"type":"string"},"backup":{"type":"boolean"}}, ["path","content"]),
        _tool("force_delete",    "Delete files/dirs immediately. Supports glob patterns.",
              {"path":{"type":"string"},"pattern":{"type":"string"}}, ["path"]),
        _tool("force_read",      "Read any file, no size limit, supports binary.",
              {"path":{"type":"string"},"limit":{"type":"integer"},"binary":{"type":"boolean"},"encoding":{"type":"string"}}, ["path"]),
        _tool("kill_process",    "Kill process by PID or name. force=true for SIGKILL.",
              {"pid":{"type":"integer"},"name":{"type":"string"},"force":{"type":"boolean"}}, []),
        _tool("process_list",    "List all running processes with CPU/memory. Optional name filter.",
              {"filter":{"type":"string"}}, []),
        _tool("system_info",     "Full system info: CPU, RAM, disk, GPU, network interfaces.",
              {"sections":{"type":"array","items":{"type":"string"}}}, []),
        _tool("network_scan",    "Network diagnostics: ping, port check, DNS lookup.",
              {"target":{"type":"string"},"ports":{"type":"array","items":{"type":"integer"}},"mode":{"type":"string","enum":["ping","ports","dns","all"]}}, []),
        _tool("extract_archive", "Extract zip, tar.gz, tar.bz2, 7z archives.",
              {"path":{"type":"string"},"dest":{"type":"string"}}, ["path"]),
        _tool("compress_files",  "Compress files/directories into a zip archive.",
              {"output":{"type":"string"},"sources":{"type":"array","items":{"type":"string"}}}, ["output"]),
        _tool("env_set",         "Set environment variable in current process.",
              {"key":{"type":"string"},"value":{"type":"string"}}, ["key","value"]),
        _tool("clipboard_read",  "Read clipboard contents.",   {}, []),
        _tool("clipboard_write", "Write text to clipboard.",
              {"text":{"type":"string"}}, ["text"]),
        _tool("open_file_os",    "Open file/URL with default OS app.",
              {"path":{"type":"string"}}, ["path"]),
        _tool("find_files",      "Find files by name pattern, min/max size, modified date.",
              {"root":{"type":"string"},"pattern":{"type":"string"},"min_size_kb":{"type":"integer"},"max_size_kb":{"type":"integer"},"modified_days":{"type":"integer"}}, []),
    ]


# ── TOOLS SCHEMA ──────────────────────────────────────────────────────────────
def build_tools(extra_mcp: list = None) -> list:
    tools = [
        _tool("read_file",      "Read file. ALWAYS call before editing.",
              {"path":{"type":"string"},"start_line":{"type":"integer"},"end_line":{"type":"integer"}}, ["path"]),
        _tool("write_file",     "Write/create file. Shows diff.",
              {"path":{"type":"string"},"content":{"type":"string"}}, ["path","content"]),
        _tool("edit_file",      "Replace exact string in file.",
              {"path":{"type":"string"},"old_string":{"type":"string"},"new_string":{"type":"string"}}, ["path","old_string","new_string"]),
        _tool("delete_file",    "Delete file or directory.",
              {"path":{"type":"string"},"recursive":{"type":"boolean"}}, ["path"]),
        _tool("copy_file",      "Copy file/dir.",
              {"src":{"type":"string"},"dest":{"type":"string"}}, ["src","dest"]),
        _tool("move_file",      "Move/rename file/dir.",
              {"src":{"type":"string"},"dest":{"type":"string"}}, ["src","dest"]),
        _tool("list_directory", "List dir, optional glob pattern like '**/*.py'.",
              {"path":{"type":"string"},"pattern":{"type":"string"},"hidden":{"type":"boolean"}}, []),
        _tool("search_in_files","Search regex across files (like ripgrep).",
              {"pattern":{"type":"string"},"path":{"type":"string"},"file_pattern":{"type":"string"},"ignore_case":{"type":"boolean"}}, ["pattern"]),
        _tool("regex_replace",  "Replace regex across multiple files at once.",
              {"pattern":{"type":"string"},"replacement":{"type":"string"},"path":{"type":"string"},"file_pattern":{"type":"string"},"ignore_case":{"type":"boolean"},"dry_run":{"type":"boolean"}}, ["pattern","replacement"]),
        _tool("bulk_write",     "Write multiple files at once. files={path:content}.",
              {"files":{"type":"object","description":"Map of path → content"}}, ["files"]),
        _tool("diff_files",     "Unified diff between two files.",
              {"path_a":{"type":"string"},"path_b":{"type":"string"}}, ["path_a","path_b"]),
        _tool("file_tree",      "Visual tree of directory structure.",
              {"path":{"type":"string"},"max_depth":{"type":"integer"},"hidden":{"type":"boolean"}}, []),
        _tool("find_todos",     "Find TODO/FIXME/HACK/BUG comments in codebase.",
              {"path":{"type":"string"},"file_pattern":{"type":"string"},"tags":{"type":"array","items":{"type":"string"}}}, []),
        _tool("get_current_time","Get current date, time and timezone. Use this when user asks what time/date it is.",
              {"format":{"type":"string","description":"strftime format, e.g. '%H:%M:%S' or '%Y-%m-%d %H:%M'"}}, []),
        _tool("run_command",    "Execute shell command for tests, builds, installs.",
              {"command":{"type":"string"},"cwd":{"type":"string"},"timeout":{"type":"integer"},"env":{"type":"object"}}, ["command"]),
        _tool("background_run", "Run long command in background. Returns immediately with log path.",
              {"command":{"type":"string"},"name":{"type":"string"},"cwd":{"type":"string"}}, ["command"]),
        _tool("bg_status",      "Check background process status.",
              {"name":{"type":"string"}}, []),
        _tool("bg_tail",        "Tail background process log.",
              {"name":{"type":"string"},"lines":{"type":"integer"}}, ["name"]),
        _tool("bg_kill",        "Kill background process.",
              {"name":{"type":"string"}}, ["name"]),
        _tool("execute_code",   "Run code inline. Languages: python, javascript, bash, typescript.",
              {"code":{"type":"string"},"language":{"type":"string","enum":["python","javascript","bash","typescript"]}}, ["code","language"]),
        _tool("web_search",     "Search the web for docs, packages, error fixes.",
              {"query":{"type":"string"},"num_results":{"type":"integer"}}, ["query"]),
        _tool("fetch_url",      "Fetch webpage or raw URL content.",
              {"url":{"type":"string"},"extract_text":{"type":"boolean"}}, ["url"]),
        _tool("http_request",   "Make any HTTP request to an API.",
              {"method":{"type":"string","enum":["GET","POST","PUT","PATCH","DELETE"]},"url":{"type":"string"},"headers":{"type":"object"},"body":{"type":"object"},"params":{"type":"object"}}, ["method","url"]),
        _tool("read_image",     "Read image file for vision/multimodal analysis.",
              {"path":{"type":"string"}}, ["path"]),
        _tool("sqlite_query",   "Query or update a SQLite database.",
              {"query":{"type":"string"},"database":{"type":"string"},"params":{"type":"array"}}, ["query"]),
        _tool("git_operation",  "Git: status, diff, log, add, commit, push, pull, branch, stash, tag, merge.",
              {"operation":{"type":"string","enum":["status","diff","log","add","commit","push","pull","branch","checkout","clone","init","stash","tag","merge","rebase"]},"args":{"type":"string"},"cwd":{"type":"string"}}, ["operation"]),
        _tool("github_cli",     "GitHub CLI (gh): create PR, issues, check CI, releases.",
              {"command":{"type":"string"},"cwd":{"type":"string"}}, ["command"]),
        _tool("memory_save",    "Save info to persistent memory.",
              {"key":{"type":"string"},"content":{"type":"string"},"type":{"type":"string","enum":["user","project","feedback","reference"]}}, ["key","content"]),
        _tool("memory_recall",  "Search persistent memory.",
              {"query":{"type":"string"}}, ["query"]),
        _tool("memory_list",    "List all memories.",
              {}, []),
        _tool("create_project", "Scaffold new project: python, fastapi, react, nodejs.",
              {"name":{"type":"string"},"type":{"type":"string","enum":["python","fastapi","django","nodejs","react","nextjs","rust","go"]},"path":{"type":"string"}}, ["name","type"]),
        _tool("install_package","Install packages via pip/npm/yarn/cargo.",
              {"package":{"type":"string"},"manager":{"type":"string","enum":["pip","npm","yarn","cargo","go"]},"dev":{"type":"boolean"},"cwd":{"type":"string"}}, ["package"]),
        _tool("env_get",        "Get environment variable(s). Use key='all' for all.",
              {"key":{"type":"string"}}, ["key"]),
        _tool("undo",           "Undo last file change.",
              {}, []),
        _tool("undo_history",   "Show undo stack.",
              {}, []),
        # ── RAG ──────────────────────────────────────────────────────────
        _tool("rag_index",   "Index directory into semantic vector DB for search.",
              {"path":{"type":"string"},"force":{"type":"boolean"}}, []),
        _tool("rag_search",  "Semantic search across entire codebase. Better than grep for concepts.",
              {"query":{"type":"string"},"n":{"type":"integer"},"file_filter":{"type":"string"}}, ["query"]),
        _tool("rag_stats",   "Show RAG index stats.",  {}, []),
        _tool("rag_clear",   "Clear RAG index.",       {}, []),
        # ── BROWSER ──────────────────────────────────────────────────────
        _tool("browser_open",       "Open a URL in browser.",
              {"url":{"type":"string"},"wait":{"type":"string"}}, ["url"]),
        _tool("browser_click",      "Click element by CSS selector.",
              {"selector":{"type":"string"},"timeout":{"type":"integer"}}, ["selector"]),
        _tool("browser_type",       "Type text into input field.",
              {"selector":{"type":"string"},"text":{"type":"string"},"clear":{"type":"boolean"}}, ["selector","text"]),
        _tool("browser_screenshot", "Take screenshot of current page.",
              {"path":{"type":"string"},"full_page":{"type":"boolean"}}, []),
        _tool("browser_get_text",   "Get visible text from page or element.",
              {"selector":{"type":"string"},"limit":{"type":"integer"}}, []),
        _tool("browser_get_links",  "Get all links on current page.",
              {"filter":{"type":"string"}}, []),
        _tool("browser_run_js",     "Execute JavaScript in browser.",
              {"code":{"type":"string"}}, ["code"]),
        _tool("browser_get_inputs", "Get all form inputs on page.", {}, []),
        _tool("browser_scroll",     "Scroll page.",
              {"direction":{"type":"string","enum":["up","down"]},"amount":{"type":"integer"}}, []),
        _tool("browser_wait_for",   "Wait for element to appear.",
              {"selector":{"type":"string"},"timeout":{"type":"integer"}}, ["selector"]),
        _tool("browser_close",      "Close browser.", {}, []),
        # ── CONTEXT7 ─────────────────────────────────────────────────────
        _tool("context7_search",   "Search Context7 for library documentation.",
              {"library":{"type":"string"},"query":{"type":"string"}}, ["library"]),
        _tool("context7_get_docs", "Get actual documentation from Context7 for a library.",
              {"library_id":{"type":"string"},"query":{"type":"string"},"tokens":{"type":"integer"}}, ["library_id"]),
        # ── OLLAMA ───────────────────────────────────────────────────────
        _tool("ollama_chat",   "Chat with local Ollama model (fast, offline, free).",
              {"prompt":{"type":"string"},"system":{"type":"string"},"max_tokens":{"type":"integer"}}, ["prompt"]),
        _tool("ollama_models", "List available Ollama models.", {}, []),
        _tool("ollama_pull",   "Pull/download an Ollama model.",
              {"model":{"type":"string"}}, ["model"]),
        # ── TDD ──────────────────────────────────────────────────────────
        _tool("tdd_run",       "Run autonomous TDD loop: write tests → code → fix until green.",
              {"task":{"type":"string"},"framework":{"type":"string"},"max_iterations":{"type":"integer"}}, ["task"]),
        # ── v6.0 CODE INTELLIGENCE ───────────────────────────────────────
        _tool("analyze_code",    "AST-based analysis: complexity, dead code, issues, maintainability index.",
              {"path":{"type":"string"}}, ["path"]),
        _tool("analyze_directory","Analyze entire directory: hotspots, duplicates, all issues.",
              {"path":{"type":"string"}}, []),
        _tool("security_scan",   "OWASP Top 10 scan: secrets, injection, XSS, crypto issues, dep CVEs.",
              {"path":{"type":"string"}}, []),
        _tool("refactor_rename", "Safely rename symbol across all files. Whole-word by default.",
              {"old_name":{"type":"string"},"new_name":{"type":"string"},"file_pattern":{"type":"string"},"whole_word":{"type":"boolean"}}, ["old_name","new_name"]),
        _tool("refactor_extract_fn", "Extract lines into a new function.",
              {"path":{"type":"string"},"start_line":{"type":"integer"},"end_line":{"type":"integer"},"function_name":{"type":"string"},"params":{"type":"array","items":{"type":"string"}}}, ["path","start_line","end_line","function_name"]),
        _tool("refactor_extract_var","Extract inline expression into named variable.",
              {"path":{"type":"string"},"line":{"type":"integer"},"expression":{"type":"string"},"var_name":{"type":"string"}}, ["path","line","expression","var_name"]),
        _tool("refactor_inline_var", "Inline a single-assignment variable at use sites.",
              {"path":{"type":"string"},"var_name":{"type":"string"}}, ["path","var_name"]),
        _tool("generate_tests",  "Generate comprehensive unit tests for all functions in a file.",
              {"path":{"type":"string"},"framework":{"type":"string","enum":["pytest","jest"]},"output_dir":{"type":"string"}}, ["path"]),
        _tool("fill_coverage_gaps","Generate tests for functions that have no existing tests.",
              {"path":{"type":"string"},"test_dir":{"type":"string"},"framework":{"type":"string"}}, ["path"]),
        _tool("run_tests",       "Run test suite and return pass/fail results.",
              {"path":{"type":"string"},"framework":{"type":"string","enum":["pytest","jest"]}}, []),
        # ── v6.0 AGENTS ──────────────────────────────────────────────────
        _tool("agent_run",       "Run a specialized agent (coder/reviewer/tester/security/optimizer/debugger).",
              {"task":{"type":"string"},"role":{"type":"string","enum":["coder","reviewer","tester","documenter","security","planner","optimizer","debugger"]},"context":{"type":"string"}}, ["task"]),
        _tool("agent_pipeline",  "Sequential pipeline: each agent refines previous output.",
              {"task":{"type":"string"},"roles":{"type":"array","items":{"type":"string"}},"context":{"type":"string"}}, ["task"]),
        _tool("agent_multi_review","Simultaneous REVIEWER + SECURITY + OPTIMIZER review of code.",
              {"code":{"type":"string"},"path":{"type":"string"}}, []),
        _tool("critic_review",   "CriticAgent: review and auto-revise code until quality bar met.",
              {"code":{"type":"string"},"path":{"type":"string"},"context":{"type":"string"},"language":{"type":"string"},"max_iterations":{"type":"integer"}}, []),
        _tool("critic_gate",     "Quality gate: approve/reject code before delivering to user.",
              {"code":{"type":"string"},"context":{"type":"string"},"language":{"type":"string"}}, ["code"]),
        # ── v6.0 MEMORY AGENT ────────────────────────────────────────────
        _tool("mem_agent_remember","Save fact/decision/bug/debt/preference to long-term memory.",
              {"content":{"type":"string"},"type":{"type":"string","enum":["decision","preference","bug","debt","fact","snippet","lesson"]},"importance":{"type":"number"}}, ["content"]),
        _tool("mem_agent_recall", "Semantic recall from long-term memory for current task context.",
              {"query":{"type":"string"},"top_k":{"type":"integer"}}, ["query"]),
        _tool("mem_agent_stats",  "Long-term memory agent statistics.", {}, []),
        # ── v6.0 REASONING ───────────────────────────────────────────────
        _tool("reason",          "Chain-of-thought + self-reflection reasoning for complex problems.",
              {"problem":{"type":"string"},"context":{"type":"string"},"use_tot":{"type":"boolean"},"reflect":{"type":"boolean"},"cot_steps":{"type":"integer"}}, ["problem"]),
        _tool("plan_task",       "Decompose goal into dependency-aware sub-tasks with ETA.",
              {"goal":{"type":"string"},"context":{"type":"string"}}, ["goal"]),
    ]
    if extra_mcp:
        tools.extend(extra_mcp)
    return tools

def _tool(name: str, desc: str, props: dict, required: list) -> dict:
    return {"type":"function","function":{"name":name,"description":desc,
            "parameters":{"type":"object","properties":props,"required":required}}}


# ── SKILLS ────────────────────────────────────────────────────────────────────
class SkillsSystem:
    def __init__(self, ex: ToolExecutor, mem: MemorySystem, mcp: MCPClient,
                 bg: BackgroundManager, config: dict, console):
        self.ex      = ex
        self.mem     = mem
        self.mcp     = mcp
        self.bg      = bg
        self.config  = config
        self.console = console

    def handle(self, cmd: str) -> Optional[str]:
        parts = cmd.strip().lstrip("/").split(maxsplit=1)
        skill = parts[0].lower()
        arg   = parts[1] if len(parts) > 1 else ""
        fn = getattr(self, f"_s_{skill}", None)
        return fn(arg) if fn else None

    def _s_help(self, _) -> str:
        return """## Qwen Ultimate v4.1 — Skills

| Skill | Descrição |
|-------|-----------|
| `/open <file>` | Lê e mostra conteúdo de um arquivo |
| `/fix <desc>` | Analisa e corrige código automaticamente |
| `/where <name>` | Encontra onde função/classe está definida |
| `/recent` | Lista arquivos modificados nas últimas 24h |
| `/copyall <file>` | Copia conteúdo formatado para clipboard |
| `/commit [msg]` | Smart commit com Conventional Commits |
| `/review` | Code review detalhado das mudanças |
| `/explain <file>` | Análise profunda de um arquivo |
| `/test <file>` | Gerar testes completos |
| `/debug <erro>` | Diagnóstico e fix de erros |
| `/plan <task>` | Plano de execução antes de agir |
| `/agent <task>` | Rodar sub-agente isolado numa tarefa |
| `/pr [título]` | Criar Pull Request no GitHub |
| `/issue <ação>` | Gerenciar issues |
| `/lint [dir]` | Rodar linter |
| `/format [dir]` | Formatar código |
| `/deps` | Analisar dependências |
| `/todos` | Listar todos os TODOs do projeto |
| `/tree [dir]` | Estrutura visual do projeto |
| `/docker <cmd>` | Operações Docker |
| `/export` | Exportar conversa p/ Markdown |
| `/undo` | Desfazer última mudança de arquivo |
| `/bg <cmd>` | Rodar comando em background |
| `/models` | Listar/trocar modelo |
| `/tools` | Listar todas as ferramentas |
| `/memory [q]` | Ver/buscar memória |
| `/mcp` | Status MCP servers |
| `/config` | Ver configurações |
| `/session` | Gerenciar sessões |
| `/clear` | Limpar histórico |
"""

    def _s_open(self, path: str) -> str:
        """Skill: /open <arquivo> — Lê e mostra o conteúdo de um arquivo"""
        if not path:
            return "Uso: `/open <caminho/do/arquivo>`\nEx: `/open main.py` ou `/open src/utils/helper.py`"
        return self.ex._read_file({"path": path})

    def _s_fix(self, description: str) -> str:
        """Skill: /fix <descrição> — Analisa e corrige código automaticamente"""
        if not description:
            return "Uso: `/fix <descrição do problema>`\nEx: `/fix erro de import no main.py`"
        return f"""ACTION PLAN para corrigir: "{description}"

1. BUSQUE o arquivo relevante: use `search_in_files` ou peça ao usuário o path
2. LEIA o arquivo: `read_file(path="...")`
3. ANALISE o erro descrito: {description}
4. APLIQUE a correção: `edit_file` ou `write_file`
5. TESTE se possível: `run_command(command="python arquivo.py")`

Execute esses passos AGORA usando as ferramentas disponíveis."""

    def _s_where(self, pattern: str) -> str:
        """Skill: /where <padrão> — Encontra onde algo está definido"""
        if not pattern:
            return "Uso: `/where <nome da função/classe/variável>`"
        return self.ex._search_in_files({
            "pattern": f"(def|class|function|const|let|var)\\s+{re.escape(pattern)}",
            "file_pattern": "*.{py,js,ts,jsx,tsx}",
            "ignore_case": False
        })

    def _s_tree(self, path: str) -> str:
        """Skill: /tree [pasta] — Mostra estrutura visual do projeto"""
        return self.ex._file_tree({"path": path or ".", "max_depth": 3, "hidden": False})

    def _s_recent(self, _: str) -> str:
        """Skill: /recent — Lista arquivos modificados recentemente"""
        recent = []
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", ".venv"}]
            for f in files:
                fp = os.path.join(root, f)
                try:
                    mtime = os.path.getmtime(fp)
                    if time.time() - mtime < 86400:
                        recent.append((fp, mtime))
                except:
                    pass
        recent.sort(key=lambda x: x[1], reverse=True)
        if not recent:
            return "Nenhum arquivo modificado nas últimas 24h."
        return "\n".join(f"- {fp} ({datetime.datetime.fromtimestamp(m):%H:%M})" 
                         for fp, m in recent[:20])

    def _s_copyall(self, path: str) -> str:
        """Skill: /copyall <arquivo> — Copia conteúdo formatado para área de transferência"""
        if not path or not os.path.exists(path):
            return f"Arquivo não encontrado: {path}"
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            if PYPERCLIP_AVAILABLE:
                pyperclip.copy(f"```python\n{content}\n```")
                return f"✅ `{path}` copiado para clipboard com formatação Markdown!"
            else:
                return f"📋 Conteúdo de `{path}`:\n\n```python\n{content}\n```"
        except Exception as e:
            return f"Erro ao ler: {e}"

    def _s_commit(self, msg: str) -> str:
        st  = self.ex._git_operation({"operation":"status"})
        dff = self.ex._git_operation({"operation":"diff"})
        return (f"Git status:\n{st}\n\nDiff:\n{dff[:4000]}\n\n"
                + (f"Faça `git add .` e `git commit -m '{msg}'`." if msg
                   else "Gere mensagem Conventional Commits, faça `git add .` e commite."))

    def _s_review(self, _) -> str:
        dff = self.ex._git_operation({"operation":"diff"})
        log = self.ex._git_operation({"operation":"log"})
        return f"Code review COMPLETO (bugs, segurança, performance, edge cases):\n\n{log}\n\n{dff[:6000]}"

    def _s_explain(self, path: str) -> str:
        if not path: return "Uso: /explain <arquivo>"
        c = self.ex._read_file({"path":path})
        return f"Explique em profundidade: propósito, arquitetura, decisões de design, pontos de melhoria:\n```\n{c[:6000]}\n```"

    def _s_test(self, path: str) -> str:
        if not path: return "Uso: /test <arquivo>"
        c = self.ex._read_file({"path":path})
        return f"Gere testes COMPLETOS (normais, edge cases, erros). Framework adequado. Escreva o arquivo:\n```\n{c[:5000]}\n```"

    def _s_debug(self, error: str) -> str:
        return f"Diagnose, encontre causa raiz, aplique o fix:\n{error}" if error else "Descreva o erro."

    def _s_plan(self, task: str) -> str:
        if not task: return "Uso: /plan <tarefa>"
        tree = self.ex._file_tree({"path":".","max_depth":2})
        return (f"MODO PLANO para: '{task}'\n\nEstrutura:\n{tree}\n\n"
                "Liste etapas numeradas com ferramentas que usará. NÃO execute ainda — apresente o plano.")

    def _s_agent(self, task: str) -> str:
        if not task: return "Uso: /agent <tarefa>"
        return f"Você é um sub-agente. Execute esta tarefa de forma autônoma e reporte o resultado:\n{task}"

    def _s_pr(self, title: str) -> str:
        log = self.ex._git_operation({"operation":"log"})
        dff = self.ex._git_operation({"operation":"diff"})
        return (f"Crie PR no GitHub. Log:\n{log}\n\nDiff:\n{dff[:3000]}\n\n"
                f"{'Título: '+title if title else 'Gere título.'} Use `github_cli` com `pr create` e body em Markdown.")

    def _s_issue(self, action: str) -> str:
        return f"Gerencie GitHub issues. Ação: {action or 'list'}. Use `github_cli`."

    def _s_lint(self, path: str) -> str:
        p = path or "."
        return f"Rode linters em '{p}': ruff/flake8 (Python), eslint (JS/TS). Instale se necessário e mostre problemas."

    def _s_format(self, path: str) -> str:
        p = path or "."
        return f"Formate código em '{p}': black/ruff (Python), prettier (JS/TS). Use `run_command`."

    def _s_deps(self, _) -> str:
        return "Analise dependências: desatualizadas, vulnerabilidades, não usadas. Use pip list/npm outdated."

    def _s_todos(self, path: str) -> str:
        return f"Use find_todos para listar todos os TODOs/FIXMEs em '{path or '.'}'."

    def _s_docker(self, cmd: str) -> str:
        return f"Execute docker/docker-compose: '{cmd or 'ps'}'. Use `run_command`."

    def _s_export(self, _) -> str:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"Exporte a conversa para `qwen_export_{ts}.md` com `write_file`. Formate bem em Markdown."

    def _s_undo(self, _) -> str:
        return self.ex.undo.undo()

    def _s_rag(self, arg: str) -> str:
        if arg.startswith("index"):
            path = arg.replace("index","").strip() or "."
            return f"Use rag_index com path='{path}' para indexar o projeto semanticamente."
        if arg:
            return f"Use rag_search com query='{arg}' para busca semântica no codebase."
        return ("**RAG — Busca Semântica no Codebase**\n"
                "- `/rag index [dir]` — indexar projeto\n"
                "- `/rag <query>` — buscar semanticamente\n"
                "Use rag_stats para ver status do índice.")

    def _s_browser(self, url: str) -> str:
        if url:
            return f"Abra o browser com browser_open(url='{url}') e explore a página."
        return ("**Browser Automation**\n"
                "- `/browser <url>` — abrir URL\n"
                "- Depois use browser_click, browser_type, browser_screenshot, etc.")

    def _s_tdd(self, task: str) -> str:
        if not task:
            return "Uso: /tdd <descrição da funcionalidade a implementar via TDD>"
        return f"Execute TDD autônomo com tdd_run: task='{task}'. Escreva testes, implemente, rode, corrija até tudo passar."

    def _s_think(self, task: str) -> str:
        prompt = task or "analise o código atual e sugira melhorias"
        return f"/think\n{prompt}"

    def _s_docs(self, lib: str) -> str:
        if not lib:
            return "Uso: /docs <biblioteca> [query]\nEx: /docs fastapi routing"
        parts = lib.split(maxsplit=1)
        library = parts[0]
        query   = parts[1] if len(parts) > 1 else ""
        return (f"1. Use context7_search com library='{library}' query='{query}' para encontrar o ID.\n"
                f"2. Use context7_get_docs com o library_id retornado para obter documentação completa.")

    def _s_local(self, prompt: str) -> str:
        if not prompt:
            return "Uso: /local <pergunta> — resposta rápida via Ollama local"
        return f"Use ollama_chat com prompt='{prompt}' para resposta offline e instantânea."

    def _s_routing(self, _) -> str:
        lines = ["**Model Routing:**\n"]
        for k, v in ROUTING_RULES.items():
            kws = ", ".join(v.get("keywords",["(default)"])[:4])
            lines.append(f"- `{k}`: {v['model'].split('/')[-1]} — triggers: {kws}")
        return "\n".join(lines)

    def _s_bg(self, cmd: str) -> str:
        if not cmd: return self.bg.list_all()
        return f"Rode em background com `background_run`: {cmd}"

    def _s_models(self, _) -> str:
        lines = ["**Modelos:**\n"]
        for a, m in AVAILABLE_MODELS.items():
            lines.append(f"- `{a}`: {m}")
        lines.append("\n**Trocar:** 'use o modelo qwen-32b'")
        return "\n".join(lines)

    def _s_tools(self, _) -> str:
        all_t = build_tools()
        lines = [f"**{len(all_t)} native + {len(self.mcp.extra_tools)} MCP tools:**\n"]
        for t in all_t:
            fn = t["function"]
            lines.append(f"- `{fn['name']}`: {fn['description'][:70]}")
        return "\n".join(lines)

    def _s_memory(self, q: str) -> str:
        return self.mem.recall(q) if q else self.mem.list_all()

    def _s_mcp(self, _) -> str:
        return f"**MCP:**\n{self.mcp.status()}\n\nEdite qwen_mcp.json."

    def _s_config(self, _) -> str:
        return f"```json\n{json.dumps(self.config, indent=2)}\n```\nEdite qwen_config.json."

    def _s_session(self, arg: str) -> str:
        return f"Gerenciar sessão: {arg or 'list'}. Use /session save <nome> ou /session load <nome>."


# ── SESSION MANAGER ───────────────────────────────────────────────────────────
class SessionManager:
    def __init__(self):
        SESSIONS_DIR.mkdir(exist_ok=True)

    def save(self, name: str, history: list) -> str:
        (SESSIONS_DIR / f"{name}.json").write_text(
            json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        return f"✅ Session saved: {name}"

    def load(self, name: str) -> Optional[list]:
        p = SESSIONS_DIR / f"{name}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def list_all(self) -> str:
        files = sorted(SESSIONS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        return "\n".join(f"- {f.stem}" for f in files) if files else "No sessions."


# ── MAIN ──────────────────────────────────────────────────────────────────────
class QwenUltimate:
    def __init__(self):
        self.config      = self._load_config()
        self.console     = Console() if RICH_AVAILABLE else None

        # ── SMART MULTI-PROVIDER ROUTER (MODO DEUS) ──────────────────────
        self.client, self.model = self._init_provider()
        self.provider = self.config.get("provider", "huggingface")
        self.memory      = MemorySystem()
        self.mcp         = MCPClient()
        self.approval    = ApprovalSystem(self.config, self.console)
        self.diff_eng    = DiffEngine(self.config, self.console)
        self.undo        = UndoSystem()
        self.bg          = BackgroundManager()
        self.ctx_mgr     = ContextManager(self.config, self.client, self.model)
        self.token_ctr   = TokenCounter()
        self.auto_ctx    = AutoContext()

        # ── RAG ───────────────────────────────────────────────────────────
        self.rag = RAGSystem() if RAG_AVAILABLE else None
        if self.rag and self.console:
            self.console.print("[dim]🧠 RAG ready (/rag index to index codebase)[/dim]")

        # ── BROWSER ───────────────────────────────────────────────────────
        headless = self.config.get("browser_headless", False)
        self.browser = BrowserAutomation(headless=headless) if BROWSER_AVAILABLE else None
        if self.browser and self.console:
            self.console.print("[dim]🌐 Browser ready (/browser <url>)[/dim]")

        # ── OLLAMA ────────────────────────────────────────────────────────
        self.ollama = OllamaClient(self.config)
        if self.ollama.is_available():
            models = self.ollama.list_models()
            if self.console:
                self.console.print(f"[dim]🏠 Ollama ready: {', '.join(models[:3])}[/dim]")
        else:
            self.ollama = None

        # ── v6.0 INTELLIGENCE MODULES ─────────────────────────────────────────
        self.code_analyzer    = CodeAnalyzer()                               if ANALYZER_AVAILABLE   else None
        self.security_scanner = SecurityScanner()                            if SECURITY_AVAILABLE   else None
        self.refactor_engine  = RefactorEngine(".")                          if REFACTOR_AVAILABLE   else None
        self.reasoning_engine = ReasoningEngine(self.client, self.model)     if REASONING_AVAILABLE  else None
        self.agent_planner    = AgentPlanner(self.client, self.model)        if PLANNER_AVAILABLE    else None
        self.test_generator   = TestGenerator(self.client, self.model)       if TESTGEN_AVAILABLE    else None
        self.critic_agent     = CriticAgent(self.client, self.model)         if CRITIC_AVAILABLE     else None
        self.memory_agent     = MemoryAgent(self.client, self.model)         if MEMORY_AGENT_AVAILABLE else None

        n6_active = sum(1 for x in [
            self.code_analyzer, self.security_scanner, self.refactor_engine,
            self.reasoning_engine, self.agent_planner, self.test_generator,
            self.critic_agent, self.memory_agent,
        ] if x is not None)
        if self.console:
            self.console.print(f"[dim green]🧠 v6.0 modules active: {n6_active}/8[/dim green]")

        # ── v7.0 RELIABILITY MODULES ──────────────────────────────────────────
        self.prompt_engine  = PromptEngine(self.client, self.model)    if PROMPT_ENGINE_AVAILABLE  else None
        self.ctx_mgr_pro    = ContextManagerPro(self.client, self.model, self.config) if CTX_PRO_AVAILABLE else None
        self.vscode_bridge  = create_vscode_bridge() if VSCODE_BRIDGE_AVAILABLE else None

        n7_active = sum(1 for x in [self.prompt_engine, self.ctx_mgr_pro, self.vscode_bridge] if x is not None)
        if self.console and n7_active:
            self.console.print(f"[dim cyan]⚡ v7.0 modules active: {n7_active}/3 (ToolValidator inline)[/dim cyan]")

        # ── v8.0 INFRASTRUCTURE MODULES ───────────────────────────────────────
        self.hooks          = HooksEngine(self.config, self.client, self.model) if HOOKS_AVAILABLE else None
        self.plan_mode      = PlanMode(self.client, self.model) if PLAN_MODE_AVAILABLE else None
        self.checkpoints    = CheckpointSystem() if CHECKPOINT_AVAILABLE else None
        self.structured_out = StructuredOutput(self.client, self.model) if STRUCTURED_OUTPUT_AVAILABLE else None
        self.cron           = CronScheduler() if CRON_AVAILABLE else None
        self.worktree_mgr   = WorktreeManager() if WORKTREE_AVAILABLE else None
        self.github         = GitHubIntegration(self.config, self.client, self.model) if GITHUB_AVAILABLE else None

        if self.hooks:
            self.hooks.setup_builtin_hooks()
        if self.cron:
            self.cron.start()

        n8_active = sum(1 for x in [
            self.hooks, self.plan_mode, self.checkpoints, self.structured_out,
            self.cron, self.worktree_mgr, self.github
        ] if x is not None)
        if self.console and n8_active:
            self.console.print(f"[dim magenta]🚀 v8.0 modules active: {n8_active}/7[/dim magenta]")

        self.executor    = ToolExecutor(self.memory, self.mcp, self.approval,
                                        self.diff_eng, self.undo, self.bg, self.config,
                                        rag=self.rag, browser=self.browser, ollama=self.ollama,
                                        code_analyzer=self.code_analyzer,
                                        security_scanner=self.security_scanner,
                                        refactor_engine=self.refactor_engine,
                                        test_generator=self.test_generator,
                                        critic_agent=self.critic_agent,
                                        memory_agent=self.memory_agent,
                                        reasoning_engine=self.reasoning_engine,
                                        agent_planner=self.agent_planner)
        self.sessions    = SessionManager()
        self.tokens_used = 0

        mcp_started = self.mcp.start_all()
        self.god_mode          = UnrestrictedExecutor(self.config)
        self.executor.god_mode = self.god_mode
        safe = self.config.get("safe_mode", True)
        self.all_tools = build_tools(self.mcp.extra_tools) + (build_godmode_tools() if not safe else [])
        self.multi_agent = MultiAgent(self.client, self.model, self.all_tools, self.executor)

        # AgentPool needs all_tools to be built first
        self.agent_pool = AgentPool(self.client, self.model, self.all_tools, self.executor) if POOL_AVAILABLE else None
        if self.executor:
            self.executor.agent_pool = self.agent_pool

        # ── TDD LOOP (needs client + executor) ────────────────────────────
        self.tdd_loop = TDDLoop(self.executor, self.client, self.model, self.all_tools)
        self.executor.tdd = self.tdd_loop

        # ── v8.0: Wire infrastructure into executor ────────────────────────
        self.executor._hooks_engine = self.hooks
        self.executor._plan_mode    = self.plan_mode
        self.executor._checkpoint   = self.checkpoints
        # permissions + task_agent wired after they are initialized below

        # Start Web UI in background if FastAPI available
        if WEBUI_AVAILABLE and self.config.get("web_ui", False):
            run_with_qwen(self, port=self.config.get("web_ui_port", 8000))

        # ── v9.0 CLAUDE CODE DNA MODULES ──────────────────────────────────
        self.dream       = DreamSystem(self.client, self.model, self.memory) if DREAM_AVAILABLE else None
        self.spec_exec   = SpeculativeExecutor(self.executor) if SPECULATIVE_AVAILABLE else None
        self.batch_tool  = BatchTool(self.executor) if SPECULATIVE_AVAILABLE else None
        self.kairos      = Kairos(self.client, self.model) if KAIROS_AVAILABLE else None
        self.ctx_collapse= ContextCollapse(self.client, self.model,
                            self.config.get("max_context_tokens", 200_000)) if COLLAPSE_AVAILABLE else None
        self.sess_state  = SessionStateManager.get() if SESSION_STATE_AVAILABLE else None
        self.buddy       = Buddy() if BUDDY_AVAILABLE else None

        # ── PRODUCTION HARDENING ──────────────────────────────────────────
        if HARDENING_AVAILABLE:
            self._hardened = HardenedAPIClient(
                self.client,
                name             = "openrouter",
                calls_per_minute = self.config.get("rate_limit_rpm", 60),
                failure_threshold= 5,
            )
        else:
            self._hardened = None

        # ── PERMISSIONS ───────────────────────────────────────────────────
        if PERMISSIONS_AVAILABLE:
            mode     = self.config.get("permission_mode", "default")
            allowed  = self.config.get("allowed_tools",   [])
            denied   = self.config.get("denied_tools",    [])
            self.permissions = PermissionManager(
                mode          = PermissionMode(mode) if mode in [m.value for m in PermissionMode] else PermissionMode.DEFAULT,
                allowed_tools = allowed,
                denied_tools  = denied,
                prompt_fn     = None,  # uses terminal prompt
            )
        else:
            self.permissions = None

        # ── TASK AGENT (sub-agents) ────────────────────────────────────────
        if TASK_AGENT_AVAILABLE:
            self.task_agent = TaskAgent(
                client      = self.client,
                model       = self.model,
                all_tools   = self.all_tools,
                executor    = self.executor,
                permissions = self.permissions,
                max_tokens  = self.config.get("max_tokens", 4096),
            )
            # Register spawn_task as a callable tool
            self.all_tools.append(self.task_agent.as_tool_definition())
        else:
            self.task_agent = None

        # Wire permissions + task_agent into executor now that they exist
        self.executor._permissions = self.permissions
        self.executor._task_agent  = self.task_agent

        # BUDDY session start
        if self.buddy:
            greeting = self.buddy.on_session_start()
            if self.console:
                from rich.panel import Panel
                self.console.print(Panel(greeting, border_style="magenta", title="[bold magenta]BUDDY[/]"))
            else:
                print(f"\n{C.MG}{greeting}{C.EN}")

        # Init session state
        if self.sess_state:
            self.sess_state.model    = self.model
            self.sess_state.provider = self.config.get("provider", "openrouter")
            self.sess_state.safe_mode= self.config.get("safe_mode", True)

        n9_active = sum(1 for x in [
            self.dream, self.spec_exec, self.kairos, self.ctx_collapse,
            self.sess_state, self.buddy, self.permissions, self.task_agent,
            self._hardened,
        ] if x is not None)
        if self.console and n9_active:
            self.console.print(f"[dim yellow]🧬 v9.0 DNA modules active: {n9_active}/9[/dim yellow]")

        ctx_info   = self.auto_ctx.detect(".")
        ctx_block  = self.auto_ctx.build_context_block(ctx_info) if self.config.get("auto_context") else ""

        self.history = self._load_history()
        if not self.history or self.history[0]["role"] != "system":
            self.history = [{"role":"system","content": build_system_prompt(self.config, ctx_block)}]
        elif ctx_block and self.config.get("auto_context"):
            self.history[0]["content"] = build_system_prompt(self.config, ctx_block)
        self._save_history()

        # Inject cache boundary into system prompt (after history is ready)
        if self.ctx_collapse:
            self.history = ContextCollapse.inject_cache_boundary(self.history)

        self.skills = SkillsSystem(self.executor, self.memory, self.mcp, self.bg,
                                   self.config, self.console)

        hook = self.config.get("hooks", {}).get("on_start", "")
        if hook:
            subprocess.run(hook, shell=True, capture_output=True)

        if mcp_started and self.console:
            self.console.print(f"[green]✅ MCP: {', '.join(mcp_started)}[/green]")

        self._print_header(ctx_info)

    def _init_provider(self):
        """Smart multi-provider init with automatic fallback chain."""
        from openai import OpenAI

        provider  = self.config.get("provider", "huggingface")
        token     = self.config.get("hf_token", "")
        cfg_model = self.config.get("model", "Qwen/Qwen3-Coder-480B-A35B-Instruct")

        # ── Provider map ─────────────────────────────────────────────────
        PROVIDERS = {
            "cerebras": {
                "base_url": "https://api.cerebras.ai/v1",
                "model":    "qwen-3-235b-a22b-instruct-2507",
                "label":    "Cerebras FREE | Qwen3-235B (1M tokens/dia)",
                "key_field": "cerebras_token",
            },
            "puter": {
                "base_url": "https://api.puter.com/puterai/openai/v1",
                "model":    "qwen3-coder-480b-a35b-instruct",
                "label":    "Puter.com FREE | Qwen3-Coder-480B",
                "key_field": "puter_token",
            },
            "openrouter_qwen3": {
                "base_url": "https://openrouter.ai/api/v1",
                "model":    "qwen/qwen3-coder:free",
                "label":    "OpenRouter FREE | Qwen3-Coder-480B",
                "key_field": "openrouter_token",
            },
            "together": {
                "base_url": "https://api.together.xyz/v1",
                "model":    "Qwen/Qwen3-480B-A22B-Instruct-Turbo",
                "label":    "Together AI | Qwen3-480B GOD MODE 🔥",
                "key_field": "together_token",
            },
            "github": {
                "base_url": "https://models.inference.ai.azure.com",
                "model":    cfg_model,
                "label":    f"GitHub Models | {cfg_model.split('/')[-1]}",
                "key_field": "hf_token",
            },
            "groq": {
                "base_url": "https://api.groq.com/openai/v1",
                "model":    "deepseek-r1-distill-llama-70b",
                "label":    "Groq FREE | DeepSeek-R1-Distill-70B",
                "key_field": "groq_token",
            },
            "openrouter": {
                "base_url": "https://openrouter.ai/api/v1",
                "model":    "deepseek/deepseek-r1:free",
                "label":    "OpenRouter FREE | DeepSeek-R1",
                "key_field": "openrouter_token",
            },
            "huggingface": {
                "base_url": None,
                "model":    cfg_model,
                "label":    "HuggingFace Inference",
                "key_field": "hf_token",
            },
        }

        cfg   = PROVIDERS.get(provider, PROVIDERS["huggingface"])
        token = self.config.get(cfg.get("key_field", "hf_token"), token)

        # HuggingFace uses its own client
        if provider == "huggingface" or cfg["base_url"] is None:
            try:
                from huggingface_hub import InferenceClient
                client = InferenceClient(token=token)
                model  = cfg["model"]
                print(f"{C.GR}✅ HuggingFace ativado | {model.split('/')[-1]}{C.EN}")
                return client, model
            except Exception as e:
                print(f"{C.YL}⚠ HuggingFace failed: {e} — trying Puter fallback{C.EN}")
                provider = "puter"
                cfg      = PROVIDERS["puter"]
                token    = self.config.get("puter_token", "")

        # OpenAI-compatible providers
        try:
            client = OpenAI(base_url=cfg["base_url"], api_key=token or "no-key")
            model  = cfg["model"]
            print(f"{C.GR}[OK] {cfg['label']}{C.EN}")
            return client, model
        except Exception as e:
            print(f"{C.YL}[!] {provider} failed: {e}{C.EN}")

        # Fallback chain: Puter → OpenRouter Qwen3 free → OpenRouter DeepSeek free → HuggingFace
        fallback_chain = [
            ("cerebras",         "https://api.cerebras.ai/v1",              "qwen-3-235b-a22b-instruct-2507",  self.config.get("cerebras_token",""),  "Cerebras FREE | Qwen3-235B"),
            ("puter",            "https://api.puter.com/puterai/openai/v1", "qwen3-coder-480b-a35b-instruct",  self.config.get("puter_token",""),     "Puter FREE | Qwen3-480B"),
            ("openrouter_qwen3", "https://openrouter.ai/api/v1",            "qwen/qwen3-coder:free",           self.config.get("openrouter_token",""),"OpenRouter FREE | Qwen3-480B"),
            ("openrouter_ds",    "https://openrouter.ai/api/v1",            "deepseek/deepseek-r1:free",       self.config.get("openrouter_token",""),"OpenRouter FREE | DeepSeek-R1"),
            ("github_llama405",  "https://models.inference.ai.azure.com",   "Meta-Llama-3.1-405B-Instruct",   self.config.get("hf_token",""),        "GitHub FREE | Llama-3.1-405B"),
            ("github_gpt4o",     "https://models.inference.ai.azure.com",   "gpt-4o",                         self.config.get("hf_token",""),        "GitHub FREE | GPT-4o"),
        ]
        for fb_name, fb_url, fb_model, fb_key, fb_label in fallback_chain:
            if fb_name == provider:
                continue  # already tried
            try:
                client = OpenAI(base_url=fb_url, api_key=fb_key or "no-key")
                print(f"{C.YL}⚠ Fallback: {fb_label}{C.EN}")
                return client, fb_model
            except Exception:
                continue

        # HuggingFace absolute last resort
        try:
            from huggingface_hub import InferenceClient
            fb_token = self.config.get("hf_token", "")
            client = InferenceClient(token=fb_token)
            model  = "Qwen/Qwen2.5-Coder-32B-Instruct"
            print(f"{C.YL}⚠ Fallback final: HuggingFace | {model}{C.EN}")
            return client, model
        except Exception as e:
            raise RuntimeError(f"All providers failed. Last error: {e}")

    def _load_config(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, encoding="utf-8") as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except Exception:
                pass
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG.copy()

    def _load_history(self) -> list:
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠ history: {e}")

    def _trim_history(self):
        sys_msg = self.history[0]
        rest    = self.history[1:]
        max_h   = self.config.get("max_history", 60)
        if len(rest) > max_h:
            rest = rest[-max_h:]
        self.history = [sys_msg] + rest

    def _print_header(self, ctx_info: dict = None):
        model_s = self.model.split("/")[-1]
        n_tools = len(self.all_tools)
        n_mem   = len(self.memory.data)
        safe    = "🔒" if self.config.get("safe_mode") else "🔓"
        stack   = ", ".join((ctx_info or {}).get("stack", [])) or "unknown"

        if self.console:
            t = Table.grid(padding=(0,2))
            t.add_row("[bold cyan]⚡ QWEN3-CODER ULTIMATE v6.0[/]",    f"[green]Model:[/] {model_s}")
            t.add_row(f"[yellow]Tools:[/] {n_tools} ({len(self.mcp.extra_tools)} MCP)", f"[magenta]Memory:[/] {n_mem}")
            t.add_row(f"[blue]Stack:[/] {stack}",                       f"[dim]Safe: {safe} | /help[/dim]")
            self.console.print(Panel(t, border_style="bright_cyan", title="[bold white]Claude Code Killer 🔥 v6.0[/]"))
        else:
            print(f"\n{C.CY}{C.BD}⚡ QWEN3-CODER ULTIMATE v9.0 🧬{C.EN}")
            print(f"  Model {model_s} | {n_tools} tools | Stack: {stack} | Safe {safe}")
            print(f"  {C.DM}/help para ver skills{C.EN}\n")

    def _status_bar(self):
        msgs  = len(self.history)
        toks  = self.tokens_used
        model = self.model.split("/")[-1][:20]
        bg    = len([p for p in self.bg._procs.values() if p.poll() is None])
        line  = f"[{model}] msgs:{msgs} ~{toks:,}tok"
        if bg:
            line += f" | bg:{bg}"
        # v7.0: show IDE bridge status
        if self.vscode_bridge and self.vscode_bridge.connected:
            line += " | 💻 IDE"
        if self.console:
            self.console.print(f"[dim]{line}[/dim]")
        else:
            print(f"{C.DM}{line}{C.EN}")

    def _v7_stats(self) -> str:
        lines = ["─── v7.0 Module Stats ───"]
        if self.prompt_engine:
            lines.append(f"  {self.prompt_engine.stats()}")
        if self.ctx_mgr_pro:
            lines.append(f"  {self.ctx_mgr_pro.stats()}")
        if self.vscode_bridge:
            lines.append(f"  {self.vscode_bridge.stats()}")
        tv = getattr(self, "_tool_validator", None)
        if tv:
            lines.append(f"  {tv.stats()}")
        return "\n".join(lines)

    def _v9_stats(self) -> str:
        lines = ["─── v9.0 DNA Module Stats ───"]
        if self.dream:
            lines.append(f"  {self.dream.stats()}")
        if self.spec_exec:
            lines.append(f"  {self.spec_exec.stats()}")
        if self.kairos:
            lines.append(f"  {self.kairos.stats()}")
        if self.ctx_collapse:
            lines.append(f"  {self.ctx_collapse.stats()}")
        if self.batch_tool:
            lines.append(f"  {self.batch_tool.stats()}")
        if self.buddy:
            lines.append(f"  {self.buddy.stats()}")
        if self.permissions:
            lines.append(f"  {self.permissions.stats()}")
        if self.task_agent:
            lines.append(f"  {self.task_agent.stats()}")
        if self._hardened:
            lines.append(f"  {self._hardened.stats()}")
        return "\n".join(lines)

    def _v8_stats(self) -> str:
        lines = ["─── v8.0 Module Stats ───"]
        if self.hooks:
            lines.append(f"  {self.hooks.stats()}")
        if self.plan_mode:
            lines.append(f"  {self.plan_mode.status()}")
        if self.checkpoints:
            lines.append(f"  {self.checkpoints.stats()}")
        if self.structured_out:
            lines.append(f"  {self.structured_out.stats()}")
        if self.cron:
            lines.append(f"  {self.cron.stats()}")
        if self.worktree_mgr:
            lines.append(f"  {self.worktree_mgr.status()}")
        if self.github:
            lines.append(f"  {self.github.stats()}")
        return "\n".join(lines)

    def _auto_detect_file_intent(self, user_input: str) -> Optional[str]:
        """Detecta se usuário quer acessar arquivos e retorna guidance para o modelo."""
        user_lower = user_input.lower()
        file_keywords = ["arquivo", "file", "código", "code", "vs code", "editor", "pasta", "folder", 
                        "src/", "main.py", ".py", ".js", "open", "read", "veja", "olhe", "mostre", "tree", "estrutura"]
        if any(kw in user_lower for kw in file_keywords) and "read_file" not in user_lower:
            return f"\n\n[SYSTEM HINT: User seems to want file access. Suggest using: `read_file`, `list_directory`, `search_in_files`, `file_tree`, or skills `/open`, `/tree`, `/where`. Current dir: {os.getcwd()}]"
        return None

    def _route_model(self, user_input: str) -> str:
        """Pick the best model for this message."""
        if not self.config.get("model_routing", True):
            return self.model
        low = user_input.lower()
        for rule_name, rule in ROUTING_RULES.items():
            if rule_name == "default":
                continue
            if any(k in low for k in rule.get("keywords", [])):
                model = rule["model"]
                if self.console:
                    self.console.print(f"[dim]⚡ Routing → {model.split('/')[-1]}[/dim]")
                else:
                    print(f"{C.DM}⚡ Routing → {model.split('/')[-1]}{C.EN}")
                return model
        return self.model

    def _apply_thinking(self, user_input: str, messages: list) -> list:
        """Prepend /think to trigger Qwen3 extended thinking mode."""
        if not self.config.get("thinking_mode", True):
            return messages
        low = user_input.lower()
        if any(t in low for t in THINKING_TRIGGERS):
            msgs = [m.copy() for m in messages]
            # Inject thinking directive before last user message
            for i in range(len(msgs) - 1, -1, -1):
                if msgs[i]["role"] == "user":
                    original = msgs[i]["content"]
                    if not original.startswith("/think"):
                        msgs[i] = {**msgs[i], "content": f"/think\n{original}"}
                    break
            return msgs
        return messages

    def _quick_answer(self, user_input: str) -> bool:
        """
        Intercept simple factual questions and answer instantly without LLM.
        Returns True if handled, False to continue to LLM.
        """
        u = user_input.lower().strip()
        now = datetime.datetime.now()

        TIME_KW  = ["que horas", "horas são", "hora é", "what time", "horas agora", "hora atual", "que hora"]
        DATE_KW  = ["que dia", "que data", "qual a data", "what date", "data de hoje", "today", "hoje é"]
        CWD_KW   = ["qual diretório", "qual pasta", "pasta atual", "current dir", "working dir", "onde estou"]

        if any(k in u for k in TIME_KW):
            resp = f"São {now.strftime('%H:%M:%S')} de {now.strftime('%d/%m/%Y')} ({now.strftime('%A')})."
            print(resp)
            self.history.append({"role": "user",      "content": user_input})
            self.history.append({"role": "assistant",  "content": resp})
            self._save_history()
            return True

        if any(k in u for k in DATE_KW):
            resp = f"Hoje é {now.strftime('%d/%m/%Y')} ({now.strftime('%A, %B %Y')})."
            print(resp)
            self.history.append({"role": "user",      "content": user_input})
            self.history.append({"role": "assistant",  "content": resp})
            self._save_history()
            return True

        if any(k in u for k in CWD_KW):
            resp = f"Diretório atual: `{os.getcwd()}`"
            print(resp)
            self.history.append({"role": "user",      "content": user_input})
            self.history.append({"role": "assistant",  "content": resp})
            self._save_history()
            return True

        return False

    def send_message(self, user_input: str):
        # ── Quick answers (sem LLM) ────────────────────────────────────────────
        if self._quick_answer(user_input):
            return

        # ── v8.0: Hooks — UserPromptSubmit ────────────────────────────────────
        if self.hooks:
            result = self.hooks.fire("UserPromptSubmit", {"content": user_input})
            if result.blocked:
                print(f"{C.YL}[Hook] Blocked: {result.message}{C.EN}")
                return
            if result.modified and isinstance(result.modified, dict):
                user_input = result.modified.get("content", user_input)

        # ── v8.0: Checkpoint — begin turn ─────────────────────────────────────
        if self.checkpoints:
            self.checkpoints.begin_turn(user_input[:60])

        # ── v7.0: PromptEngine — task-aware system prompt + few-shot hints ────
        effective_input = user_input
        if self.prompt_engine:
            task_type = self.prompt_engine.classify_task(user_input)
            sys_prompt = self.prompt_engine.build_system_prompt(task_type)
            if self.history and self.history[0]["role"] == "system":
                self.history[0]["content"] = sys_prompt
            effective_input = self.prompt_engine.inject_task_hints(user_input, task_type)

        self.history.append({"role":"user","content":effective_input})

        # ── v9.0: 4-tier Context Collapse (smart dispatch) ────────────────────
        if self.ctx_collapse:
            self.history = self.ctx_collapse.smart_compress(
                self.history, focus=user_input[:100]
            )
        elif self.ctx_mgr_pro and self.ctx_mgr_pro.should_compress(self.history):
            self.history = self.ctx_mgr_pro.smart_trim(self.history, current_task=user_input)
        elif self.ctx_mgr.should_compress(self.history):
            self.history = self.ctx_mgr.compress(self.history)
        self._trim_history()

        # ── v7.0: VSCodeBridge — inject active file context ───────────────────
        if self.vscode_bridge and self.vscode_bridge.connected:
            ide_ctx = self.vscode_bridge.build_context_message()
            if ide_ctx and self.history:
                last_user = next((i for i in range(len(self.history)-1, -1, -1) if self.history[i]["role"] == "user"), None)
                if last_user is not None:
                    self.history[last_user]["content"] += f"\n\n{ide_ctx}"

        # ── v7.0: ToolValidator — lazy init once tools are built ─────────────
        if not hasattr(self, "_tool_validator") and VALIDATOR_AVAILABLE and hasattr(self, "all_tools"):
            self._tool_validator = ToolValidator(self.client, self.model, self.all_tools)
        else:
            if not hasattr(self, "_tool_validator"):
                self._tool_validator = None

        # Model routing + thinking mode
        active_model   = self._route_model(user_input)
        active_history = self._apply_thinking(user_input, self.history)

        for _ in range(25):
            try:
                params = {
                    "model":       active_model,
                    "messages":    active_history,
                    "max_tokens":  self.config.get("max_tokens", 8192),
                    "temperature": self.config.get("temperature", 0.2),
                    "tools":       self.all_tools,
                    "tool_choice": "auto",
                    "stream":      False,
                }
                if self.console:
                    with self.console.status("[dim]Thinking...[/dim]", spinner="dots"):
                        resp = self.client.chat.completions.create(**params)
                else:
                    print(f"{C.DM}Thinking...{C.EN}", end="\r")
                    resp = self.client.chat.completions.create(**params)
                    print(" " * 20, end="\r")

                msg = resp.choices[0].message

            except Exception as e:
                err = str(e)
                if "429" in err or "queue_exceeded" in err or "high traffic" in err.lower():
                    # Try switching to next provider in fallback chain
                    switched = self._switch_provider_on_ratelimit()
                    if switched:
                        params["model"] = self.model
                        continue
                    wait = 15
                    print(f"{C.YL}Rate limit. Waiting {wait}s...{C.EN}")
                    time.sleep(wait)
                    continue
                if "503" in err or "502" in err:
                    print(f"{C.YL}Model loading. Wait 20s...{C.EN}")
                    time.sleep(20)
                    continue
                print(f"{C.RD}Error: {err}{C.EN}")
                logger.error(f"API Error: {err}")
                break

            if msg.tool_calls:
                if msg.content and msg.content.strip():
                    if self.console:
                        self.console.print(f"\n[dim italic]{msg.content.strip()}[/dim italic]")
                    else:
                        print(f"\n{C.DM}{msg.content.strip()}{C.EN}")

                tool_msg = {
                    "role": "assistant", "content": msg.content or "",
                    "tool_calls": [{"id":tc.id,"type":"function","function":{"name":tc.function.name,"arguments":tc.function.arguments}} for tc in msg.tool_calls]
                }
                self.history.append(tool_msg)
                active_history.append(tool_msg)

                tool_results: dict = {}
                calls     = msg.tool_calls
                validator = getattr(self, "_tool_validator", None)

                if self.console:
                    sep = "─" * 55
                    self.console.print(f"[dim]{sep}[/dim]")

                # ── v9.0: Speculative Executor — concurrent-safe tools start NOW ──
                if self.spec_exec and len(calls) >= 1:
                    # Submit all to speculative executor (it auto-classifies safe/serial)
                    for tc in calls:
                        if validator:
                            vr = validator.validate_and_fix(tc.function.name, tc.function.arguments)
                            args = vr.args if vr.valid else {}
                        else:
                            try:
                                args = json.loads(tc.function.arguments)
                            except Exception:
                                args = {}
                        self.spec_exec.submit(tc.id, tc.function.name, args)
                        args_p = json.dumps(args, ensure_ascii=False)[:100]
                        safe_icon = "⚡" if TOOL_CONCURRENCY.get(tc.function.name, False) else "🔧"
                        if self.console:
                            self.console.print(f"[bold cyan]  {safe_icon} {tc.function.name}[/][dim]({args_p})[/dim]")
                        else:
                            print(f"{C.CY}  {safe_icon} {tc.function.name}{C.EN}{C.DM}({args_p}){C.EN}")

                    # ── v9.0: Dream System runs WHILE tools execute ────────────
                    if self.dream:
                        self.dream.dream(self.history, current_task=user_input)

                    # Collect results (speculative ones may already be done)
                    tool_results = self.spec_exec.collect_all(timeout=30.0)

                elif self.config.get("parallel_tools", True) and len(calls) > 1:
                    if self.console:
                        self.console.print(f"[dim cyan]⚡ {len(calls)} tools in parallel...[/dim cyan]")
                    else:
                        print(f"{C.CY}⚡ {len(calls)} tools parallel...{C.EN}")

                    def _exec_tc(tc):
                        if validator:
                            vr = validator.validate_and_fix(tc.function.name, tc.function.arguments)
                            args = vr.args if vr.valid else {}
                        else:
                            try:
                                args = json.loads(tc.function.arguments)
                            except Exception:
                                args = {}
                        return tc.id, self.executor.execute(tc.function.name, args)

                    with ThreadPoolExecutor(max_workers=4) as pool:
                        for tc_id, result in pool.map(_exec_tc, calls):
                            tool_results[tc_id] = result
                else:
                    for tc in calls:
                        if validator:
                            vr = validator.validate_and_fix(tc.function.name, tc.function.arguments)
                            args = vr.args if vr.valid else {}
                            if vr.corrected and self.console:
                                self.console.print(f"[dim yellow]  ⚙ Args auto-corrected for {tc.function.name}[/dim yellow]")
                        else:
                            try:
                                args = json.loads(tc.function.arguments)
                            except Exception:
                                args = {}
                        args_p = json.dumps(args, ensure_ascii=False)[:120]
                        if self.console:
                            self.console.print(f"[bold cyan]  🔧 {tc.function.name}[/][dim]({args_p})[/dim]")
                        else:
                            print(f"{C.CY}  🔧 {tc.function.name}{C.EN}{C.DM}({args_p}){C.EN}")
                        result = self.executor.execute(tc.function.name, args)
                        tool_results[tc.id] = result

                for tc in calls:
                    result = tool_results.get(tc.id, "")
                    preview = result[:200].replace("\n", " ")
                    if self.console:
                        self.console.print(f"[dim green]  ↳ {preview}[/dim green]")
                    else:
                        print(f"{C.DM}{C.GR}  ↳ {preview}{C.EN}")
                    tool_result_msg = {"role":"tool","tool_call_id":tc.id,"content":result}
                    self.history.append(tool_result_msg)
                    active_history.append(tool_result_msg)

                    # ── BUDDY events ──────────────────────────────────────────
                    if self.buddy:
                        r_low = result.lower()
                        if result.startswith("Tool error") or result.startswith("Error"):
                            bm = self.buddy.on_error(tc.function.name)
                            if bm and self.console:
                                self.console.print(f"[dim magenta]{bm}[/dim magenta]")
                            elif bm:
                                print(f"{C.MG}{bm}{C.EN}")
                        elif any(kw in r_low for kw in ["fixed","corrigido","corrected","written","created","saved","updated"]):
                            bm = self.buddy.on_bug_fixed(tc.function.name)
                            if bm and self.console:
                                self.console.print(f"[dim magenta]{bm}[/dim magenta]")
                            elif bm:
                                print(f"{C.MG}{bm}{C.EN}")
                        elif len(result) > 500:
                            bm = self.buddy.on_good_code(tc.function.name)
                            if bm and self.console:
                                self.console.print(f"[dim magenta]{bm}[/dim magenta]")
                            elif bm:
                                print(f"{C.MG}{bm}{C.EN}")

                # Update params with fresh active_history
                params["messages"] = active_history
                continue

            final = msg.content or ""
            print()
            if self.console:
                self.console.print(Markdown(final))
            else:
                print(final)

            self.tokens_used += self.token_ctr.count(final) + self.token_ctr.count(json.dumps(self.history[-3:]))
            self.history.append({"role":"assistant","content":final})
            self._save_history()
            self._status_bar()
            logger.info(f"ASSISTANT: {final[:200]} | tokens: ~{self.tokens_used:,}")

            if self.config.get("auto_copy") and PYPERCLIP_AVAILABLE:
                try:
                    pyperclip.copy(final)
                except Exception:
                    pass

            # ── v7.0: PromptEngine — record successful interaction as few-shot ─
            if self.prompt_engine and len(final) > 50:
                task_type = self.prompt_engine.classify_task(user_input)
                self.prompt_engine.record_example(task_type, user_input, final)

            # ── v9.0: Dream System — inject consolidated memory if ready ──────
            if self.dream:
                result = self.dream.await_dream(timeout=1.0)
                if result and result.consolidated:
                    self.history = self.dream.inject_into_context(self.history)

            # ── v9.0: KAIROS — proactive assistance detection ─────────────────
            if self.kairos:
                signal = self.kairos.analyze(self.history, user_input, final)
                if signal:
                    kairos_msg = self.kairos.render(signal)
                    if self.console:
                        from rich.panel import Panel
                        self.console.print(Panel(kairos_msg, border_style="yellow", expand=False))
                    else:
                        print(f"{C.YL}{kairos_msg}{C.EN}")

            # ── v9.0: Session State — record turn metrics ─────────────────────
            if self.sess_state:
                tokens = self.token_ctr.count(final)
                self.sess_state.record_turn(tokens, 0)
                self.sess_state.tool_calls_total += len([m for m in self.history[-5:] if m.get("role") == "tool"])

            # ── v8.0: Checkpoint — commit turn ───────────────────────────────
            if self.checkpoints:
                self.checkpoints.commit_turn()

            # ── BUDDY: long session check ─────────────────────────────────────
            if self.buddy and self.buddy.state.sessions > 0 and self.sess_state:
                if self.sess_state.turn_count > 0 and self.sess_state.turn_count % 20 == 0:
                    bm = self.buddy.on_long_session()
                    if bm:
                        print(f"{C.MG}{bm}{C.EN}")

            break
        else:
            print(f"{C.YL}⚠ Max iterations reached.{C.EN}")

    def _switch_provider_on_ratelimit(self) -> bool:
        """On rate limit: retry Qwen3-480B first, then fallback."""
        from openai import OpenAI
        or_token = self.config.get("openrouter_token","")
        # Always retry Qwen3-480B on OpenRouter if we have the token
        if or_token and self.model != "qwen/qwen3-coder:free":
            try:
                self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_token)
                self.model  = "qwen/qwen3-coder:free"
                print(f"{C.YL}-> Qwen3-Coder-480B (OpenRouter){C.EN}")
                return True
            except Exception:
                pass
        # Emergency fallbacks (only if 480B is unavailable)
        chain = [
            ("https://api.cerebras.ai/v1",            "qwen-3-235b-a22b-instruct-2507", self.config.get("cerebras_token","")),
            ("https://models.inference.ai.azure.com", "Meta-Llama-3.1-405B-Instruct",   self.config.get("hf_token","")),
            ("https://models.inference.ai.azure.com", "gpt-4o",                         self.config.get("hf_token","")),
        ]
        for url, model, key in chain:
            if not key:
                continue
            if model == self.model:
                continue
            try:
                self.client = OpenAI(base_url=url, api_key=key)
                self.model  = model
                print(f"{C.YL}Emergency fallback -> {model.split('/')[-1]}{C.EN}")
                return True
            except Exception:
                continue
        return False

    def _handle_meta(self, text: str) -> bool:
        cmd = text.strip().lower()

        if cmd in ("exit","quit","sair"):
            hook = self.config.get("hooks",{}).get("on_exit","")
            if hook: subprocess.run(hook, shell=True)
            print("\n👋 Até mais!")
            self.mcp.stop_all()
            raise SystemExit(0)

        if cmd in ("clear","/clear"):
            self.history = [self.history[0]]
            self._save_history()
            print("🧹 Cleared.")
            return True

        for alias, mid in AVAILABLE_MODELS.items():
            if alias in text.lower() and any(k in text.lower() for k in ("use","muda","troca","switch","modelo")):
                self.model = mid
                self.ctx_mgr.model = mid
                self.multi_agent.model = mid
                if self.console:
                    self.console.print(f"[green]✅ Modelo: {mid}[/green]")
                else:
                    print(f"✅ {mid}")
                return True

        if text.lower().startswith("/session"):
            parts = text.split(maxsplit=2)
            sub   = parts[1] if len(parts) > 1 else "list"
            arg   = parts[2] if len(parts) > 2 else ""
            if sub == "save" and arg:
                print(self.sessions.save(arg, self.history))
            elif sub == "load" and arg:
                h = self.sessions.load(arg)
                if h:
                    self.history = h
                    print(f"✅ Loaded: {arg}")
                else:
                    print(f"❌ Not found: {arg}")
            else:
                print(self.sessions.list_all())
            return True

        if text.lower() in ("undo","/undo"):
            print(self.undo.undo())
            return True

        if text.lower() in ("/v7stats", "/v7", "/stats7", "/v8stats", "/v8",
                            "/v9stats", "/v9", "/stats", "/allstats"):
            print(self._v7_stats())
            print(self._v8_stats())
            print(self._v9_stats())
            if self.sess_state:
                print(f"\n{self.sess_state.summary()}")
            return True

        # ── v9.0 CONTEXT COLLAPSE ─────────────────────────────────────────────
        if text.lower() in ("/collapse", "/compress"):
            if self.ctx_collapse:
                self.history = self.ctx_collapse.collapse(self.history)
                print(self.ctx_collapse.list_commits())
            else:
                print("ContextCollapse not available.")
            return True

        if text.lower() in ("/collapses", "/commits"):
            print(self.ctx_collapse.list_commits() if self.ctx_collapse else "Not available.")
            return True

        if text.lower().startswith("/revert"):
            parts = text.split()
            cid   = parts[1] if len(parts) > 1 else None
            if self.ctx_collapse:
                restored = self.ctx_collapse.revert(cid)
                if restored:
                    self.history = restored
                    self._save_history()
                    print(f"Reverted. History restored to {len(restored)} messages.")
                else:
                    print("No collapse commit to revert.")
            else:
                print("ContextCollapse not available.")
            return True

        # ── v9.0 SESSION ──────────────────────────────────────────────────────
        if text.lower() in ("/session-info", "/session-state"):
            if self.sess_state:
                print(self.sess_state.summary())
                s = self.sess_state
                print(f"  Git: {s.git_branch or 'none'} {'(dirty)' if s.git_dirty else ''}")
                print(f"  Dream cycles: {s.dream_cycles} | KAIROS: {s.kairos_signals}")
                print(f"  Speculative ms saved: {s.speculative_ms_saved:,}")
                print(f"  Tool calls: {s.tool_calls_total} | Errors: {s.tool_errors}")
            else:
                print("SessionState not available.")
            return True

        # ── v9.0 BATCH ────────────────────────────────────────────────────────
        if text.lower().startswith("/batch"):
            print("BatchTool: use via agent or pass JSON array of tool calls.")
            if self.batch_tool:
                print(self.batch_tool.stats())
            return True

        if text.lower() in ("/kairos-off",):
            if self.kairos:
                self.kairos._signal_cooldown = 999999
                print("KAIROS proactive assistance: OFF")
            return True

        if text.lower() in ("/kairos-on",):
            if self.kairos:
                self.kairos._signal_cooldown = 120
                print("KAIROS proactive assistance: ON")
            return True

        # ── BUDDY commands ────────────────────────────────────────────────────
        if text.lower() in ("/buddy", "/buddy-status"):
            if self.buddy:
                if self.console:
                    self.console.print(self.buddy.status())
                else:
                    print(self.buddy.status())
            else:
                print("BUDDY not available.")
            return True

        if text.lower() in ("/buddy-feed",):
            if self.buddy:
                msg = self.buddy.feed()
                if self.console:
                    self.console.print(f"[magenta]{msg}[/magenta]")
                else:
                    print(f"{C.MG}{msg}{C.EN}")
            return True

        if text.lower().startswith("/buddy-rename "):
            if self.buddy:
                new_name = text[len("/buddy-rename "):].strip()
                msg = self.buddy.rename(new_name)
                if self.console:
                    self.console.print(f"[magenta]{msg}[/magenta]")
                else:
                    print(f"{C.MG}{msg}{C.EN}")
            return True

        if text.lower() in ("/buddy-tip",):
            if self.buddy:
                tip = self.buddy.tip()
                if self.console:
                    self.console.print(f"[magenta]{tip}[/magenta]")
                else:
                    print(f"{C.MG}{tip}{C.EN}")
            return True

        if text.lower() in ("/buddy-stats",):
            if self.buddy:
                if self.console:
                    self.console.print(self.buddy.stats())
                else:
                    print(self.buddy.stats())
            return True

        # ── PERMISSIONS commands ───────────────────────────────────────────────
        if text.lower() in ("/permissions", "/perms"):
            if self.permissions:
                print(self.permissions.status())
                print(self.permissions.stats())
            else:
                print("Permissions not available.")
            return True

        if text.lower().startswith("/perms-mode "):
            mode = text.split(maxsplit=1)[1].strip()
            if self.permissions:
                self.permissions.set_mode(mode)
                self.executor._permissions = self.permissions
                print(f"Permission mode set to: {mode}")
            return True

        if text.lower().startswith("/perms-allow "):
            tool = text.split(maxsplit=1)[1].strip()
            if self.permissions:
                self.permissions.grant_session(tool)
                print(f"Granted (session): {tool}")
            return True

        if text.lower().startswith("/perms-deny "):
            tool = text.split(maxsplit=1)[1].strip()
            if self.permissions:
                self.permissions.deny_session(tool)
                print(f"Denied (session): {tool}")
            return True

        if text.lower() in ("/perms-audit",):
            if self.permissions:
                log = self.permissions.audit_log()
                for e in log[-20:]:
                    icon = "OK" if e["allowed"] else "NO"
                    print(f"  [{icon}] {e['tool']:<30} {e['decision']}")
            return True

        # ── TASK AGENT commands ────────────────────────────────────────────────
        if text.lower().startswith("/task "):
            task = text[len("/task "):].strip()
            if self.task_agent and task:
                print(f"Spawning sub-agent for: {task[:80]}...")
                result = self.task_agent.spawn(task=task)
                status = "OK" if result.success else "FAIL"
                print(f"\n[TaskAgent {result.task_id}] {status} | {result.turns} turns | {result.duration_s:.1f}s")
                print(result.output)
            elif not self.task_agent:
                print("TaskAgent not available.")
            return True

        if text.lower() in ("/tasks",):
            if self.task_agent:
                print(self.task_agent.list_tasks())
            return True

        # ── v8.0 PLAN MODE ────────────────────────────────────────────────────
        if text.lower().startswith("/plan"):
            parts = text.split(maxsplit=1)
            goal  = parts[1] if len(parts) > 1 else ""
            if self.plan_mode:
                print(self.plan_mode.enter(goal))
                # Sync to executor
                if self.executor:
                    self.executor._plan_mode = self.plan_mode
            else:
                print("PlanMode not available.")
            return True

        if text.lower() in ("/approve", "/accept"):
            if self.plan_mode and self.plan_mode.active:
                print(self.plan_mode.exit(approved=True))
                # Re-execute queued steps
                if self.plan_mode.current_plan:
                    for step in (self.plan_mode.current_plan.steps or []):
                        if step.tool:
                            result = self.executor.execute(step.tool, step.args)
                            print(f"  [{step.order}] {step.tool}: {result[:100]}")
            else:
                print("No active plan to approve.")
            return True

        if text.lower() in ("/reject", "/cancel-plan"):
            if self.plan_mode and self.plan_mode.active:
                print(self.plan_mode.exit(approved=False))
            else:
                print("No active plan.")
            return True

        if text.lower() in ("/plan-status",):
            print(self.plan_mode.status() if self.plan_mode else "PlanMode not available.")
            return True

        # ── v8.0 CHECKPOINT ───────────────────────────────────────────────────
        if text.lower() in ("/checkpoints", "/ckpts"):
            print(self.checkpoints.list_checkpoints() if self.checkpoints else "Checkpoints not available.")
            return True

        if text.lower() in ("/checkpoint-undo", "/cundo"):
            print(self.checkpoints.undo() if self.checkpoints else "Checkpoints not available.")
            return True

        if text.lower() in ("/diff-last",):
            print(self.checkpoints.diff_last() if self.checkpoints else "Checkpoints not available.")
            return True

        # ── v8.0 WORKTREE ─────────────────────────────────────────────────────
        if text.lower().startswith("/worktree") or text.lower().startswith("/wt"):
            parts = text.split(maxsplit=2)
            sub   = parts[1] if len(parts) > 1 else "list"
            arg   = parts[2] if len(parts) > 2 else ""
            wm    = self.worktree_mgr
            if not wm:
                print("WorktreeManager not available.")
            elif sub == "list":
                print(wm.list_worktrees())
            elif sub == "create":
                ok, msg = wm.create(arg or None)
                print(msg)
                if ok:
                    ok2, msg2 = wm.enter(msg.split("\n")[0] if "\n" in msg else msg)
                    print(msg2)
            elif sub == "exit":
                ok, msg = wm.exit()
                print(msg)
            elif sub == "remove":
                ok, msg = wm.remove(arg or None)
                print(msg)
            elif sub == "status":
                print(wm.status())
            return True

        # ── v8.0 GITHUB ───────────────────────────────────────────────────────
        if text.lower().startswith("/github") or text.lower().startswith("/gh"):
            parts = text.split(maxsplit=2)
            sub   = parts[1] if len(parts) > 1 else "status"
            arg   = parts[2] if len(parts) > 2 else ""
            gh    = self.github
            if not gh:
                print("GitHub not available.")
            elif sub in ("prs", "list"):
                print(gh.list_prs())
            elif sub == "issues":
                print(gh.list_issues())
            elif sub == "pr":
                pr = gh.get_pr(int(arg)) if arg.isdigit() else None
                if pr:
                    print(f"PR #{pr.number}: {pr.title}\nBranch: {pr.branch}\nStatus: {pr.status}")
                    if pr.failing_checks:
                        print(f"Failing: {', '.join(pr.failing_checks)}")
                else:
                    print("PR not found.")
            elif sub == "fix-pr" and arg.isdigit():
                print(gh.auto_fix_pr(int(arg)))
            elif sub == "status":
                print(gh.stats())
            return True

        # ── v8.0 CRON ─────────────────────────────────────────────────────────
        if text.lower().startswith("/cron"):
            parts = text.split(maxsplit=3)
            sub   = parts[1] if len(parts) > 1 else "list"
            if not self.cron:
                print("CronScheduler not available.")
            elif sub == "list":
                print(self.cron.list_tasks())
            elif sub == "add" and len(parts) >= 4:
                interval = int(parts[2]) if parts[2].isdigit() else 60
                prompt   = parts[3]
                task_id  = self.cron.create(
                    prompt, interval,
                    callback=lambda p: self.send_message(p),
                    name=f"cron-{prompt[:20]}"
                )
                print(f"Cron task created: {task_id} (every {interval}s)")
            elif sub == "delete" and len(parts) >= 3:
                ok = self.cron.delete(parts[2])
                print(f"Deleted: {parts[2]}" if ok else "Task not found.")
            elif sub == "stats":
                print(self.cron.stats())
            return True

        # ── v8.0 HOOKS ────────────────────────────────────────────────────────
        if text.lower().startswith("/hooks"):
            if self.hooks:
                print(self.hooks.list_hooks())
                print(self.hooks.stats())
            else:
                print("HooksEngine not available.")
            return True

        # ── v8.0 WEB UI ───────────────────────────────────────────────────────
        if text.lower().startswith("/webui"):
            if WEBUI_AVAILABLE:
                port = 8000
                parts = text.split()
                if len(parts) > 1 and parts[1].isdigit():
                    port = int(parts[1])
                run_with_qwen(self, port=port)
                print(f"Web UI started at http://localhost:{port}")
            else:
                print("pip install fastapi uvicorn websockets")
            return True

        if text.lower().startswith("/vscode"):
            parts = text.split(maxsplit=1)
            sub   = parts[1].strip() if len(parts) > 1 else "status"
            bridge = self.vscode_bridge
            if sub == "status":
                if bridge:
                    print(bridge.stats())
                else:
                    print("VSCodeBridge not available (pip install websockets)")
            elif sub == "context" and bridge:
                ctx = bridge.build_context_message()
                print(ctx or "No active file context.")
            elif sub == "errors" and bridge:
                errs = bridge.get_errors()
                if errs:
                    for e in errs:
                        print(f"  {e.file}:{e.line} [{e.severity}] {e.message}")
                else:
                    print("No errors in active files.")
            return True

        return False

    def run(self):
        while True:
            try:
                if self.console:
                    user_input = Prompt.ask(f"\n[bold green]You[/]")
                else:
                    user_input = input(f"\n{C.GR}{C.BD}You:{C.EN} ")
                user_input = user_input.strip()
                if not user_input:
                    continue

                if self._handle_meta(user_input):
                    continue

                if user_input.startswith("/"):
                    result = self.skills.handle(user_input)
                    if result is not None:
                        self.send_message(result)
                        continue

                self.send_message(user_input)

            except SystemExit:
                break
            except KeyboardInterrupt:
                print(f"\n{C.YL}Ctrl+C — 'exit' para sair.{C.EN}")
            except Exception as e:
                print(f"\n{C.RD}❌ {type(e).__name__}: {e}{C.EN}")
                logger.exception("Unhandled exception")


# ── ENTRY ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    DEPS = [("rich","rich"),("requests","requests"),("beautifulsoup4","bs4"),
            ("duckduckgo-search","duckduckgo_search"),("tiktoken","tiktoken")]
    missing = [pkg for pkg, mod in DEPS if not __import__("importlib").util.find_spec(mod)]
    if missing:
        print(f"{C.YL}💡 pip install {' '.join(missing)}{C.EN}")

    if not os.path.exists(QWEN_MD):
        Path(QWEN_MD).write_text(
            "# Project Instructions\n\nAdd project-specific instructions here.\n"
            "This file is automatically loaded by Qwen Ultimate on startup.\n",
            encoding="utf-8"
        )
        print(f"{C.DM}✅ Created QWEN.md — add your project instructions there.{C.EN}")

    QwenUltimate().run()