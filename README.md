<div align="center">

<img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/OpenAI_Agents_SDK-0.17.6-412991?style=for-the-badge&logo=openai&logoColor=white" />
<img src="https://img.shields.io/badge/E2B-Sandbox-FF6B35?style=for-the-badge&logoColor=white" />
<img src="https://img.shields.io/badge/SQLite-Session_Store-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />

# 🐛 Repro Tracker

### A multi-agent AI system that automatically triages bug reports and reproduces them inside a live sandbox — so you know a bug is real before it ever hits your backlog.

*Submit a bug report. Get back a confirmed verdict — triaged, sandboxed, and reproduced autonomously.*

[Features](#-features) · [Architecture](#-architecture) · [Installation](#-installation) · [Usage](#-usage) · [Configuration](#-configuration) · [Project Structure](#-project-structure) · [Roadmap](#-roadmap)

</div>

---

## 📖 Overview

**Repro Tracker** is an autonomous bug reproduction assistant powered by a **multi-agent pipeline** built on the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python). You describe a bug — steps to reproduce, a URL, an error — and the system takes it from there.

A **Triage Agent** parses and structures the report, then hands it off to a **Reproduction Specialist** that spins up a secure [E2B](https://e2b.dev/) sandbox, visits the URL, runs Playwright automation scripts, and returns a clear verdict.

- 🛡️ A **Guardrail** blocks prompt injection before anything runs
- 🗂️ A **Triage Agent** structures freeform bug reports and routes them
- 🔬 A **Reproduction Specialist** executes curl checks and Playwright scripts in an isolated sandbox
- ✅ A final **verdict** — `REPRODUCED`, `NOT REPRODUCED`, or `PARTIAL` — with evidence

> Think of it as a QA engineer who never sleeps, never skips steps, and always shows their work.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **Multi-Agent Orchestration** | Triage and Reproduction agents each own a distinct phase; handoffs are automatic |
| 🔬 **Live Sandbox Execution** | Powered by E2B — browser automation and HTTP checks run in an isolated, ephemeral environment |
| 🎭 **Playwright Automation** | Visits repro URLs, fills forms, clicks buttons, and captures console output and errors |
| 🛡️ **Prompt Injection Guardrail** | An LLM classifier intercepts and blocks malicious inputs before they reach any agent |
| 👤 **Human-in-the-Loop Approvals** | Destructive commands are paused for user confirmation before execution |
| 💬 **Persistent Sessions** | Conversation history is stored in SQLite (`bugs.db`) — context carries across turns |
| 🔍 **Known-Issue Lookup** | Checks an existing issue database before attempting reproduction |
| 🌊 **Streaming Output** | Responses and tool calls stream to the terminal in real time |

---

## 🏗️ Architecture

The system uses an **input guardrail → triage → specialist** pattern. Every message is validated before it reaches any agent. On a bug report, the Triage Agent parses it and hands off to the Reproduction Specialist, which operates entirely inside an E2B sandbox.

```
User Input
    │
    ▼
┌──────────────────────────────────────┐
│         Input Guardrail              │  ← LLM classifier blocks prompt injection
│         (gpt-5.4-mini)               │
└──────────────┬───────────────────────┘
               │ (safe input passes through)
               ▼
┌──────────────────────────────────────┐
│        Triage Agent                  │  ← parse_bug_report tool extracts URL,
│        (gpt-5.4-mini)                │    steps, severity, environment
│   General Q&A │ Bug report routing   │
└──────────────┬───────────────────────┘
               │ handoff (on bug report)
               ▼
┌──────────────────────────────────────┐
│      Reproduction Specialist         │  ← Runs inside E2B sandbox
│      (gpt-5.5 · SandboxAgent)        │
│                                      │
│  Step 1 — curl reachability check    │
│  Step 2 — Playwright browser script  │
│  Step 3 — API / backend curl tests   │
│  Step 4 — search_known_issues tool   │
│  Step 5 — human approval (if risky)  │
└──────────────┬───────────────────────┘
               │
               ▼
     Verdict: REPRODUCED / NOT REPRODUCED / PARTIAL
     (with captured exit codes, HTTP status, console output)
```

Sessions are persisted via `SQLiteSession` in `bugs.db`, retaining the last **16 messages** per session.

---

## 📦 Tech Stack

| Package | Version | Role |
|---|---|---|
| `openai-agents[e2b]` | ≥ 0.17.6 | Multi-agent framework, streaming, session management, E2B sandbox integration |
| `python-dotenv` | ≥ 1.2.2 | `.env` environment variable loading |
| **E2B Sandbox** | — | Isolated cloud sandbox for safe execution of curl, Playwright, and shell commands |
| **SQLite** | built-in | Lightweight session store for persistent conversation context |

> **Models:** All inference runs through OpenAI. Model assignments live in `model.py` for easy swapping.

---

## ⚡ Installation

### Prerequisites

- Python **3.12+**
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) package manager (recommended)
- API keys for [OpenAI](https://platform.openai.com/api-keys) and [E2B](https://e2b.dev/)

### Steps

**1. Clone the repository**

```bash
git clone https://github.com/your-username/Repro_Tracker.git
cd Repro_Tracker
```

**2. Install dependencies**

Using `uv` (recommended):
```bash
uv sync
```

Or with pip:
```bash
pip install "openai-agents[e2b]>=0.17.6" python-dotenv
```

**3. Set up environment variables**

```bash
cp .env.example .env
# then fill in your keys
```

---

## ⚙️ Configuration

Create a `.env` file at the project root:

```env
# Required — OpenAI API key (used for all agents and guardrail)
OPENAI_API_KEY=sk-...

# Required — E2B API key for sandboxed reproduction execution
E2B_API_KEY=e2b_...
```

| Variable | Description | Required |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key — powers all three agents and the guardrail classifier | ✅ |
| `E2B_API_KEY` | E2B API key — provisions the sandbox for safe command execution | ✅ |

Get your keys here:
- **OpenAI**: https://platform.openai.com/api-keys
- **E2B**: https://e2b.dev/

### Model Configuration

Edit `model.py` to swap models for any agent:

```python
# model.py
TRIAGE_MODEL    = "gpt-5.4-mini"   # Fast, cheap — handles routing and parsing
REPRO_MODEL     = "gpt-5.5"        # Powerful — drives sandbox reasoning
GUARDRAIL_MODEL = "gpt-5.4-mini"   # Fast classifier for injection detection
```

---

## 🚀 Usage

```bash
uv run python cli.py
# or
python cli.py
```

The CLI starts a conversational loop. You can chat normally, or submit a bug report:

```
Your Repro Tracker is Ready. Type /exit to quit

You : The login button on https://example.com/login does nothing when
      the password field is left empty. Steps: 1) Open URL 2) Leave
      password blank 3) Click Login — no request is sent.

Assistant :
  [tool: parse_bug_report]
  [handoff]
  [tool: search_known_issues]

  Checking reachability... HTTP 200 ✓
  Installing Playwright... done
  Running reproduction script...

  Verdict: REPRODUCED — Playwright confirmed the Login button emits
  no network request when the password field is empty. Console shows
  no validation error either. Screenshot captured.
```

### Human Approval

Before any potentially destructive command, the agent pauses:

```
--- Approval needed ---
POST https://example.com/api/reset with body {"email": "test@test.com"}
Approve? (y/n):
```

Type `/exit` at any prompt to quit.

---

## 📁 Project Structure

```
Repro_Tracker/
│
├── core_agents/
│   ├── triage_agent.py      # Triage Agent — parses reports, routes to specialist
│   └── repro_agent.py       # Reproduction Specialist — SandboxAgent driving E2B
│
├── cli.py                   # Entry point — REPL loop, streaming, session management
├── model.py                 # Model name constants — change models here
├── guardrail.py             # Input guardrail — LLM-based prompt injection detection
├── tools.py                 # Shared tools — parse_bug_report, search_known_issues
│
├── bugs.db                  # SQLite session store (auto-created on first run)
├── pyproject.toml           # Project metadata and dependencies
├── uv.lock                  # Locked dependency versions
└── .env                     # Environment variables (not committed)
```

---

## 🔌 Tools & Guardrails

### `tools.py`

| Tool | Description |
|---|---|
| `parse_bug_report` | Extracts title, repro URL, reproduction steps, severity, and environment from freeform text |
| `search_known_issues` | Queries a known-issues database by title and environment before attempting reproduction |

### `guardrail.py` — Prompt Injection Shield

Every user message passes through an LLM classifier before reaching any agent. Messages that attempt to override system instructions, reveal the system prompt, or impersonate a different role are blocked immediately — the pipeline never sees them.

```
Injection attempt → Guardrail fires → "I can only help with bug reproduction."
```

---

## 🗺️ Roadmap

- [ ] Connect `search_known_issues` to a real issue tracker (GitHub Issues, Jira, Linear)
- [ ] Surface Playwright screenshots in the CLI output
- [ ] Multi-session support with named session IDs
- [ ] Web UI for submitting reports and viewing verdicts
- [ ] Export reports to Markdown or JSON

---

## 🤝 Contributing

Contributions are welcome — bug fixes, new tools, or new agent types.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit with [Conventional Commits](https://www.conventionalcommits.org/): `git commit -m "feat: add your feature"`
4. Push and open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ using the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) + [E2B Sandboxes](https://e2b.dev/)

⭐ Star this repo if it saved you a debugging session!

</div>
