# QWEN3-CODER ULTIMATE v9.0

> Advanced AI coding assistant with production-grade architecture — sub-agents, granular permissions, BUDDY companion, and 9 specialized modules.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Providers](https://img.shields.io/badge/Providers-Cerebras%20%7C%20OpenRouter%20%7C%20Together.ai%20%7C%20Ollama-orange)]()

---

## Features

### Core Engine
- **Multi-provider** — Cerebras, OpenRouter, Together.ai, Groq, Puter, Ollama (local)
- **Model routing** — automatically selects best model per task type
- **Thinking mode** — extended reasoning for complex problems
- **Streaming** — real-time token-by-token output
- **Context compression** — auto-compresses history at threshold to stay within limits
- **Cache boundary injection** — efficient prompt caching

### 9 Production Modules
| Module | Description |
|--------|-------------|
| `core/buddy.py` | BUDDY companion — Tamagotchi-style AI pet with XP/levels, 18 species |
| `core/permissions.py` | Granular tool permissions — 6 modes, per-tool allow/deny, audit log |
| `agents/task_agent.py` | Real sub-agents — isolated context, parallel execution, LLM-callable |
| `core/production_hardening.py` | Retry, circuit breaker, rate limiter, error budget |
| `core/prompt_engine.py` | Task-type detection, few-shot injection, SQLite storage |
| `core/context_collapse.py` | Smart history compression, cache optimization |
| `core/reasoning_engine.py` | Chain-of-thought, tree-of-thought, step-back prompting |
| `core/dream_system.py` | Background learning during idle time |
| `ui/web_ui.py` | FastAPI web interface with file tree and live stats |

### BUDDY Companion System
- 18 species: Dragon, Phoenix, Unicorn, Wolf, Fox, Cat, Dog, Owl, Turtle, and more
- XP gains on every interaction — levels 1 to 100
- Events: session start, bug fixed, error, good code, long session
- Persistent state in `.qwen/buddy_state.json`
- Commands: `/buddy`, `/buddy-status`, `/buddy-feed`, `/buddy-tip`, `/buddy-rename`

### Permissions System
- **6 modes**: DEFAULT, ACCEPT_EDITS, PLAN, AUTO, DONT_ASK, BYPASS
- Per-tool allow/deny lists
- Session-level grants
- Full audit log
- Commands: `/permissions`, `/perms-mode`, `/perms-allow`, `/perms-deny`, `/perms-audit`

### Sub-Agent System
- Spawn isolated agents with their own context and history
- Parallel execution via `spawn_parallel()`
- LLM can call `spawn_task` as a tool
- Commands: `/task <description>`, `/tasks`

### Quick Answers
Python-level interception for instant responses (no LLM call needed):
- Current time, date, weekday
- Current working directory

---

## Installation

```bash
git clone https://github.com/joseivictor/qwen3-coder-ultimate
cd qwen3-coder-ultimate
pip install -r requirements.txt
```

### Configuration

Edit `qwen_config.json`:

```json
{
  "provider": "cerebras",
  "cerebras_token": "YOUR_TOKEN",
  "openrouter_token": "YOUR_TOKEN",
  "together_token": "YOUR_TOKEN",
  "model": "qwen/qwen3-coder:free",
  "temperature": 0.2,
  "max_tokens": 8192,
  "thinking_mode": true,
  "model_routing": true
}
```

**Free tier:** Use Cerebras (fastest) or OpenRouter free models — no credit card needed.
**Best quality:** Get a Together.ai token and use `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8`.

---

## Usage

### Terminal
```bash
# Windows
qwen.bat

# Or directly
python -X utf8 qwen_ultimate.py
```

### VS Code
Open Command Palette → `Tasks: Run Task` → `QWEN3-CODER: Start`

### Web UI
```bash
python ui/web_ui.py
# Open http://localhost:8765
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/stats` | Session statistics (all 9 modules) |
| `/model <name>` | Switch model |
| `/mode <mode>` | Switch provider mode |
| `/clear` | Clear history |
| `/save` | Save current session |
| `/buddy` | Show BUDDY companion |
| `/buddy-feed` | Feed your companion |
| `/task <desc>` | Spawn a sub-agent |
| `/permissions` | Show permission rules |
| `/perms-mode auto` | Set permission mode |
| `/web` | Start web interface |
| `/think <query>` | Force deep reasoning |
| `/plan <goal>` | Enter plan mode |

---

## Supported Models

| Model | Provider | Quality | Cost |
|-------|----------|---------|------|
| Qwen3-235B-A22B | Cerebras | Good | Free |
| Qwen/Qwen3-Coder:free | OpenRouter | Good | Free |
| Qwen/Qwen3-Coder-480B | Together.ai | Excellent | Paid |
| DeepSeek-V3 | Together.ai | Excellent | Paid |
| GLM-5 | OpenRouter | Excellent | Free |
| qwen2.5-coder:7b | Ollama (local) | Decent | Free/Local |

---

## Architecture

```
qwen_ultimate.py          — Main entry point, QwenUltimate class
├── core/
│   ├── buddy.py          — BUDDY companion
│   ├── permissions.py    — Permission manager
│   ├── production_hardening.py — Retry/circuit breaker
│   ├── prompt_engine.py  — Prompt optimization
│   ├── context_collapse.py — History compression
│   ├── reasoning_engine.py — Advanced reasoning
│   ├── dream_system.py   — Background learning
│   └── session_state.py  — Session management
├── agents/
│   ├── task_agent.py     — Sub-agent system
│   ├── memory_agent.py   — Memory retrieval
│   └── critic_agent.py   — Code critic
├── ui/
│   └── web_ui.py         — FastAPI web interface
├── tools/                — Tool implementations
├── scripts/
│   └── feed_model.py     — HuggingFace dataset ingestion
└── qwen_config.json      — Configuration
```

---

## License

MIT — free to use, modify, and distribute.

---

*Built with Qwen3, Cerebras, OpenRouter, Together.ai, FastAPI, and Python.*
