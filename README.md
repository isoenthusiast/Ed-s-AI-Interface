# 🧠 Ed's AI Interface

A **local AI agent** with a beautiful Windows desktop app — powered by DeepSeek.

> 🔒 **100% local.** Your API keys stay on your laptop. Your conversation history stays on your laptop. Nothing leaves your machine except the API calls to DeepSeek.

---

## ✨ Features

- **🖥️ Desktop GUI** — Clean greyscale-themed chat interface built with CustomTkinter
- **🤖 Powered by DeepSeek** — Uses DeepSeek's OpenAI-compatible API (also supports OpenAI & Anthropic)
- **💬 Streaming Chat** — See responses as they're generated, rendered with full Markdown formatting
- **📋 Conversation Management** — Browse, switch, rename, archive, and delete conversations
- **↔️ Resizable Sidebar** — Click and drag the divider between the sidebar and chat to resize
- **📝 Custom Names** — Rename conversations for easy identification
- **📦 Archiving** — Archive old conversations to keep the active list clean (unarchive anytime)
- **🗑️ Delete** — Permanently delete conversations with a confirmation dialog
- **🧠 Persistent Memory** — SQLite database stores all conversations, facts, and notes
- **🎨 Markdown Rendering** — Bold, italic, code blocks, headings, lists, and links render visually in chat bubbles
- **🔐 Secure by Design** — API keys in `.secrets` (gitignored), all data stored locally
- **📋 Menu Bar** — Conversation menu (New, Rename, Archive, Delete, Clear) + keyboard shortcuts
- **🖱️ Right-Click Context Menus** — Quick access to archive, rename, and delete on any conversation

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** — [Download](https://python.org)
- **DeepSeek API Key** — [Get one here](https://platform.deepseek.com/api_keys)

### Windows (PowerShell)

```powershell
# Run the setup script
.\scripts\setup.ps1

# Activate the virtual environment
.\.venv\Scripts\activate

# Edit your API key
# Open .secrets and set DEEPSEEK_API_KEY

# Launch the desktop app
python gui_main.py
```

### macOS / Linux

```bash
# Run the setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Activate the virtual environment
source .venv/bin/activate

# Edit your API key
# Open .secrets and set DEEPSEEK_API_KEY

# Launch the desktop app
python gui_main.py
```

### Manual Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate it
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up secrets
cp .secrets.example .secrets
# Then edit .secrets with your DeepSeek API key

# Run (choose one)
python gui_main.py   # 🖥️ Desktop GUI app
python main.py        # ⌨️  CLI version (Rich terminal)
```

---

## 🖥️ Desktop GUI

Launch the app with `python gui_main.py` and a clean greyscale-themed window appears:

```
┌──────────────────────────────────────────────────────────────┐
│ 🧠 Ed's AI Assistant                                — □ ×   │
├────────────┬─────────────────────────────────────────────────┤
│ 💬 Chats   │  🧠 Assistant (Markdown rendered)               │
│            │  ┌─────────────────────────────────────────────┐│
│ [+ New]    │  │ **Bold**, *italic*, `code`, headings,      ││
│            │  │ lists, and links all render visually       ││
│ ── Active ─│  └─────────────────────────────────────────────┘│
│ Hello...   │  ┌─────────────────────────────────────────────┐│
│ Tell me... │  │ 🧑 You                                      ││
│            │  │ What is DeepSeek?                           ││
│ ── Archive ─│  └─────────────────────────────────────────────┘│
│ Old chat   │                                                 │
│            │  ┌──────────────────────────────────────┬──────┐│
│            │  │ Type a message...                   │  ➤   ││
│            │  └──────────────────────────────────────┴──────┘│
├────────────┴─────────────────────────────────────────────────┤
│ 🔗 deepseek (deepseek-v4-flash)                ✅ Ready      │
└──────────────────────────────────────────────────────────────┘
```

### GUI Features

| Feature | How to use |
|---------|-----------|
| **↔️ Resizable sidebar** | Click & drag the grey divider between sidebar and chat |
| **✏️ Rename conversation** | Right-click → Rename, or Menu → Rename (`Ctrl+R`) |
| **📦 Archive** | Right-click → Archive, or Menu → Archive (`Ctrl+E`) |
| **📬 Unarchive** | Click on "Archived" section → right-click → Unarchive |
| **🗑️ Delete** | Right-click → Delete, or Menu → Delete (`Ctrl+D`) — confirmation shown |
| **➕ New chat** | Click `+` button, or Menu → New (`Ctrl+N`) |
| **📋 Clear chat** | Menu → Clear Chat (clears display, keeps history) |
| **🖱️ Right-click menu** | Right-click any conversation for quick actions |
| **⌨️ Keyboard shortcuts** | `Ctrl+N` new, `Ctrl+R` rename, `Ctrl+E` archive, `Ctrl+D` delete, `Ctrl+Q` quit |

### Sidebar Sections

- **Active** — current conversations (shown at top)
- **Archived** — hidden conversations (shown at bottom with count, expandable)
- Conversation titles **wrap** to fit the panel width — no truncation

---

## 🔒 Secrets & Security

| File | Purpose | Git |
|------|---------|-----|
| `.secrets` | Your API keys and private config | ❌ Ignored |
| `.secrets.example` | Template with all options | ✅ Tracked |

**.secrets** is in `.gitignore` — it will **never** be committed to the repository.

```
# .secrets format:
DEEPSEEK_API_KEY=sk-your-actual-key-here
DEEPSEEK_MODEL=deepseek-chat
```

---

## 🎮 Commands (CLI only)

These work in the CLI version (`python main.py`):

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/new` | Start a new conversation |
| `/sessions` | List all past sessions |
| `/switch <id>` | Switch to a session |
| `/delete <id>` | Delete a session |
| `/facts` | Show what I've learned about you |
| `/note <title> \| <content>` | Save a note |
| `/notes` | Show your notes |
| `/forget` | Clear all stored facts |
| `/clear` | Clear screen |
| `/exit` | Quit |

In the **Desktop GUI** (`python gui_main.py`), all these actions are available via the **menu bar**, **right-click context menus**, and **keyboard shortcuts**.

---

## 📁 Project Structure

```
📂 Ed's AI Interface/
├── main.py                 # 🚀 CLI entry point
├── gui_main.py             # 🖥️ Desktop GUI entry point
├── src/
│   ├── agent.py            # 🤖 AI Agent (DeepSeek integration)
│   ├── chat_ui.py          # ⌨️  CLI interface (Rich)
│   ├── config.py           # ⚙️ Configuration loader
│   ├── context_manager.py  # 🧠 Memory & context (SQLite)
│   ├── gui.py              # 🖥️ Desktop GUI (CustomTkinter)
│   ├── markdown_renderer.py# 📝 Markdown → tkinter renderer
│   └── __init__.py
├── memory/                 # 💾 Local storage
│   └── memory.db           #    └─ SQLite database (gitignored)
├── scripts/
│   ├── setup.ps1           # 🪟 Windows setup
│   ├── setup.sh            # 🐧 macOS/Linux setup
│   └── github-setup.ps1    # 🌐 GitHub repo setup
├── .secrets                # 🔑 Your API keys (DO NOT COMMIT)
├── .secrets.example        # 📄 Secrets template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔧 Configuration

All configuration lives in `.secrets`. Key options:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEEPSEEK_API_KEY` | — | Your DeepSeek API key |
| `DEEPSEEK_MODEL` | `deepseek-chat` | Model to use |
| `AGENT_NAME` | Ed's AI Assistant | Your agent's name |
| `AGENT_TEMPERATURE` | `0.7` | Creativity (0.0–1.0) |
| `AGENT_MAX_TOKENS` | `4096` | Max response length |
| `AGENT_SYSTEM_PROMPT` | — | Custom system prompt |

You can also use OpenAI or Anthropic by setting their respective keys.

---

## 📦 Dependencies

- **openai** — DeepSeek API client (OpenAI-compatible)
- **python-dotenv** — Load `.secrets` file
- **rich** — CLI terminal UI
- **customtkinter** & **Pillow** — Modern desktop GUI
- **sqlite3** — Database (built into Python, zero dependencies)

---

## 📄 License

MIT — Do whatever you want with it.

---

<p align="center">
  Built with ❤️ for Ed
</p>
