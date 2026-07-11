"""
Configuration loader — reads from .secrets file and environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project root is the parent of the src/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SECRETS_PATH = PROJECT_ROOT / ".secrets"


def load_config() -> dict:
    """Load configuration from .secrets file (or environment variables as fallback)."""

    # Load .secrets if it exists
    if SECRETS_PATH.exists():
        load_dotenv(SECRETS_PATH, override=True)
    else:
        print(f"⚠️  No .secrets file found at {SECRETS_PATH}")
        print("   Copy .secrets.example to .secrets and add your API keys.\n")

    # ── Core API Keys ──────────────────────────────────────────────
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    # ── Pick the active provider ───────────────────────────────────
    if deepseek_key and not deepseek_key.startswith("sk-your"):
        provider = "deepseek"
        api_key = deepseek_key
        api_base = "https://api.deepseek.com/v1"
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    elif openai_key and not openai_key.startswith("sk-your"):
        provider = "openai"
        api_key = openai_key
        api_base = "https://api.openai.com/v1"
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    elif anthropic_key and not anthropic_key.startswith("sk-ant"):
        provider = "anthropic"
        api_key = anthropic_key
        api_base = ""  # Anthropic uses a different client
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    else:
        provider = "none"
        api_key = ""
        api_base = ""
        model = ""

    # ── Agent Preferences ──────────────────────────────────────────
    config = {
        "provider": provider,
        "api_key": api_key,
        "api_base": api_base,
        "model": model,
        "agent_name": os.getenv("AGENT_NAME", "Ed's AI Assistant"),
        "temperature": float(os.getenv("AGENT_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("AGENT_MAX_TOKENS", "4096")),
        "system_prompt": os.getenv(
            "AGENT_SYSTEM_PROMPT",
            "You are a helpful AI assistant for Ed. You are knowledgeable, "
            "friendly, and context-aware. Use conversation history and stored "
            "memories to provide personalized, relevant responses.",
        ),
        "memory_dir": PROJECT_ROOT / "memory",
    }

    return config
