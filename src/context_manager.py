"""
Context Manager — stores memories, conversation history, and personal context.
Uses SQLite for lightweight, dependency-free persistence.
"""

import json
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional


class ContextManager:
    """Manages the agent's memory using SQLite — zero extra dependencies."""

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = memory_dir / "memory.db"
        self._lock = threading.Lock()  # thread-safe writes

        # Tables
        self._init_db()
        # Migrate any lingering JSON data
        self._migrate_from_json()

    # ═══════════════════════════════════════════════════════════════
    #  Database Setup
    # ═══════════════════════════════════════════════════════════════

    def _connect(self) -> sqlite3.Connection:
        """Get a new database connection (thread-safe)."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")        # faster concurrent reads
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT    NOT NULL,
                    role        TEXT    NOT NULL CHECK(role IN ('user','assistant','system')),
                    content     TEXT    NOT NULL,
                    timestamp   TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_conv_session
                    ON conversations(session_id, id);

                CREATE TABLE IF NOT EXISTS projects (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL UNIQUE,
                    created_at  TEXT    NOT NULL,
                    updated_at  TEXT    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    session_id  TEXT    PRIMARY KEY,
                    project_id  INTEGER DEFAULT NULL REFERENCES projects(id) ON DELETE SET NULL,
                    name        TEXT    DEFAULT NULL,
                    archived    INTEGER NOT NULL DEFAULT 0,
                    created_at  TEXT    NOT NULL,
                    updated_at  TEXT    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS facts (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    fact        TEXT    NOT NULL,
                    category    TEXT    NOT NULL DEFAULT 'general',
                    timestamp   TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_facts_category
                    ON facts(category);

                CREATE TABLE IF NOT EXISTS notes (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    title       TEXT    NOT NULL,
                    content     TEXT    NOT NULL,
                    timestamp   TEXT    NOT NULL DEFAULT (datetime('now'))
                );
            """)
            # Migrations for older DB versions
            try:
                conn.execute("ALTER TABLE sessions ADD COLUMN name TEXT DEFAULT NULL")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE sessions ADD COLUMN project_id INTEGER DEFAULT NULL REFERENCES projects(id) ON DELETE SET NULL")
            except sqlite3.OperationalError:
                pass
            # Ensure index exists on project_id
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id)")
            except sqlite3.OperationalError:
                pass

    # ═══════════════════════════════════════════════════════════════
    #  Migration from JSON (one-time)
    # ═══════════════════════════════════════════════════════════════

    def _migrate_from_json(self):
        """Import data from old JSON files if they exist and DB is empty."""
        conv_file = self.memory_dir / "conversations.json"
        facts_file = self.memory_dir / "facts.json"
        notes_file = self.memory_dir / "notes.json"

        with self._connect() as conn:
            # Check if DB already has data
            count = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            if count > 0:
                return  # already migrated

            # Migrate conversations
            if conv_file.exists():
                try:
                    with open(conv_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        for session_id, messages in data.items():
                            for msg in messages:
                                conn.execute(
                                    "INSERT INTO conversations (session_id, role, content, timestamp) VALUES (?,?,?,?)",
                                    (session_id, msg.get("role", "user"),
                                     msg.get("content", ""),
                                     msg.get("timestamp", datetime.now().isoformat()))
                                )
                        conn.commit()
                except (json.JSONDecodeError, Exception):
                    pass

            # Migrate facts
            if facts_file.exists():
                try:
                    with open(facts_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        for fact in data:
                            conn.execute(
                                "INSERT INTO facts (fact, category, timestamp) VALUES (?,?,?)",
                                (fact.get("fact", ""), fact.get("category", "general"),
                                 fact.get("timestamp", datetime.now().isoformat()))
                            )
                        conn.commit()
                except (json.JSONDecodeError, Exception):
                    pass

            # Migrate notes
            if notes_file.exists():
                try:
                    with open(notes_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        for note in data:
                            conn.execute(
                                "INSERT INTO notes (title, content, timestamp) VALUES (?,?,?)",
                                (note.get("title", ""), note.get("content", ""),
                                 note.get("timestamp", datetime.now().isoformat()))
                            )
                        conn.commit()
                except (json.JSONDecodeError, Exception):
                    pass


    # ═══════════════════════════════════════════════════════════════
    #  Conversation History
    # ═══════════════════════════════════════════════════════════════

    def get_conversation_history(self, session_id: str, limit: int = 20) -> list:
        """Get recent conversation messages for a session."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT role, content, timestamp FROM conversations
                   WHERE session_id = ? ORDER BY id ASC""",
                (session_id,)
            ).fetchall()
        if limit:
            rows = rows[-limit:]
        return [{"role": r["role"], "content": r["content"],
                 "timestamp": r["timestamp"]} for r in rows]

    def _ensure_session_meta(self, session_id: str, conn: sqlite3.Connection):
        """Auto-create session metadata row if it doesn't exist."""
        now = datetime.now().isoformat()
        conn.execute(
            """INSERT OR IGNORE INTO sessions (session_id, archived, created_at, updated_at)
               VALUES (?, 0, ?, ?)""",
            (session_id, now, now)
        )

    def add_to_conversation(self, session_id: str, role: str, content: str):
        """Add a message to the conversation history."""
        now = datetime.now().isoformat()
        with self._lock, self._connect() as conn:
            self._ensure_session_meta(session_id, conn)
            conn.execute(
                "INSERT INTO conversations (session_id, role, content, timestamp) VALUES (?,?,?,?)",
                (session_id, role, content, now)
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (now, session_id)
            )
            # Enforce cap: keep newest 100 messages per session
            conn.execute("""
                DELETE FROM conversations WHERE id IN (
                    SELECT id FROM conversations WHERE session_id = ?
                    ORDER BY id DESC LIMIT -1 OFFSET 100
                )
            """, (session_id,))
            conn.commit()

    def list_sessions(self, include_archived: bool = False) -> list:
        """Return list of session IDs with message counts and last activity.
        
        Args:
            include_archived: If True, return ALL sessions. If False (default),
                             return only active (non-archived) sessions.
        """
        with self._connect() as conn:
            if include_archived:
                where = ""
            else:
                where = "WHERE s.archived = 0"
            rows = conn.execute(f"""
                SELECT s.session_id,
                       s.name,
                       s.archived,
                       s.project_id,
                       COALESCE(p.name, NULL) AS project_name,
                       COALESCE(c.cnt, 0) AS cnt,
                       s.updated_at AS last_ts,
                       c.last_msg
                FROM sessions s
                LEFT JOIN projects p ON p.id = s.project_id
                LEFT JOIN (
                    SELECT session_id,
                           COUNT(*) AS cnt,
                           MAX(timestamp) AS max_ts,
                           (SELECT content FROM conversations c2
                            WHERE c2.session_id = conversations.session_id
                            ORDER BY c2.id DESC LIMIT 1) AS last_msg
                    FROM conversations
                    GROUP BY session_id
                ) c ON c.session_id = s.session_id
                {where}
                ORDER BY s.updated_at DESC
            """).fetchall()
        return [{
            "id": r["session_id"],
            "name": r["name"],
            "archived": bool(r["archived"]),
            "count": r["cnt"],
            "last_active": r["last_ts"],
            "preview": (r["last_msg"] or "")[:80],
            "project_id": r["project_id"],
            "project_name": r["project_name"],
        } for r in rows]

    def archive_session(self, session_id: str) -> bool:
        """Archive a conversation (hides it from the default view)."""
        with self._lock, self._connect() as conn:
            self._ensure_session_meta(session_id, conn)
            cur = conn.execute(
                "UPDATE sessions SET archived = 1, updated_at = datetime('now') WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()
            return cur.rowcount > 0

    def unarchive_session(self, session_id: str) -> bool:
        """Unarchive a conversation (restores it to the active view)."""
        with self._lock, self._connect() as conn:
            self._ensure_session_meta(session_id, conn)
            cur = conn.execute(
                "UPDATE sessions SET archived = 0, updated_at = datetime('now') WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()
            return cur.rowcount > 0

    def delete_session(self, session_id: str) -> bool:
        """Permanently delete a conversation and all its messages."""
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            cur = conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            return cur.rowcount > 0

    def rename_session(self, session_id: str, new_name: str) -> bool:
        """Rename a conversation."""
        with self._lock, self._connect() as conn:
            self._ensure_session_meta(session_id, conn)
            cur = conn.execute(
                "UPDATE sessions SET name = ?, updated_at = datetime('now') WHERE session_id = ?",
                (new_name, session_id)
            )
            conn.commit()
            return cur.rowcount > 0

    # ═══════════════════════════════════════════════════════════════
    #  Projects
    # ═══════════════════════════════════════════════════════════════

    def create_project(self, name: str) -> int | None:
        """Create a new project. Returns the new project ID, or None if name exists."""
        now = datetime.now().isoformat()
        with self._lock, self._connect() as conn:
            try:
                cur = conn.execute(
                    "INSERT INTO projects (name, created_at, updated_at) VALUES (?, ?, ?)",
                    (name.strip(), now, now)
                )
                conn.commit()
                return cur.lastrowid
            except sqlite3.IntegrityError:
                return None  # duplicate name

    def delete_project(self, project_id: int) -> bool:
        """Delete a project. All sessions in it become uncategorized (NULL project_id)."""
        with self._lock, self._connect() as conn:
            # Set sessions' project_id to NULL first (uncategorized)
            conn.execute(
                "UPDATE sessions SET project_id = NULL WHERE project_id = ?",
                (project_id,)
            )
            cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return cur.rowcount > 0

    def rename_project(self, project_id: int, new_name: str) -> bool:
        """Rename a project."""
        now = datetime.now().isoformat()
        with self._lock, self._connect() as conn:
            try:
                cur = conn.execute(
                    "UPDATE projects SET name = ?, updated_at = ? WHERE id = ?",
                    (new_name.strip(), now, project_id)
                )
                conn.commit()
                return cur.rowcount > 0
            except sqlite3.IntegrityError:
                return False  # duplicate name

    def list_projects(self) -> list:
        """List all projects with conversation counts."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT p.id, p.name, p.created_at, p.updated_at,
                       COALESCE(s.cnt, 0) AS session_count
                FROM projects p
                LEFT JOIN (
                    SELECT project_id, COUNT(*) AS cnt
                    FROM sessions
                    WHERE archived = 0
                    GROUP BY project_id
                ) s ON s.project_id = p.id
                ORDER BY p.name ASC
            """).fetchall()
        return [{
            "id": r["id"],
            "name": r["name"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "session_count": r["session_count"],
        } for r in rows]

    def assign_session_to_project(self, session_id: str, project_id: int | None) -> bool:
        """Assign a session to a project (or None for uncategorized)."""
        now = datetime.now().isoformat()
        with self._lock, self._connect() as conn:
            self._ensure_session_meta(session_id, conn)
            cur = conn.execute(
                "UPDATE sessions SET project_id = ?, updated_at = ? WHERE session_id = ?",
                (project_id, now, session_id)
            )
            conn.commit()
            return cur.rowcount > 0

    def get_sessions_for_project(self, project_id: int | None) -> list:
        """Get sessions for a specific project (None = uncategorized)."""
        with self._connect() as conn:
            if project_id is None:
                where = "WHERE s.project_id IS NULL AND s.archived = 0"
                params = ()
            else:
                where = "WHERE s.project_id = ? AND s.archived = 0"
                params = (project_id,)
            rows = conn.execute(f"""
                SELECT s.session_id, s.name, s.archived, s.project_id,
                       COALESCE(c.cnt, 0) AS cnt,
                       s.updated_at AS last_ts,
                       c.last_msg
                FROM sessions s
                LEFT JOIN (
                    SELECT session_id, COUNT(*) AS cnt,
                           (SELECT content FROM conversations c2
                            WHERE c2.session_id = conversations.session_id
                            ORDER BY c2.id DESC LIMIT 1) AS last_msg
                    FROM conversations GROUP BY session_id
                ) c ON c.session_id = s.session_id
                {where}
                ORDER BY s.updated_at DESC
            """, params).fetchall()
        return [{
            "id": r["session_id"],
            "name": r["name"],
            "count": r["cnt"],
            "last_active": r["last_ts"],
            "preview": (r["last_msg"] or "")[:80],
            "project_id": r["project_id"],
        } for r in rows]

    def get_project_for_session(self, session_id: str) -> dict | None:
        """Get the project that a session belongs to (or None if uncategorized)."""
        with self._connect() as conn:
            row = conn.execute("""
                SELECT p.id, p.name
                FROM sessions s
                LEFT JOIN projects p ON p.id = s.project_id
                WHERE s.session_id = ?
            """, (session_id,)).fetchone()
        if row and row["id"]:
            return {"id": row["id"], "name": row["name"]}
        return None

    # ═══════════════════════════════════════════════════════════════
    #  Facts
    # ═══════════════════════════════════════════════════════════════

    def add_fact(self, fact: str, category: str = "general"):
        """Store a fact about the user or context."""
        now = datetime.now().isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO facts (fact, category, timestamp) VALUES (?,?,?)",
                (fact, category, now)
            )
            conn.commit()

    def get_facts(self, category: Optional[str] = None) -> list:
        """Retrieve stored facts, optionally filtered by category."""
        with self._connect() as conn:
            if category:
                rows = conn.execute(
                    "SELECT fact, category, timestamp FROM facts WHERE category = ? ORDER BY id DESC",
                    (category,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT fact, category, timestamp FROM facts ORDER BY id DESC"
                ).fetchall()
        return [{"fact": r["fact"], "category": r["category"],
                 "timestamp": r["timestamp"]} for r in rows]

    def get_facts_summary(self) -> str:
        """Return a formatted string of all facts for inclusion in prompts."""
        facts = self.get_facts()
        if not facts:
            return ""
        lines = ["\n📌 **What I know about you:**"]
        for f in facts[-20:]:
            lines.append(f"  • {f['fact']}")
        return "\n".join(lines)

    def clear_facts(self):
        """Delete all stored facts."""
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM facts")
            conn.commit()

    # ═══════════════════════════════════════════════════════════════
    #  Notes
    # ═══════════════════════════════════════════════════════════════

    def add_note(self, title: str, content: str):
        """Add a note that the agent can reference."""
        now = datetime.now().isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO notes (title, content, timestamp) VALUES (?,?,?)",
                (title, content, now)
            )
            conn.commit()

    def get_notes(self) -> list:
        """Retrieve all notes."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT title, content, timestamp FROM notes ORDER BY id DESC"
            ).fetchall()
        return [{"title": r["title"], "content": r["content"],
                 "timestamp": r["timestamp"]} for r in rows]

    def get_notes_summary(self) -> str:
        """Return formatted notes for prompt inclusion."""
        notes = self.get_notes()
        if not notes:
            return ""
        lines = ["\n📝 **Your notes to me:**"]
        for n in notes[-10:]:
            lines.append(f"  • **{n['title']}**: {n['content'][:200]}")
        return "\n".join(lines)
