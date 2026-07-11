"""
AI Agent core — handles communication with DeepSeek (OpenAI-compatible) API.
"""

import sys
from typing import Optional
from openai import OpenAI

from src.config import load_config
from src.context_manager import ContextManager


class AIAgent:
    """The AI agent that talks to you, understands context, and searches the web."""

    def __init__(self):
        self.config = load_config()
        self.context = ContextManager(self.config["memory_dir"])
        self.session_id = self._generate_session_id()
        self.client: Optional[OpenAI] = None
        self.web_search_enabled = True  # web search toggle

        # Initialize the API client
        self._init_client()

    # ── Initialization ────────────────────────────────────────────

    def _init_client(self):
        """Set up the API client based on the configured provider."""
        cfg = self.config

        if cfg["provider"] == "deepseek":
            self.client = OpenAI(
                api_key=cfg["api_key"],
                base_url=cfg["api_base"],
            )
            print(f"🔗 Connected to DeepSeek ({cfg['model']})")
        elif cfg["provider"] == "openai":
            self.client = OpenAI(
                api_key=cfg["api_key"],
            )
            print(f"🔗 Connected to OpenAI ({cfg['model']})")
        elif cfg["provider"] == "none":
            print("❌ No API key configured.")
            print("   Copy .secrets.example → .secrets and add your DeepSeek API key.")
            sys.exit(1)
        else:
            print(f"❌ Unknown provider: {cfg['provider']}")
            sys.exit(1)

    @staticmethod
    def _generate_session_id() -> str:
        """Generate a simple session ID based on time."""
        from datetime import datetime
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # ── Building the Prompt ───────────────────────────────────────

    def _build_messages(self, user_input: str) -> list:
        """Build the message list with system prompt, context, and history."""
        messages = []

        # System prompt
        messages.append({"role": "system", "content": self.config["system_prompt"]})

        # Add context from memory
        facts = self.context.get_facts_summary()
        notes = self.context.get_notes_summary()
        if facts or notes:
            context_block = "Here is what I know about the user and our context:"
            if facts:
                context_block += facts
            if notes:
                context_block += notes
            context_block += "\n\nUse this information to personalize your responses."
            messages.append({"role": "system", "content": context_block})

        # Conversation history
        history = self.context.get_conversation_history(self.session_id, limit=10)
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Current user input
        messages.append({"role": "user", "content": user_input})

        return messages

    # ── Chat ──────────────────────────────────────────────────────

    def chat(self, user_input: str) -> str:
        """Send a message to the AI and get a response (with optional web search)."""
        from src.web_search import search_web, format_search_results, should_search

        self._extract_and_store_facts(user_input)

        # Handle explicit /search command
        processed_input = user_input
        search_results_display = None

        if user_input.startswith("/search "):
            search_query = user_input[8:].strip()
            if search_query:
                results = search_web(search_query, max_results=5)
                search_results_display = format_search_results(search_query, results)
                processed_input = (
                    f"I performed a web search for you. Here are the results:\n\n"
                    f"{search_results_display}\n\n"
                    f"Please provide a helpful answer based on these results "
                    f"and your own knowledge. Cite sources where appropriate."
                )
        elif self.web_search_enabled and should_search(user_input):
            results = search_web(user_input, max_results=3)
            if results and "error" not in results[0]:
                search_fmt = format_search_results(user_input, results)
                processed_input = (
                    f"The user asked: \"{user_input}\"\n\n"
                    f"I searched the web and found these relevant results:\n\n"
                    f"{search_fmt}\n\n"
                    f"Please answer based on these results and your own knowledge. "
                    f"Cite sources where helpful."
                )

        # Build messages with the (possibly augmented) input
        messages = self._build_messages(processed_input)

        # Save the original user message to history (not the augmented one)
        self.context.add_to_conversation(self.session_id, "user", user_input)

        try:
            response_text = ""
            stream = self.client.chat.completions.create(
                model=self.config["model"],
                messages=messages,
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
                stream=True,
            )

            # If we did a search, yield the results first so the user sees them
            if search_results_display and "error" not in (search_results_display or ""):
                yield search_results_display + "\n\n---\n\n"

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    response_text += content
                    yield content

            if response_text:
                self.context.add_to_conversation(
                    self.session_id, "assistant", response_text
                )

        except Exception as e:
            error_msg = f"\n\n❌ Error: {e}"
            yield error_msg

    # ── Simple (non-streaming) version ────────────────────────────

    def chat_sync(self, user_input: str) -> str:
        """Non-streaming version — returns the full response at once."""
        messages = self._build_messages(user_input)
        self.context.add_to_conversation(self.session_id, "user", user_input)

        try:
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=messages,
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
            )

            reply = response.choices[0].message.content
            self.context.add_to_conversation(self.session_id, "assistant", reply)
            return reply

        except Exception as e:
            return f"❌ Error: {e}"

    # ── Context Learning ──────────────────────────────────────────

    def _extract_and_store_facts(self, user_input: str):
        """Simple extraction of potential facts from user input."""
        # Look for "I am", "I work", "I like", "my name is" patterns
        import re

        patterns = [
            (r"my name is (\w+)", "personal"),
            (r"I'm? (\w+),?", "personal"),
            (r"I work (?:as|at|for) (.+)", "work"),
            (r"I (?:like|love|enjoy) (.+)", "interests"),
            (r"I (?:use|work with) (.+)", "tools"),
            (r"I live (?:in|at) (.+)", "location"),
            (r"my (?:job|role|title) is (.+)", "work"),
        ]

        for pattern, category in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                fact = match.group(0).strip()
                # Avoid duplicate facts
                existing = self.context.get_facts(category)
                if not any(f["fact"] == fact for f in existing):
                    self.context.add_fact(fact, category)

    # ── Session Management ────────────────────────────────────────

    def switch_session(self, session_id: str):
        """Switch to a different conversation session."""
        self.session_id = session_id

    def list_sessions(self):
        """List all available sessions."""
        return self.context.list_sessions()

    def new_session(self):
        """Start a new conversation session."""
        self.session_id = self._generate_session_id()
        return self.session_id

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        return self.context.delete_session(session_id)

    # ── Model Selection ──────────────────────────────────────────

    def set_model(self, model_name: str):
        """Change the active model. The client stays connected; only the model param updates."""
        self.config["model"] = model_name

    def get_model(self) -> str:
        """Get the currently active model name."""
        return self.config["model"]

    def get_available_models(self) -> list:
        """Return the configurable model list from .secrets (DEEPSEEK_MODELS)."""
        models = self.config.get("models", [])
        if not models:
            # Fallback if DEEPSEEK_MODELS is not set
            models = [self.config.get("model", "deepseek-chat")]
        return models
