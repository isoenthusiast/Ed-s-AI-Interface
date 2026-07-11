# 🧠 Ed's AI Interface

A **local AI agent** that talks to you, remembers your conversations, and learns about your context — powered by DeepSeek.

> 🔒 **100% local.** Your API keys stay on your laptop. Your conversation history stays on your laptop. Nothing leaves your machine except the API calls to DeepSeek.

---

## ✨ Features

- **🤖 Powered by DeepSeek** — Uses DeepSeek's OpenAI-compatible API for fast, capable responses
- **💬 Streaming Chat** — See responses as they're generated (typewriter-style)
- **🧠 Persistent Memory** — Remembers facts about you across sessions
- **📝 Notes System** — Save notes that the agent can reference
- **💾 Conversation History** — Browse, switch between, and manage past sessions
- **🎨 Beautiful CLI** — Rich terminal UI with Markdown rendering, colors, and panels
- **🔐 Secure by Design** — API keys in `.secrets` (gitignored), all data stored locally
- **⚡ Multiple Providers** — Supports DeepSeek, OpenAI, and Anthropic

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

# Launch the agent
python main.py
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

# Launch the agent
python main.py
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

# Run
python main.py
```

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

## 🎮 Commands

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

---

## 📁 Project Structure

```
📂 Ed's AI Interface/
├── main.py                 # 🚀 Entry point
├── src/
│   ├── agent.py            # 🤖 AI Agent (DeepSeek integration)
│   ├── chat_ui.py          # 🎨 CLI interface (Rich)
│   ├── config.py           # ⚙️ Configuration loader
│   ├── context_manager.py  # 🧠 Memory & context management
│   └── __init__.py
├── memory/                 # 💾 Local storage (gitignored content)
├── scripts/
│   ├── setup.ps1           # 🪟 Windows setup
│   └── setup.sh            # 🐧 macOS/Linux setup
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
- **rich** — Beautiful terminal UI
- **chromadb** & **sentence-transformers** — Vector memory (optional, for advanced RAG)

---

## 📄 License

MIT — Do whatever you want with it.

---

<p align="center">
  Built with ❤️ for Ed
</p>
