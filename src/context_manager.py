"""
Context Manager — stores memories, conversation history, and personal context.
Uses a simple JSON-file store (no external DB needed to keep things local & simple).
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class ContextManager:
    """Manages the agent's memory: conversations, facts about the user, and notes."""

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.conversations_file = memory_dir / "conversations.json"
        self.facts_file = memory_dir / "facts.json"
        self.notes_file = memory_dir / "notes.json"

        self._init_storage()

    # ── Initialization ────────────────────────────────────────────

    def _init_storage(self):
        """Ensure storage files exist with default values."""
        if not self.conversations_file.exists():
            self._write_json(self.conversations_file, {})
        if not self.facts_file.exists():
            self._write_json(self.facts_file, [])
        if not self.notes_file.exists():
            self._write_json(self.notes_file, [])

    # ── Conversation History ──────────────────────────────────────

    def get_conversation_history(self, session_id: str, limit: int = 20) -> list:
        """Get recent conversation messages for a session."""
        history = self._read_json(self.conversations_file)
        session = history.get(session_id, [])
        return session[-limit:] if limit else session

    def add_to_conversation(self, session_id: str, role: str, content: str):
        """Add a message to the conversation history."""
        history = self._read_json(self.conversations_file)
        if session_id not in history:
            history[session_id] = []
        history[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        # Keep last 100 messages per session
        history[session_id] = history[session_id][-100:]
        self._write_json(self.conversations_file, history)

    def list_sessions(self) -> list:
        """Return list of session IDs with message counts and last activity."""
        history = self._read_json(self.conversations_file)
        sessions = []
        for sid, messages in history.items():
            if messages:
                sessions.append({
                    "id": sid,
                    "count": len(messages),
                    "last_active": messages[-1]["timestamp"],
                    "preview": messages[-1]["content"][:80],
                })
        return sorted(sessions, key=lambda s: s["last_active"], reverse=True)

    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session."""
        history = self._read_json(self.conversations_file)
        if session_id in history:
            del history[session_id]
            self._write_json(self.conversations_file, history)
            return True
        return False

    # ── Facts (things you've learned about the user) ──────────────

    def add_fact(self, fact: str, category: str = "general"):
        """Store a fact about the user or context."""
        facts = self._read_json(self.facts_file)
        facts.append({
            "fact": fact,
            "category": category,
            "timestamp": datetime.now().isoformat(),
        })
        self._write_json(self.facts_file, facts)

    def get_facts(self, category: Optional[str] = None) -> list:
        """Retrieve stored facts, optionally filtered by category."""
        facts = self._read_json(self.facts_file)
        if category:
            return [f for f in facts if f["category"] == category]
        return facts

    def get_facts_summary(self) -> str:
        """Return a formatted string of all facts for inclusion in prompts."""
        facts = self._read_json(self.facts_file)
        if not facts:
            return ""
        lines = ["\n📌 **What I know about you:**"]
        for f in facts[-20:]:  # last 20 facts
            lines.append(f"  • {f['fact']}")
        return "\n".join(lines)

    # ── Notes (user-taken notes for the agent) ────────────────────

    def add_note(self, title: str, content: str):
        """Add a note that the agent can reference."""
        notes = self._read_json(self.notes_file)
        notes.append({
            "title": title,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        self._write_json(self.notes_file, notes)

    def get_notes(self) -> list:
        """Retrieve all notes."""
        return self._read_json(self.notes_file)

    def get_notes_summary(self) -> str:
        """Return formatted notes for prompt inclusion."""
        notes = self._read_json(self.notes_file)
        if not notes:
            return ""
        lines = ["\n📝 **Your notes to me:**"]
        for n in notes[-10:]:
            lines.append(f"  • **{n['title']}**: {n['content'][:200]}")
        return "\n".join(lines)

    # ── File I/O ──────────────────────────────────────────────────

    @staticmethod
    def _read_json(path: Path) -> dict | list:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {} if path.suffix == "conversations.json" else []

    @staticmethod
    def _write_json(path: Path, data: dict | list):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
