"""
🎨 Desktop GUI for Ed's AI Assistant — built with CustomTkinter.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont
import threading
import time
import os
from datetime import datetime
from typing import Optional
from src.agent import AIAgent
from src.markdown_renderer import MarkdownRenderer

# ── Drag & Drop (tkinterdnd2) ──────────────────────────────────
try:
    from tkinterdnd2 import DND_FILES
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False
    DND_FILES = None

# ── Theme Configuration (Greyscale) ──────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")  # neutral base

# Color palette — pure black & white / greyscale
COLORS = {
    "sidebar_bg": "#f0f0f0",
    "chat_bg": "#ffffff",
    "user_bubble": "#e0e0e0",
    "assistant_bubble": "#f5f5f5",
    "input_bg": "#ffffff",
    "border": "#cccccc",
    "text": "#000000",
    "text_muted": "#777777",
    "accent": "#333333",
    "success": "#1b5e20",
    "hover": "#dcdcdc",
}


class ChatMessage:
    """Represents a single chat message with metadata."""

    def __init__(self, role: str, content: str, timestamp: str = ""):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")


class ChatBubbleFrame(ctk.CTkFrame):
    """A styled message bubble for the chat area with markdown rendering."""

    def __init__(self, master, message: ChatMessage, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        is_user = message.role == "user"

        # Bubble container
        bubble_color = COLORS["user_bubble"] if is_user else COLORS["assistant_bubble"]
        self.bubble = ctk.CTkFrame(
            self,
            fg_color=bubble_color,
            corner_radius=12,
        )
        self.bubble.pack(side="right" if is_user else "left", fill="x", expand=True, pady=(1, 1), padx=(16 if is_user else 4, 4 if is_user else 16))

        # Role label + time
        header_frame = ctk.CTkFrame(self.bubble, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(4, 0))

        role_text = "🧑 You" if is_user else "🧠 Assistant"
        ctk.CTkLabel(
            header_frame,
            text=role_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["accent"] if is_user else "#a78bfa",
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            header_frame,
            text=message.timestamp,
            font=ctk.CTkFont(size=9),
            text_color=COLORS["text_muted"],
            anchor="e",
        ).pack(side="right")

        # ── Rich Text Content (Markdown rendered) ──────────
        content_frame = ctk.CTkFrame(self.bubble, fg_color="transparent")
        content_frame.pack(fill="x", padx=8, pady=(1, 4))

        self.text_widget = tk.Text(
            content_frame,
            wrap="word",
            height=1,  # auto-expand
            bg=bubble_color,
            fg=COLORS["text"],
            font=("Segoe UI", 13),
            borderwidth=0,
            highlightthickness=0,
            padx=6,
            pady=2,
            spacing1=0,
            spacing3=0,
            insertwidth=0,  # no cursor
            cursor="arrow",
            relief="flat",
            state="normal",
        )
        self.text_widget.pack(fill="x", expand=True)

        # Make read-only
        self.text_widget.bind("<Key>", lambda e: "break")
        self.text_widget.bind("<Button-1>", self._handle_click)

        # Markdown renderer
        self.md_renderer = MarkdownRenderer(self.text_widget, base_font_size=13)
        self._table_widgets = []

        # Render initial content (with table replacement if any)
        self.md_renderer.render(message.content)
        self._replace_table_placeholders()
        self._auto_size()

        # Store the full content for re-rendering
        self._content = message.content

    def _auto_size(self):
        """Resize the text widget to fit its content."""
        line_count = int(self.text_widget.index("end-1c").split(".")[0])
        self.text_widget.configure(height=max(line_count, 2))

    def _handle_click(self, event):
        """Allow selecting text but not editing."""
        self.text_widget.focus_set()
        return None  # Allow default click behavior (selection)

    def update_content(self, text: str):
        """Update the message text (for streaming — plain text, no markdown)."""
        self._content = text
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", text)
        self.text_widget.see("end")
        self._clean_table_widgets()

    def finalize_content(self, text: str = None):
        """Re-render with full markdown formatting after streaming completes."""
        if text is not None:
            self._content = text
        self._clean_table_widgets()
        self.md_renderer.render(self._content)
        self._replace_table_placeholders()
        self._auto_size()

    def _clean_table_widgets(self):
        """Remove any existing table sub-widgets."""
        for w in getattr(self, '_table_widgets', []):
            if w.winfo_exists():
                w.destroy()
        self._table_widgets = []

    def _replace_table_placeholders(self):
        """Remove placeholder markers and create scrollable table widgets."""
        tables = getattr(self.md_renderer, 'tables', [])
        if not tables:
            return

        # Remove placeholder text lines from the main widget
        content = self.text_widget.get("1.0", "end-1c")
        for idx in range(len(tables)):
            content = content.replace(f"⸻ TABLE_{idx} ⸻\n", "")
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", content)

        # Create scrollable table widgets below the text
        is_user = self.text_widget.cget("bg") == COLORS["user_bubble"]
        bg = COLORS["user_bubble"] if is_user else COLORS["assistant_bubble"]

        for table_data in tables:
            tf = ctk.CTkFrame(self.bubble, fg_color=bg)
            tf.pack(fill="x", padx=2, pady=(2, 4))

            rows = len(table_data["lines"])
            tw = tk.Text(
                tf, wrap="none", height=rows, bg=bg, fg="#000000",
                font=("Consolas", 11), borderwidth=1, relief="solid",
                padx=4, pady=2, cursor="arrow", state="normal",
            )

            # Configure tags
            tw.tag_configure("table_border", foreground="#aaaaaa")
            tw.tag_configure("table_header", font=("Consolas", 11, "bold"), foreground="#000000")
            tw.tag_configure("table_header_bold", font=("Consolas", 11, "bold"), foreground="#000000")
            tw.tag_configure("table_bold", font=("Consolas", 11, "bold"), foreground="#000000")
            tw.tag_configure("table_code", font=("Consolas", 11), foreground="#555555", background="#f0f0f0")

            cw = table_data["col_widths"]
            all_rows = [table_data.get("header_raw", [])] + table_data.get("body_raw", [])

            def _insert_cell(tw, raw, width, header=False):
                """Insert a cell with inline markdown formatting, padded to width."""
                clean = raw
                # Remove markdown for width calculation
                import re as _re
                dirty = _re.sub(r"\*\*(.+?)\*\*", r"\1", clean)
                dirty = _re.sub(r"__(.+?)__", r"\1", dirty)
                dirty = _re.sub(r"\*(.+?)\*", r"\1", dirty)
                dirty = _re.sub(r"_(.+?)_", r"\1", dirty)
                dirty = _re.sub(r"`(.+?)`", r"\1", dirty)
                dirty = _re.sub(r"\[(.+?)\]\(.+?\)", r"\1", dirty)
                pad = width - len(dirty.strip())
                if pad < 0:
                    pad = 0

                # Insert with inline formatting
                base_tag = "table_header" if header else ""
                self._insert_table_cell(tw, raw, base_tag, pad)

            # Border row
            border = "─" * table_data["total_width"]
            tw.insert("end", "┌" + border[1:-1] + "┐\n", "table_border")

            # Header row
            tw.insert("end", "│ ", ())
            for j, w in enumerate(cw):
                cell = all_rows[0][j] if j < len(all_rows[0]) else ""
                _insert_cell(tw, cell, w, header=True)
                if j < len(cw) - 1:
                    tw.insert("end", " │ ", ())
            tw.insert("end", " │\n", ())

            # Separator
            tw.insert("end", "├" + border[1:-1] + "┤\n", "table_border")

            # Body rows
            for r in range(1, len(all_rows)):
                tw.insert("end", "│ ", ())
                for j, w in enumerate(cw):
                    cell = all_rows[r][j] if j < len(all_rows[r]) else ""
                    _insert_cell(tw, cell, w, header=False)
                    if j < len(cw) - 1:
                        tw.insert("end", " │ ", ())
                tw.insert("end", " │\n", ())

            # Bottom border
            tw.insert("end", "└" + border[1:-1] + "┘\n", "table_border")

            tw.configure(state="disabled")

            sb = ctk.CTkScrollbar(tf, orientation="horizontal", command=tw.xview,
                                   button_color="#cccccc", button_hover_color="#aaaaaa")
            tw.configure(xscrollcommand=sb.set)
            tw.pack(fill="x", expand=True, side="top")
            sb.pack(fill="x", side="bottom")

            self._table_widgets.append(tf)

    def _insert_table_cell(self, tw, text: str, base_tag: str, pad: int):
        """Insert a table cell with inline bold/italic/code formatting, left-padded."""
        import re as _re
        if pad > 0:
            tw.insert("end", " " * pad, base_tag if base_tag else ())

        pos = 0
        pattern = _re.compile(
            r"\*\*(.+?)\*\*|__(.+?)__|\*(.+?)\*|_(.+?)_|`(.+?)`|\[(.+?)\]\(.+?\)"
        )
        while pos < len(text):
            m = pattern.search(text, pos)
            if not m:
                tw.insert("end", text[pos:], base_tag if base_tag else ())
                break
            if m.start() > pos:
                tw.insert("end", text[pos:m.start()], base_tag if base_tag else ())
            if m.group(1) or m.group(2):
                inner = m.group(1) or m.group(2)
                tag = "table_header_bold" if base_tag == "table_header" else "table_bold"
                tw.insert("end", inner, tag)
            elif m.group(3) or m.group(4):
                inner = m.group(3) or m.group(4)
                tw.insert("end", inner, base_tag if base_tag else ())
            elif m.group(5):
                tw.insert("end", m.group(5), "table_code")
            elif m.group(6):
                tw.insert("end", m.group(6), base_tag if base_tag else ())
            pos = m.end()


class ConversationItem(ctk.CTkFrame):
    """A clickable conversation item in the sidebar."""

    ACTIVE_BG = "#d0d0d0"
    HOVER_BG = "#dcdcdc"

    def __init__(self, master, session_id: str, preview: str, last_active: str,
                 is_active: bool = False, archived: bool = False,
                 name: str = None,
                 on_click=None, on_archive=None, on_unarchive=None,
                 on_delete=None, on_rename=None, on_move=None, **kwargs):
        super().__init__(
            master,
            fg_color=self.ACTIVE_BG if is_active else COLORS["sidebar_bg"],
            corner_radius=8,
            cursor="hand2",
            **kwargs
        )
        self.session_id = session_id
        self.is_active = is_active
        self.archived = archived
        self.on_click = on_click
        self.on_archive = on_archive
        self.on_unarchive = on_unarchive
        self.on_delete = on_delete
        self.on_rename = on_rename
        self.on_move = on_move
        self._name = name
        self._preview = preview
        self.configure(corner_radius=8)

        # Build display text (no truncation, will wrap)
        prefix = "📦 " if archived else ""
        display_text = name if name else (preview.strip() if preview else "Empty conversation")
        self._display_text = prefix + display_text

        font_weight = "bold" if is_active else "normal"
        self.label = ctk.CTkLabel(
            self,
            text=self._display_text,
            font=ctk.CTkFont(size=12, weight=font_weight),
            text_color=COLORS["text"],
            anchor="w",
            justify="left",
            wraplength=0,  # updated dynamically on resize
        )
        self.label.pack(side="left", fill="x", expand=True, padx=(10, 4), pady=6)

        # Timestamp
        time_str = last_active[-8:-3] if len(last_active) > 8 else ""
        self.time_label = ctk.CTkLabel(
            self,
            text=time_str,
            font=ctk.CTkFont(size=9),
            text_color=COLORS["text_muted"],
            anchor="e",
        )
        self.time_label.pack(side="right", padx=(0, 8))

        # Bind clicks
        self.bind("<Button-1>", self._on_click)
        self.label.bind("<Button-1>", self._on_click)
        self.bind("<Button-3>", self._on_right_click)
        self.label.bind("<Button-3>", self._on_right_click)

        # Hover effect
        self.bind("<Enter>", lambda e: self._on_hover(True))
        self.bind("<Leave>", lambda e: self._on_hover(False))
        self.label.bind("<Enter>", lambda e: self._on_hover(True))
        self.label.bind("<Leave>", lambda e: self._on_hover(False))

        # Bind to parent resize to update wrap width
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event=None):
        """Update the wrap width to fit the available panel width."""
        self.after(10, self._update_wraplength)

    def _update_wraplength(self):
        """Set wraplength so text wraps instead of truncating."""
        item_w = self.winfo_width()
        if item_w < 50:
            return
        # Available width = item width minus timestamp (~40px) and padding (~30px)
        avail_w = item_w - 70
        if avail_w < 20:
            avail_w = 20
        self.label.configure(wraplength=avail_w)

    def _on_click(self, event=None):
        if self.on_click:
            self.on_click(self.session_id)

    def _on_right_click(self, event):
        """Show context menu on right-click."""
        menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 10),
                       bg="#ffffff", fg="#000000",
                       activebackground="#dcdcdc", activeforeground="#000000")
        menu.add_command(label="Open", command=lambda: self.on_click(self.session_id) if self.on_click else None)
        menu.add_separator()
        menu.add_command(label="Rename", command=lambda: self.on_rename(self.session_id, self._name) if self.on_rename else None)
        menu.add_command(label="Move to Project...", command=lambda: self.on_move(self.session_id) if self.on_move else None)
        menu.add_separator()
        if self.archived:
            menu.add_command(label="Unarchive", command=lambda: self.on_unarchive(self.session_id) if self.on_unarchive else None)
        else:
            menu.add_command(label="Archive", command=lambda: self.on_archive(self.session_id) if self.on_archive else None)
        menu.add_separator()
        menu.add_command(label="Delete", command=lambda: self.on_delete(self.session_id) if self.on_delete else None)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _on_hover(self, entering: bool):
        if not self.is_active:
            self.configure(fg_color=self.HOVER_BG if entering else COLORS["sidebar_bg"])

    def set_active(self, active: bool):
        self.is_active = active
        bg = self.ACTIVE_BG if active else COLORS["sidebar_bg"]
        self.configure(fg_color=bg)
        weight = "bold" if active else "normal"
        self.label.configure(font=ctk.CTkFont(size=12, weight=weight),
                             text_color=COLORS["text"])


class ChatApp(ctk.CTk):
    """Main desktop chat application."""

    # ═══════════════════════════════════════════════════════════
    #  Menu Bar
    # ═══════════════════════════════════════════════════════════

    def _build_menu_bar(self):
        """Build the top menu bar with Conversation and File menus."""
        self.menu_bar = tk.Menu(self, font=("Segoe UI", 11),
                                bg="#f0f0f0", fg="#000000",
                                activebackground="#dcdcdc", activeforeground="#000000",
                                relief="flat", bd=0)

        # ── Conversation Menu ────────────────────────────
        conv_menu = tk.Menu(self.menu_bar, tearoff=0, font=("Segoe UI", 11),
                            bg="#ffffff", fg="#000000",
                            activebackground="#dcdcdc", activeforeground="#000000")
        conv_menu.add_command(label="New Conversation", command=self._new_conversation,
                              accelerator="Ctrl+N")
        conv_menu.add_separator()
        conv_menu.add_command(label="Archive", command=self._menu_archive,
                              accelerator="Ctrl+E")
        conv_menu.add_command(label="Unarchive", command=self._menu_unarchive)
        conv_menu.add_separator()
        conv_menu.add_command(label="Rename", command=self._menu_rename,
                              accelerator="Ctrl+R")
        conv_menu.add_separator()
        conv_menu.add_command(label="Delete", command=self._menu_delete,
                              accelerator="Ctrl+D")
        conv_menu.add_separator()
        conv_menu.add_command(label="Clear Chat", command=self._menu_clear)

        self.menu_bar.add_cascade(label="Conversation", menu=conv_menu)

        # ── Model Menu ───────────────────────────────────
        model_menu = tk.Menu(self.menu_bar, tearoff=0, font=("Segoe UI", 11),
                             bg="#ffffff", fg="#000000",
                             activebackground="#dcdcdc", activeforeground="#000000")
        model_menu.add_command(label="Select Model...", command=self._show_model_selector,
                               accelerator="Ctrl+M")
        model_menu.add_separator()
        # Populate known models
        for m in self.agent.get_available_models():
            model_menu.add_command(
                label=m,
                command=lambda mod=m: self._switch_model(mod),
            )
        self.model_menu = model_menu
        self.menu_bar.add_cascade(label="Model", menu=model_menu)

        # ── File Menu ────────────────────────────────────
        file_menu = tk.Menu(self.menu_bar, tearoff=0, font=("Segoe UI", 11),
                            bg="#ffffff", fg="#000000",
                            activebackground="#dcdcdc", activeforeground="#000000")
        file_menu.add_command(label="Exit", command=self.destroy, accelerator="Ctrl+Q")

        self.menu_bar.add_cascade(label="File", menu=file_menu)

        self.configure(menu=self.menu_bar)

        # Keyboard shortcuts
        self.bind("<Control-n>", lambda e: self._new_conversation())
        self.bind("<Control-d>", lambda e: self._menu_delete())
        self.bind("<Control-e>", lambda e: self._menu_archive())
        self.bind("<Control-r>", lambda e: self._menu_rename())
        self.bind("<Control-m>", lambda e: self._show_model_selector())
        self.bind("<Control-q>", lambda e: self.destroy())

    # ── Menu Actions ─────────────────────────────────────────

    def _menu_archive(self):
        """Archive the current conversation via menu."""
        if self.current_session_id:
            self._archive_session(self.current_session_id)

    def _menu_unarchive(self):
        """Unarchive the current conversation via menu."""
        if self.current_session_id:
            self._unarchive_session(self.current_session_id)

    def _menu_rename(self):
        """Rename the current conversation via menu."""
        if self.current_session_id:
            session_info = None
            for s in self.agent.context.list_sessions(include_archived=True):
                if s["id"] == self.current_session_id:
                    session_info = s
                    break
            current_name = session_info["name"] if session_info and session_info["name"] else ""
            self._show_rename_dialog(self.current_session_id, current_name)

    def _menu_delete(self):
        """Delete the current conversation via menu."""
        if self.current_session_id:
            self._show_delete_confirmation(self.current_session_id)

    def _menu_clear(self):
        """Clear the chat display."""
        self._clear_chat_area()
        self._show_welcome()

    # ═══════════════════════════════════════════════════════════
    #  Model Selection
    # ═══════════════════════════════════════════════════════════

    def _switch_model(self, model_name: str):
        """Switch to a different model and update the UI."""
        old = self.agent.get_model()
        self.agent.set_model(model_name)
        # Update status bar
        provider = self.agent.config["provider"]
        self._set_status(f"🔗 Switched to {model_name}", COLORS["text"])
        # Update window title
        self.title(f"🧠 {self.agent.config['agent_name']} — {model_name}")
        # Also update the status bar provider label
        for child in self.status_bar.winfo_children():
            if isinstance(child, ctk.CTkLabel) and "🔗" in (child.cget("text") or ""):
                child.configure(text=f"🔗 {provider} ({model_name})")
                break

    def _toggle_web_search(self):
        """Toggle web search based on checkbox state."""
        self.agent.web_search_enabled = bool(self.search_toggle.get())
        state = "ON" if self.agent.web_search_enabled else "OFF"
        self._set_status(f"🌐 Web search {state}", COLORS["text"])

    def _show_model_selector(self):
        """Show a dialog to select or type a model name."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Select Model")
        dialog.geometry("460x320")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Center on parent
        x = self.winfo_x() + (self.winfo_width() - 460) // 2
        y = self.winfo_y() + (self.winfo_height() - 320) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text="🤖 Select Model",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(pady=(16, 4))

        current = self.agent.get_model()
        ctk.CTkLabel(
            dialog,
            text=f"Current: {current}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack(pady=(0, 8))

        # Frame for model list
        list_frame = ctk.CTkScrollableFrame(
            dialog,
            fg_color="transparent",
            height=160,
        )
        list_frame.pack(fill="x", padx=20, pady=(0, 8))

        models = self.agent.get_available_models()
        selected_var = tk.StringVar(value=current)

        for m in models:
            is_current = m == current
            btn = ctk.CTkButton(
                list_frame,
                text=f"  {m}" + ("  ✅" if is_current else ""),
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold" if is_current else "normal"),
                fg_color=COLORS["accent"] if is_current else COLORS["sidebar_bg"],
                hover_color="#d0d0d0",
                text_color=COLORS["text"],
                corner_radius=6,
                height=32,
                command=lambda mod=m: [setattr(dialog, "_selected", mod), dialog.destroy()],
            )
            btn.pack(fill="x", pady=1)

        # Custom model entry
        entry_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        entry_frame.pack(fill="x", padx=20, pady=(4, 12))

        ctk.CTkLabel(
            entry_frame,
            text="Or type a custom model:",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w")

        entry = ctk.CTkEntry(
            entry_frame,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["input_bg"],
            text_color=COLORS["text"],
            border_color=COLORS["border"],
            corner_radius=6,
        )
        entry.pack(fill="x", pady=(2, 6))

        def confirm():
            custom = entry.get().strip()
            if custom:
                dialog._selected = custom
            dialog.destroy()

        ctk.CTkButton(
            entry_frame,
            text="Use Custom Model",
            fg_color=COLORS["accent"],
            hover_color="#555555",
            text_color="#ffffff",
            command=confirm,
        ).pack()

        # Wait for dialog and apply selection
        self.wait_window(dialog)
        selected = getattr(dialog, "_selected", None)
        if selected:
            self._switch_model(selected)

    # ═══════════════════════════════════════════════════════════
    #  UI Construction
    # ═══════════════════════════════════════════════════════════

    def __init__(self):
        super().__init__()

        # ── Initialize Agent ──────────────────────────────────
        self.agent = AIAgent()
        self.current_session_id = self.agent.session_id
        self.messages: dict[str, list[ChatMessage]] = {}
        self.is_streaming = False
        self.stream_buffer = ""
        self.current_bubble: Optional[ChatBubbleFrame] = None
        self.selected_project_id: Optional[int] = None  # None = show all, or project id filter
        self.project_widgets: dict[int, ctk.CTkFrame] = {}  # track project item widgets
        self.attached_files: list[dict] = []  # list of {filename, saved_path, content}

        # ── Enable Drag & Drop ───────────────────────────────
        self._dnd_enabled = False
        self._dnd_hovering = False
        self._setup_drag_drop()

        # ── Window Setup ──────────────────────────────────────
        self.title(f"🧠 {self.agent.config['agent_name']}")
        self.geometry("1100x680")
        self.minsize(800, 500)

        # Center on screen
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # ── Build UI ──────────────────────────────────────────
        self._build_menu_bar()
        self._build_ui()

        # Load conversations
        self._refresh_sidebar()

        # Welcome message
        self._show_welcome()

        # Bind keyboard
        self.bind("<Return>", lambda e: self._send_message())
        self.bind("<Control-Return>", lambda e: self._send_message())

        # Show API key dialog if not configured
        if self.agent.client is None:
            self.after(200, self._show_api_key_dialog)

    SIDEBAR_MIN = 180
    SIDEBAR_WIDTH = 260

    def _build_ui(self):
        """Build the complete UI layout with a draggable splitter."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── PanedWindow (draggable divider) ────────────────
        self.pane = tk.PanedWindow(
            self,
            orient="horizontal",
            sashwidth=5,
            sashrelief="flat",
            bg=COLORS["border"],
            bd=0,
        )
        self.pane.grid(row=0, column=0, sticky="nsew")

        # ── Sidebar ─────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(
            self.pane,
            fg_color=COLORS["sidebar_bg"],
            corner_radius=0,
        )
        self.sidebar.grid_rowconfigure(4, weight=1)  # conversation list expands

        # ── Row 0: Project Header ──────────────────────────
        proj_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        proj_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(14, 4))

        ctk.CTkLabel(
            proj_header,
            text="📁 Projects",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        # Add project button
        self.add_project_btn = ctk.CTkButton(
            proj_header,
            text="+",
            width=28,
            height=28,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color="#555555",
            corner_radius=6,
            command=self._show_add_project_dialog,
        )
        self.add_project_btn.pack(side="right")

        # ── Row 1: Project List (scrollable, limited height) ──
        self.project_list_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            height=140,
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent"],
        )
        self.project_list_frame.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 4))

        # ── Row 2: Separator ───────────────────────────────
        ctk.CTkFrame(
            self.sidebar,
            fg_color=COLORS["border"],
            height=1,
        ).grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 4))

        # ── Row 3: Conversations Header ────────────────────
        conv_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        conv_header.grid(row=3, column=0, sticky="ew", padx=12, pady=(4, 4))

        ctk.CTkLabel(
            conv_header,
            text="💬 Conversations",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        # New chat button
        self.new_btn = ctk.CTkButton(
            conv_header,
            text="+",
            width=28,
            height=28,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color="#555555",
            corner_radius=6,
            command=self._new_conversation,
        )
        self.new_btn.pack(side="right")

        # ── Row 4: Conversation List (scrollable) ─────────
        self.conv_list_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent"],
        )
        self.conv_list_frame.grid(row=4, column=0, sticky="nsew", padx=6, pady=4)

        # ── Bind sidebar resize → keep scrollable frames in sync ──
        self.sidebar.bind("<Configure>", self._on_sidebar_resize)

        # ── Main Chat Area ──────────────────────────────────
        self.chat_container = ctk.CTkFrame(
            self.pane,
            fg_color=COLORS["chat_bg"],
            corner_radius=0,
        )
        self.chat_container.grid_rowconfigure(0, weight=1)

        # Chat header
        self.chat_header = ctk.CTkFrame(
            self.chat_container,
            fg_color=COLORS["chat_bg"],
            height=48,
            corner_radius=0,
        )
        self.chat_header.pack(fill="x", padx=16, pady=(8, 0))

        self.chat_title = ctk.CTkLabel(
            self.chat_header,
            text="💬 New Conversation",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text"],
        )
        self.chat_title.pack(side="left")

        self.typing_label = ctk.CTkLabel(
            self.chat_header,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        )
        self.typing_label.pack(side="right", padx=(0, 8))

        # Separator
        ctk.CTkFrame(
            self.chat_container,
            fg_color=COLORS["border"],
            height=1,
        ).pack(fill="x", padx=8)

        # Messages area (scrollable)
        self.messages_frame = ctk.CTkScrollableFrame(
            self.chat_container,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent"],
        )
        self.messages_frame.pack(fill="both", expand=True, padx=8, pady=4)

        # ── Input Area ──────────────────────────────────────
        input_container = ctk.CTkFrame(
            self.chat_container,
            fg_color="transparent",
        )
        input_container.pack(fill="x", padx=12, pady=(4, 12))

        input_bg = ctk.CTkFrame(
            input_container,
            fg_color=COLORS["input_bg"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        input_bg.pack(fill="x", padx=4, pady=4)

        # Text input
        self.input_text = ctk.CTkTextbox(
            input_bg,
            height=44,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            text_color=COLORS["text"],
            border_width=0,
            corner_radius=8,
            wrap="word",
        )
        self.input_text.pack(side="left", fill="x", expand=True, padx=(12, 4), pady=6)
        self.input_text.bind("<Return>", self._on_enter_key)
        self.input_text.bind("<Shift-Return>", lambda e: None)
        self.input_text.focus()

        # Attach button
        self.attach_btn = ctk.CTkButton(
            input_bg,
            text="📎",
            width=40,
            height=36,
            font=ctk.CTkFont(size=16),
            fg_color=COLORS["sidebar_bg"],
            hover_color="#d0d0d0",
            text_color=COLORS["text"],
            corner_radius=8,
            command=self._attach_file,
        )
        self.attach_btn.pack(side="right", padx=(2, 2), pady=6)

        # Search toggle
        self.search_toggle = ctk.CTkCheckBox(
            input_bg,
            text="🌐",
            width=44,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS["accent"],
            hover_color="#555555",
            checkbox_width=22,
            checkbox_height=22,
            border_width=2,
            corner_radius=4,
            command=self._toggle_web_search,
        )
        if self.agent.web_search_enabled:
            self.search_toggle.select()
        self.search_toggle.pack(side="right", padx=(2, 2), pady=6)

        # Send button
        self.send_btn = ctk.CTkButton(
            input_bg,
            text="➤",
            width=40,
            height=36,
            font=ctk.CTkFont(size=18),
            fg_color=COLORS["accent"],
            hover_color="#3a7ee8",
            corner_radius=8,
            command=self._send_message,
        )
        self.send_btn.pack(side="right", padx=(4, 6), pady=6)

        # ── Attachment Chips ───────────────────────────────
        self.attach_chips_frame = ctk.CTkFrame(
            self.chat_container,
            fg_color="transparent",
            height=0,
        )
        self.attach_chips_frame.pack(fill="x", padx=12, pady=(0, 0))

        # ── Status Bar ──────────────────────────────────────
        self.status_bar = ctk.CTkFrame(
            self,
            fg_color=COLORS["sidebar_bg"],
            height=28,
            corner_radius=0,
        )
        self.status_bar.grid(row=1, column=0, sticky="ew")

        provider = self.agent.config["provider"]
        model = self.agent.config["model"]
        ctk.CTkLabel(
            self.status_bar,
            text=f"🔗 {provider} ({model})",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
        ).pack(side="left", padx=12)

        self.status_right = ctk.CTkLabel(
            self.status_bar,
            text="✅ Ready",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["success"],
        )
        self.status_right.pack(side="right", padx=12)

        # ── Register panes in the PanedWindow ──────────────
        self.pane.add(self.sidebar, width=self.SIDEBAR_WIDTH, minsize=self.SIDEBAR_MIN)
        self.pane.add(self.chat_container, minsize=300)

    def _on_sidebar_resize(self, event=None):
        """Keep CTkScrollableFrame internal canvases matching the sidebar width."""
        w = self.sidebar.winfo_width()
        if w < 40:
            return
        inner_w = w - 14  # account for padx
        for sf in (self.project_list_frame, self.conv_list_frame):
            try:
                # Update the canvas width so internal content fills the available space
                sf._parent_canvas.configure(width=inner_w)
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════
    #  API Key / Settings Dialog
    # ═══════════════════════════════════════════════════════════

    def _show_api_key_dialog(self):
        """Show a dialog to enter the DeepSeek API key and select a model."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("🔑 API Configuration")
        dialog.geometry("480x340")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        x = self.winfo_x() + (self.winfo_width() - 480) // 2
        y = self.winfo_y() + (self.winfo_height() - 340) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)  # prevent closing without config

        ctk.CTkLabel(dialog, text="🔑 Configure DeepSeek API",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLORS["text"]).pack(pady=(20, 4))

        ctk.CTkLabel(dialog,
                     text="Enter your API key to get started.\nGet one at: platform.deepseek.com/api_keys",
                     font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_muted"],
                     justify="center").pack(pady=(0, 14))

        # ── API Key ────────────────────────────────────────
        ctk.CTkLabel(dialog, text="API Key",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x", padx=40, pady=(0, 2))
        key_entry = ctk.CTkEntry(dialog, width=400, height=34, font=ctk.CTkFont(size=12),
                                 fg_color=COLORS["input_bg"], text_color=COLORS["text"],
                                 border_color=COLORS["border"], corner_radius=8,
                                 placeholder_text="sk-...", show="•")
        key_entry.pack(padx=40, pady=(0, 12))
        key_entry.focus()

        # ── Model ComboBox ──────────────────────────────────
        ctk.CTkLabel(dialog, text="Default Model",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x", padx=40, pady=(0, 2))

        models = ["deepseek-chat", "deepseek-reasoner", "deepseek-coder"]
        model_var = tk.StringVar(value=models[0])
        combo = ctk.CTkOptionMenu(
            dialog,
            values=models,
            variable=model_var,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["input_bg"],
            text_color=COLORS["text"],
            button_color=COLORS["accent"],
            button_hover_color="#555555",
            dropdown_fg_color="#ffffff",
            dropdown_text_color=COLORS["text"],
            dropdown_font=ctk.CTkFont(size=12),
            corner_radius=8,
            height=34,
            width=400,
        )
        combo.pack(padx=40, pady=(0, 16))

        # ── Buttons ────────────────────────────────────────
        error_label = ctk.CTkLabel(dialog, text="",
                                   font=ctk.CTkFont(size=11),
                                   text_color="#d32f2f")
        error_label.pack(pady=(0, 4))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=(4, 16))

        def save_and_connect():
            api_key = key_entry.get().strip()
            model = model_var.get().strip()
            if not api_key:
                error_label.configure(text="⚠️  Please enter your API key")
                return
            if not api_key.startswith("sk-"):
                error_label.configure(text="⚠️  Key should start with 'sk-'")
                return

            # Write .secrets file
            from datetime import datetime
            from pathlib import Path
            secrets_path = Path(r"c:\Users\edwar\OneDrive\Documents\1 ProgrammingProjects\02 AI UI") / ".secrets"
            # Also try the exe directory (for frozen builds)
            import sys as _sys
            if getattr(_sys, 'frozen', False):
                secrets_path = Path(_sys.executable).resolve().parent / ".secrets"

            content = f"""# Generated by Ed's AI Interface
DEEPSEEK_API_KEY={api_key}
DEEPSEEK_MODEL={model}
DEEPSEEK_MODELS=deepseek-chat, deepseek-reasoner, deepseek-coder
AGENT_NAME=Ed's AI Assistant
AGENT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=4096
AGENT_SYSTEM_PROMPT=You are a helpful AI assistant. You are knowledgeable, friendly, and context-aware. Use the conversation history and stored memories to provide personalized, relevant responses.
"""
            secrets_path.write_text(content, encoding="utf-8")

            # Reconnect the agent
            if self.agent.reconnect():
                dialog.destroy()
                # Update status bar
                for child in self.status_bar.winfo_children():
                    if isinstance(child, ctk.CTkLabel) and "🔗" in (child.cget("text") or ""):
                        child.configure(text=f"🔗 deepseek ({model})")
                        break
                self._set_status("✅ Connected to DeepSeek", COLORS["success"])
                self.title(f"🧠 {self.agent.config['agent_name']} — {model}")
            else:
                error_label.configure(text="❌ Failed to connect. Check your API key.")

        ctk.CTkButton(btn_frame, text="Save & Connect",
                      fg_color=COLORS["accent"], hover_color="#555555",
                      text_color="#ffffff", height=36, width=160,
                      command=save_and_connect).pack(expand=True)

        key_entry.bind("<Return>", lambda e: save_and_connect())

    # ═══════════════════════════════════════════════════════════
    #  Project Management
    # ═══════════════════════════════════════════════════════════

    def _refresh_projects(self):
        """Rebuild the project list in the project panel."""
        for widget in self.project_list_frame.winfo_children():
            widget.destroy()
        self.project_widgets.clear()

        projects = self.agent.list_projects()
        uncategorized_count = sum(
            1 for s in self.agent.context.list_sessions(include_archived=False)
            if s.get("project_id") is None
        )

        # ── "Uncategorized" (always first) ──────────────────
        is_selected = self.selected_project_id is None
        uc_item = ctk.CTkFrame(
            self.project_list_frame,
            fg_color=COLORS["sidebar_bg"] if not is_selected else "#d0d0d0",
            corner_radius=6,
            cursor="hand2",
        )
        uc_item.pack(fill="x", pady=1)

        uc_label = ctk.CTkLabel(
            uc_item,
            text=f"📂 Uncategorized ({uncategorized_count})",
            font=ctk.CTkFont(size=12, weight="bold" if is_selected else "normal"),
            text_color=COLORS["text"],
            anchor="w",
        )
        uc_label.pack(side="left", fill="x", expand=True, padx=8, pady=4)
        uc_item.bind("<Button-1>", lambda e: self._select_project(None))
        uc_label.bind("<Button-1>", lambda e: self._select_project(None))

        # ── Project items ──────────────────────────────────
        for proj in projects:
            is_selected = self.selected_project_id == proj["id"]
            proj_item = ctk.CTkFrame(
                self.project_list_frame,
                fg_color=COLORS["sidebar_bg"] if not is_selected else "#d0d0d0",
                corner_radius=6,
                cursor="hand2",
            )
            proj_item.pack(fill="x", pady=1)
            self.project_widgets[proj["id"]] = proj_item

            proj_label = ctk.CTkLabel(
                proj_item,
                text=f"📁 {proj['name']} ({proj['session_count']})",
                font=ctk.CTkFont(size=12, weight="bold" if is_selected else "normal"),
                text_color=COLORS["text"],
                anchor="w",
            )
            proj_label.pack(side="left", fill="x", expand=True, padx=8, pady=4)
            proj_item.bind("<Button-1>", lambda e, pid=proj["id"]: self._select_project(pid))
            proj_label.bind("<Button-1>", lambda e, pid=proj["id"]: self._select_project(pid))
            # Right-click context menu
            proj_item.bind("<Button-3>", lambda e, pid=proj["id"], nm=proj["name"]: self._project_context_menu(e, pid, nm))
            proj_label.bind("<Button-3>", lambda e, pid=proj["id"], nm=proj["name"]: self._project_context_menu(e, pid, nm))

    def _select_project(self, project_id: int | None):
        """Filter conversations sidebar by the selected project."""
        self.selected_project_id = project_id
        self._refresh_projects()
        self._refresh_conversations()

    def _project_context_menu(self, event, project_id: int, project_name: str):
        """Show context menu for a project (Rename / Delete)."""
        menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 10),
                       bg="#ffffff", fg="#000000",
                       activebackground="#dcdcdc", activeforeground="#000000")
        menu.add_command(label="Rename", command=lambda: self._show_rename_project_dialog(project_id, project_name))
        menu.add_separator()
        menu.add_command(label="Delete", command=lambda: self._show_delete_project_dialog(project_id, project_name))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _show_add_project_dialog(self):
        """Dialog to create a new project."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Project")
        dialog.geometry("400x180")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        x = self.winfo_x() + (self.winfo_width() - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 180) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(dialog, text="📁 Create New Project",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORS["text"]).pack(pady=(16, 8))

        entry = ctk.CTkEntry(dialog, width=340, height=36, font=ctk.CTkFont(size=13),
                             fg_color=COLORS["input_bg"], text_color=COLORS["text"],
                             border_color=COLORS["border"], corner_radius=8,
                             placeholder_text="Project name...")
        entry.pack(padx=30, pady=(0, 8))
        entry.focus()

        def confirm():
            name = entry.get().strip()
            dialog.destroy()
            if name:
                pid = self.agent.create_project(name)
                if pid is None:
                    self._set_status(f"⚠️ Project \"{name}\" already exists", "#ff8a80")
                else:
                    self._set_status(f"📁 Created project \"{name}\"", COLORS["success"])
                self._refresh_projects()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(4, 12))
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#cccccc",
                      hover_color="#bbbbbb", text_color="#000000",
                      width=100, command=dialog.destroy).pack(side="left", expand=True)
        ctk.CTkButton(btn_frame, text="Create", fg_color=COLORS["accent"],
                      hover_color="#555555", text_color="#ffffff",
                      width=100, command=confirm).pack(side="right", expand=True)
        entry.bind("<Return>", lambda e: confirm())

    def _show_rename_project_dialog(self, project_id: int, current_name: str):
        """Dialog to rename a project."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Rename Project")
        dialog.geometry("400x180")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        x = self.winfo_x() + (self.winfo_width() - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 180) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(dialog, text="✏️ Rename Project",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORS["text"]).pack(pady=(16, 8))

        entry = ctk.CTkEntry(dialog, width=340, height=36, font=ctk.CTkFont(size=13),
                             fg_color=COLORS["input_bg"], text_color=COLORS["text"],
                             border_color=COLORS["border"], corner_radius=8)
        entry.insert(0, current_name)
        entry.select_range(0, "end")
        entry.pack(padx=30, pady=(0, 8))
        entry.focus()

        def confirm():
            new_name = entry.get().strip()
            dialog.destroy()
            if new_name and new_name != current_name:
                if self.agent.rename_project(project_id, new_name):
                    self._set_status(f"✏️ Renamed to \"{new_name}\"", COLORS["text"])
                    self._refresh_projects()
                else:
                    self._set_status(f"⚠️ Name \"{new_name}\" already taken", "#ff8a80")

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(4, 12))
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#cccccc",
                      hover_color="#bbbbbb", text_color="#000000",
                      width=100, command=dialog.destroy).pack(side="left", expand=True)
        ctk.CTkButton(btn_frame, text="Rename", fg_color=COLORS["accent"],
                      hover_color="#555555", text_color="#ffffff",
                      width=100, command=confirm).pack(side="right", expand=True)
        entry.bind("<Return>", lambda e: confirm())

    def _show_delete_project_dialog(self, project_id: int, project_name: str):
        """Confirmation dialog before deleting a project."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Delete Project")
        dialog.geometry("420x200")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        x = self.winfo_x() + (self.winfo_width() - 420) // 2
        y = self.winfo_y() + (self.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(dialog, text="🗑️ Delete Project",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORS["text"]).pack(pady=(16, 8))
        ctk.CTkLabel(dialog,
                     text=f"Delete \"{project_name}\"?\nConversations in it will become uncategorized.",
                     font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"],
                     justify="center").pack(pady=(0, 12))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#cccccc",
                      hover_color="#bbbbbb", text_color="#000000",
                      width=100, command=dialog.destroy).pack(side="left", expand=True)
        ctk.CTkButton(btn_frame, text="Delete", fg_color="#d32f2f",
                      hover_color="#b71c1c", width=100,
                      command=lambda: self._confirm_delete_project(project_id, project_name, dialog)
                      ).pack(side="right", expand=True)

    def _confirm_delete_project(self, project_id: int, project_name: str, dialog: ctk.CTkToplevel):
        """Execute project deletion."""
        dialog.destroy()
        if self.agent.delete_project(project_id):
            if self.selected_project_id == project_id:
                self.selected_project_id = None
            self._set_status(f"🗑️ Deleted project \"{project_name}\"", "#ff8a80")
            self._refresh_projects()
            self._refresh_conversations()

    def _show_move_to_project_dialog(self, session_id: str):
        """Dialog to move a conversation to a different project."""
        current_project = self.agent.get_project_for_session(session_id)
        current_pid = current_project["id"] if current_project else None

        dialog = ctk.CTkToplevel(self)
        dialog.title("Move to Project")
        dialog.geometry("360x320")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        x = self.winfo_x() + (self.winfo_width() - 360) // 2
        y = self.winfo_y() + (self.winfo_height() - 320) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(dialog, text="📁 Move Conversation",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["text"]).pack(pady=(14, 8))

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent", height=200)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        # Uncategorized option
        is_current = current_pid is None
        uc_btn = ctk.CTkButton(
            scroll, text=f"📂 Uncategorized" + (" ✅" if is_current else ""),
            anchor="w", font=ctk.CTkFont(size=12, weight="bold" if is_current else "normal"),
            fg_color=COLORS["accent"] if is_current else COLORS["sidebar_bg"],
            hover_color="#d0d0d0", text_color=COLORS["text"],
            corner_radius=6, height=30,
            command=lambda: self._do_move_session(session_id, None, dialog),
        )
        uc_btn.pack(fill="x", pady=1)

        # Project options
        for proj in self.agent.list_projects():
            is_current = current_pid == proj["id"]
            btn = ctk.CTkButton(
                scroll, text=f"📁 {proj['name']}" + (" ✅" if is_current else ""),
                anchor="w", font=ctk.CTkFont(size=12, weight="bold" if is_current else "normal"),
                fg_color=COLORS["accent"] if is_current else COLORS["sidebar_bg"],
                hover_color="#d0d0d0", text_color=COLORS["text"],
                corner_radius=6, height=30,
                command=lambda pid=proj["id"]: self._do_move_session(session_id, pid, dialog),
            )
            btn.pack(fill="x", pady=1)

    def _do_move_session(self, session_id: str, project_id: int | None, dialog: ctk.CTkToplevel):
        """Execute the move."""
        dialog.destroy()
        if self.agent.assign_session_to_project(session_id, project_id):
            label = "Uncategorized" if project_id is None else f"project {project_id}"
            self._set_status(f"📁 Moved to {label}", COLORS["text"])
            self._refresh_projects()
            self._refresh_conversations()

    # ═══════════════════════════════════════════════════════════
    #  Conversation Management
    # ═══════════════════════════════════════════════════════════

    def _refresh_sidebar(self):
        """Refresh both project list and conversation list."""
        self._refresh_projects()
        self._refresh_conversations()

    def _refresh_conversations(self):
        """Refresh the conversation list in the sidebar, filtered by selected project."""
        for widget in self.conv_list_frame.winfo_children():
            widget.destroy()

        # Get sessions filtered by selected project
        if self.selected_project_id is None:
            active_sessions = self.agent.context.list_sessions(include_archived=False)
        else:
            active_sessions = self.agent.get_sessions_for_project(self.selected_project_id)

        all_sessions = self.agent.context.list_sessions(include_archived=True)
        archived_sessions = [s for s in all_sessions if s.get("archived", False)]
        # Also filter archived by project
        if self.selected_project_id is not None:
            archived_sessions = [s for s in archived_sessions if s.get("project_id") == self.selected_project_id]

        # Sort by last active
        active_sessions.sort(key=lambda s: s["last_active"], reverse=True)
        archived_sessions.sort(key=lambda s: s["last_active"], reverse=True)

        has_any = bool(active_sessions or archived_sessions)

        if not has_any:
            ctk.CTkLabel(
                self.conv_list_frame,
                text="No conversations yet\nStart a new chat!",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_muted"],
                justify="center",
            ).pack(pady=30)
            return

        # ── Active Section ─────────────────────────────────
        if active_sessions:
            section_label = ctk.CTkLabel(
                self.conv_list_frame,
                text="   Active",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=COLORS["text"],
                anchor="w",
            )
            section_label.pack(fill="x", padx=6, pady=(6, 2))

            for s in active_sessions:
                is_active = s["id"] == self.current_session_id
                item = ConversationItem(
                    self.conv_list_frame,
                    session_id=s["id"],
                    preview=s.get("preview", ""),
                    last_active=s["last_active"],
                    name=s.get("name"),
                    is_active=is_active,
                    archived=False,
                    on_click=self._switch_conversation,
                    on_archive=self._archive_session,
                    on_delete=self._show_delete_confirmation,
                    on_rename=self._rename_session,
                    on_move=self._show_move_to_project_dialog,
                )
                item.pack(fill="x", pady=1)

        # ── Archived Section ───────────────────────────────
        if archived_sessions:
            # Separator
            ctk.CTkFrame(
                self.conv_list_frame,
                fg_color=COLORS["border"],
                height=1,
            ).pack(fill="x", padx=8, pady=(8, 4))

            section_label = ctk.CTkLabel(
                self.conv_list_frame,
                text=f"   Archived ({len(archived_sessions)})",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=COLORS["text"],
                anchor="w",
            )
            section_label.pack(fill="x", padx=6, pady=(0, 2))

            for s in archived_sessions:
                is_active = s["id"] == self.current_session_id
                item = ConversationItem(
                    self.conv_list_frame,
                    session_id=s["id"],
                    preview=s.get("preview", ""),
                    last_active=s["last_active"],
                    name=s.get("name"),
                    is_active=is_active,
                    archived=True,
                    on_click=self._switch_conversation,
                    on_unarchive=self._unarchive_session,
                    on_delete=self._show_delete_confirmation,
                    on_rename=self._rename_session,
                    on_move=self._show_move_to_project_dialog,
                )
                item.pack(fill="x", pady=1)

    def _switch_conversation(self, session_id: str):
        """Switch to a different conversation."""
        if session_id == self.current_session_id:
            return
        self.current_session_id = session_id
        self.agent.switch_session(session_id)
        self._refresh_sidebar()
        self._load_conversation(session_id)

    def _new_conversation(self):
        """Show a dialog to name the conversation and pick a project, then create it."""
        self._show_new_conversation_dialog()

    def _show_new_conversation_dialog(self):
        """Dialog for creating a new conversation with a title and project selection."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Conversation")
        dialog.geometry("440x280")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        x = self.winfo_x() + (self.winfo_width() - 440) // 2
        y = self.winfo_y() + (self.winfo_height() - 280) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(dialog, text="💬 New Conversation",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORS["text"]).pack(pady=(16, 10))

        # ── Title ──────────────────────────────────────────
        ctk.CTkLabel(dialog, text="Conversation Title",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x", padx=30, pady=(0, 2))
        title_entry = ctk.CTkEntry(dialog, width=380, height=34, font=ctk.CTkFont(size=13),
                                   fg_color=COLORS["input_bg"], text_color=COLORS["text"],
                                   border_color=COLORS["border"], corner_radius=8,
                                   placeholder_text="Optional — leave blank for auto-name")
        title_entry.pack(padx=30, pady=(0, 10))
        title_entry.focus()

        # ── Project Selection ──────────────────────────────
        ctk.CTkLabel(dialog, text="Project",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"], anchor="w").pack(fill="x", padx=30, pady=(0, 2))

        # Dropdown frame
        proj_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        proj_frame.pack(fill="x", padx=30, pady=(0, 12))

        projects = self.agent.list_projects()
        project_names = ["📂 Uncategorized"] + [f"📁 {p['name']}" for p in projects]
        project_ids = [None] + [p["id"] for p in projects]

        # Pre-select current project filter
        default_idx = 0
        if self.selected_project_id is not None:
            for i, pid in enumerate(project_ids):
                if pid == self.selected_project_id:
                    default_idx = i
                    break

        selected_var = tk.StringVar(value=project_names[default_idx])
        dropdown = ctk.CTkOptionMenu(
            proj_frame,
            values=project_names,
            variable=selected_var,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["input_bg"],
            text_color=COLORS["text"],
            button_color=COLORS["accent"],
            button_hover_color="#555555",
            dropdown_fg_color="#ffffff",
            dropdown_text_color=COLORS["text"],
            dropdown_font=ctk.CTkFont(size=12),
            corner_radius=8,
            height=32,
        )
        dropdown.pack(fill="x")

        # ── Buttons ────────────────────────────────────────
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(4, 16))

        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#cccccc",
                      hover_color="#bbbbbb", text_color="#000000",
                      width=100, command=dialog.destroy).pack(side="left", expand=True)

        def confirm():
            title = title_entry.get().strip()
            selected_name = selected_var.get()
            dialog.destroy()
            # Find the project id for the selected name
            pid = None
            for i, name in enumerate(project_names):
                if name == selected_name:
                    pid = project_ids[i]
                    break

            new_id = self.agent.new_session()
            if pid is not None:
                self.agent.assign_session_to_project(new_id, pid)
            if title:
                self.agent.context.rename_session(new_id, title)

            self.current_session_id = new_id
            self.chat_title.configure(text=f"💬 {title}" if title else "💬 New Conversation")
            self._clear_chat_area()
            self._refresh_sidebar()
            self.input_text.focus()
            self._set_status("✅ New conversation started", COLORS["success"])

        ctk.CTkButton(btn_frame, text="Create", fg_color=COLORS["accent"],
                      hover_color="#555555", text_color="#ffffff",
                      width=100, command=confirm).pack(side="right", expand=True)

        title_entry.bind("<Return>", lambda e: confirm())

    def _archive_session(self, session_id: str):
        """Archive a conversation."""
        if self.agent.context.archive_session(session_id):
            self._refresh_sidebar()
            self._set_status(f"📦 Archived conversation", "#a78bfa")
            # If we archived the current conversation, clear the chat
            if session_id == self.current_session_id:
                self._clear_chat_area()
                self._show_welcome()
                self.current_session_id = self.agent.new_session()

    def _unarchive_session(self, session_id: str):
        """Unarchive a conversation back to active."""
        if self.agent.context.unarchive_session(session_id):
            self._refresh_sidebar()
            self._set_status(f"📬 Restored conversation", COLORS["success"])

    def _rename_session(self, session_id: str, current_name: str = None):
        """Show the rename dialog for a conversation."""
        self._show_rename_dialog(session_id, current_name or "")

    def _show_rename_dialog(self, session_id: str, current_name: str = ""):
        """Show a dialog to rename a conversation."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Rename Conversation")
        dialog.geometry("420x200")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Center on parent
        x = self.winfo_x() + (self.winfo_width() - 420) // 2
        y = self.winfo_y() + (self.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text="✏️ Rename Conversation",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            dialog,
            text="Enter a new name for this conversation:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack(pady=(0, 8))

        entry = ctk.CTkEntry(
            dialog,
            width=360,
            height=36,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["input_bg"],
            text_color=COLORS["text"],
            border_color=COLORS["border"],
            corner_radius=8,
        )
        entry.pack(padx=30, pady=(0, 12))
        entry.insert(0, current_name)
        entry.select_range(0, "end")
        entry.focus()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(0, 16))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="#cccccc",
            hover_color="#bbbbbb",
            text_color="#000000",
            width=100,
            command=dialog.destroy,
        ).pack(side="left", expand=True)

        def confirm():
            new_name = entry.get().strip()
            dialog.destroy()
            if new_name and self.agent.context.rename_session(session_id, new_name):
                self._refresh_sidebar()
                self._set_status(f"✏️ Renamed to \"{new_name}\"", COLORS["text"])

        ctk.CTkButton(
            btn_frame,
            text="Rename",
            fg_color=COLORS["accent"],
            hover_color="#555555",
            text_color="#ffffff",
            width=100,
            command=confirm,
        ).pack(side="right", expand=True)

        entry.bind("<Return>", lambda e: confirm())

    def _show_delete_confirmation(self, session_id: str):
        """Show a confirmation dialog before deleting a conversation."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Delete Conversation")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Center on parent
        x = self.winfo_x() + (self.winfo_width() - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text="🗑️ Delete Conversation",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            dialog,
            text="This will permanently delete this conversation\nand all its messages. This cannot be undone.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
            justify="center",
        ).pack(pady=(0, 16))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="#3a3a5a",
            hover_color="#4a4a6a",
            width=100,
            command=dialog.destroy,
        ).pack(side="left", padx=(0, 8), expand=True)

        ctk.CTkButton(
            btn_frame,
            text="Delete",
            fg_color="#d32f2f",
            hover_color="#b71c1c",
            width=100,
            command=lambda: self._confirm_delete(session_id, dialog),
        ).pack(side="right", padx=(8, 0), expand=True)

    def _confirm_delete(self, session_id: str, dialog: ctk.CTkToplevel):
        """Execute the deletion after confirmation."""
        dialog.destroy()
        if self.agent.context.delete_session(session_id):
            # If we deleted the current session, start a new one
            if session_id == self.current_session_id:
                self._clear_chat_area()
                self._show_welcome()
                self.current_session_id = self.agent.new_session()
            self._refresh_sidebar()
            self._set_status("🗑️ Conversation deleted", "#ff8a80")

    def _load_conversation(self, session_id: str):
        """Load and display a conversation's messages."""
        self._clear_chat_area()
        history = self.agent.context.get_conversation_history(session_id, limit=100)

        # Build title from first user message
        title = "💬 Conversation"
        for msg in history:
            if msg["role"] == "user":
                title = f"💬 {msg['content'][:50]}..."
                break
        self.chat_title.configure(text=title)

        # Display messages
        self.messages[session_id] = []
        for msg in history:
            chat_msg = ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("timestamp", "")[-8:-3] if msg.get("timestamp") else "",
            )
            self.messages[session_id].append(chat_msg)
            self._display_message(chat_msg, animate=False)

        self._scroll_to_bottom()

    def _clear_chat_area(self):
        """Clear all message widgets from the chat area."""
        for widget in self.messages_frame.winfo_children():
            widget.destroy()

    # ═══════════════════════════════════════════════════════════
    #  Message Display
    # ═══════════════════════════════════════════════════════════

    def _show_welcome(self):
        """Show welcome message in empty chat."""
        self._clear_chat_area()

        welcome = ChatMessage(
            "assistant",
            f"## 👋 Hello! I'm {self.agent.config['agent_name']}!\n\n"
            f"I'm powered by **{self.agent.config['model']}** and ready to help.\n\n"
            "💡 **Tips:**\n"
            "• Tell me about yourself — I'll remember!\n"
            "• Use **/help** for available commands\n"
            "• Start a new chat with the **+** button\n"
            f"📅 Today is {datetime.now().strftime('%B %d, %Y')}",
        )
        self._display_message(welcome)
        self._scroll_to_bottom()

    def _display_message(self, message: ChatMessage, animate: bool = False):
        """Add a message bubble to the chat area."""
        bubble = ChatBubbleFrame(self.messages_frame, message)
        bubble.pack(fill="x", pady=1)
        if animate:
            # Simple fade-in effect
            self.update_idletasks()
        return bubble

    def _scroll_to_bottom(self):
        """Scroll the messages view to the bottom."""
        self.messages_frame.after(50, lambda: self.messages_frame._parent_canvas.yview_moveto(1.0))

    # ═══════════════════════════════════════════════════════════
    #  Sending Messages
    # ═══════════════════════════════════════════════════════════

    def _on_enter_key(self, event):
        """Handle Enter key (send on Enter, newline on Shift+Enter)."""
        if not event.state & 0x1:  # Shift not pressed
            self._send_message()
            return "break"

    # ═══════════════════════════════════════════════════════════
    #  Drag & Drop File Support
    # ═══════════════════════════════════════════════════════════

    def _setup_drag_drop(self):
        """Load the tkdnd Tcl extension and register this window as a drop target."""
        if not _DND_AVAILABLE:
            return
        try:
            from tkinterdnd2.TkinterDnD import Tk as DnDTk

            # Determine platform-specific tkdnd library path
            import platform as _platform
            system = _platform.system()
            if system == "Windows":
                machine = os.environ.get('PROCESSOR_ARCHITECTURE', _platform.machine())
                if machine == "ARM64":
                    plat = "win-arm64"
                elif machine == "AMD64":
                    plat = "win-x64"
                elif machine == "x86":
                    plat = "win-x86"
                else:
                    raise RuntimeError(f"Unsupported Windows architecture: {machine}")
            else:
                raise RuntimeError(f"Unsupported platform: {system}")

            import tkinterdnd2
            tcl_major = int(self.tk.call('info', 'tclversion').split('.')[0])
            if tcl_major >= 9:
                tcl9_path = os.path.join(os.path.dirname(tkinterdnd2.__file__), 'tkdnd', plat + '-tcl9')
                module_path = tcl9_path if os.path.isdir(tcl9_path) else os.path.join(os.path.dirname(tkinterdnd2.__file__), 'tkdnd', plat)
            else:
                module_path = os.path.join(os.path.dirname(tkinterdnd2.__file__), 'tkdnd', plat)

            self.tk.call('lappend', 'auto_path', module_path)
            self.tk.call('package', 'require', 'tkdnd')

            # Monkey-patch the DnD methods from TkinterDnD.Tk onto this ctk.CTk instance.
            # ctk.CTk doesn't inherit from TkinterDnD.Tk, so we copy the methods over.
            self._subst_format_str_dnd = DnDTk._subst_format_str_dnd
            self._subst_format_dnd = DnDTk._subst_format_dnd
            self._substitute_dnd = DnDTk._substitute_dnd.__get__(self, type(self))
            self._dnd_bind = DnDTk._dnd_bind.__get__(self, type(self))
            self.drop_target_register = DnDTk.drop_target_register.__get__(self, type(self))
            self.dnd_bind = DnDTk.dnd_bind.__get__(self, type(self))

            # Register this window as a file drop target
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<DropEnter>>', self._on_dnd_enter)
            self.dnd_bind('<<DropLeave>>', self._on_dnd_leave)
            self.dnd_bind('<<Drop>>', self._on_dnd_drop)
            self.dnd_bind('<<DropPosition>>', self._on_dnd_position)

            self._dnd_enabled = True
            print("✅ Drag & drop enabled")
        except Exception as e:
            print(f"⚠️  Drag & drop unavailable: {e}")

    def _on_dnd_enter(self, event):
        """Visual feedback when files are dragged over the window."""
        if not self._dnd_hovering:
            self._dnd_hovering = True
            # Highlight the input area with an accent border
            try:
                if hasattr(self, 'input_text') and self.input_text.winfo_exists():
                    self.input_text.configure(border_width=2)
                    self.input_text.configure(border_color=COLORS["accent"])
            except Exception:
                pass

    def _on_dnd_leave(self, event):
        """Reset visual feedback when drag leaves."""
        self._dnd_hovering = False
        try:
            if hasattr(self, 'input_text') and self.input_text.winfo_exists():
                self.input_text.configure(border_width=1)
                self.input_text.configure(border_color=COLORS["border"])
        except Exception:
            pass

    def _on_dnd_position(self, event):
        """Accept the drag by returning the copy action."""
        return "copy"

    def _on_dnd_drop(self, event):
        """Handle files dropped from Windows Explorer."""
        self._on_dnd_leave(event)

        if not event.data:
            return

        files = self.tk.splitlist(event.data)
        from src.attachment_handler import process_attachment

        count = 0
        for filepath in files:
            # Strip curly braces that tkdnd may add around paths with spaces
            filepath = filepath.strip('{}')
            if not os.path.isfile(filepath):
                continue
            try:
                result = process_attachment(filepath)
                self.attached_files.append(result)
                count += 1
            except Exception as e:
                self._set_status(f"❌ Failed to attach {os.path.basename(filepath)}: {e}", "#ff8a80")

        if count > 0:
            self._refresh_attach_chips()
            self._set_status(f"📎 Attached {count} file(s)", COLORS["text"])

    # ═══════════════════════════════════════════════════════════

    def _attach_file(self):
        """Open file dialog and attach one or more files."""
        from tkinter import filedialog
        from src.attachment_handler import process_attachment

        filetypes = [
            ("All Supported", "*.pdf *.docx *.txt *.csv *.md *.markdown"),
            ("PDF Files", "*.pdf"),
            ("Word Documents", "*.docx"),
            ("Markdown Files", "*.md *.markdown"),
            ("Text Files", "*.txt"),
            ("CSV Files", "*.csv"),
        ]
        filepaths = filedialog.askopenfilenames(
            title="Attach files",
            filetypes=filetypes,
        )
        if not filepaths:
            return

        count = 0
        for filepath in filepaths:
            try:
                result = process_attachment(filepath)
                self.attached_files.append(result)
                count += 1
            except Exception as e:
                self._set_status(f"❌ Failed to attach {os.path.basename(filepath)}: {e}", "#ff8a80")

        if count > 0:
            self._refresh_attach_chips()
            self._set_status(f"📎 Attached {count} file(s)", COLORS["text"])

    def _remove_attachment(self, index: int):
        """Remove an attachment at the given index."""
        if 0 <= index < len(self.attached_files):
            removed = self.attached_files.pop(index)
            self._refresh_attach_chips()
            self._set_status(f"📎 Removed: {removed['filename']}", COLORS["text_muted"])

    def _refresh_attach_chips(self):
        """Refresh the attachment chips display."""
        for widget in self.attach_chips_frame.winfo_children():
            widget.destroy()

        if not self.attached_files:
            return

        for i, att in enumerate(self.attached_files):
            chip = ctk.CTkFrame(
                self.attach_chips_frame,
                fg_color=COLORS["sidebar_bg"],
                corner_radius=6,
            )
            chip.pack(side="left", padx=(0, 6), pady=2)

            label_text = f"📄 {att['filename']}  ✕"
            lbl = ctk.CTkLabel(
                chip,
                text=label_text,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text"],
            )
            lbl.pack(side="left", padx=8, pady=3)
            lbl.bind("<Button-1>", lambda e, idx=i: self._remove_attachment(idx))
            chip.bind("<Button-1>", lambda e, idx=i: self._remove_attachment(idx))

    def _send_message(self):
        """Send the current input as a message, including any attachments."""
        content = self.input_text.get("1.0", "end-1c").strip()
        if (not content and not self.attached_files) or self.is_streaming:
            return

        # Build the full prompt — user message + attachment content
        full_content = content
        if self.attached_files:
            attachment_blocks = []
            for att in self.attached_files:
                attachment_blocks.append(
                    f"[Attached file: {att['filename']}]\n\n{att['content']}"
                )
            attachments_text = "\n\n---\n\n".join(attachment_blocks)
            if content:
                full_content = f"{content}\n\n---\n\n{attachments_text}"
            else:
                full_content = f"Please analyze this attached file:\n\n{attachments_text}"

        # Clear input and attachments
        self.input_text.delete("1.0", "end")
        self.attached_files.clear()
        self._refresh_attach_chips()

        # Handle commands
        if content.startswith("/"):
            self._handle_command(content)
            return

        # Create user message — display original text, send full with attachments
        display_content = content if content else "📎 [Files attached]"
        user_msg = ChatMessage("user", display_content)
        self._ensure_session_loaded()
        self.messages.setdefault(self.current_session_id, []).append(user_msg)
        self._display_message(user_msg)
        self._scroll_to_bottom()

        # Update sidebar with new preview
        self._refresh_sidebar()

        # Start streaming AI response with full content (including attachments)
        self._start_streaming(full_content)

    def _ensure_session_loaded(self):
        """Ensure the current session has messages loaded."""
        if self.current_session_id not in self.messages:
            self.messages[self.current_session_id] = []

    def _start_streaming(self, user_input: str):
        """Start streaming an AI response in a background thread."""
        self.is_streaming = True
        self.stream_buffer = ""
        self.send_btn.configure(state="disabled", text="⏳")
        self._set_status("🧠 Thinking...", "#a78bfa")
        self.typing_label.configure(text="🧠 AI is typing...")

        # Create placeholder bubble
        assistant_msg = ChatMessage("assistant", "▊")
        self.current_bubble = self._display_message(assistant_msg)
        self._scroll_to_bottom()

        def stream_worker():
            try:
                for chunk in self.agent.chat(user_input):
                    self.stream_buffer += chunk
                    # Update UI on main thread
                    self.after(0, self._update_streaming)
                # Stream completed successfully
                self.after(0, self._finish_streaming)
            except Exception as e:
                self.after(0, lambda: self._finish_streaming(error=str(e)))

        thread = threading.Thread(target=stream_worker, daemon=True)
        thread.start()

    def _update_streaming(self):
        """Update the streaming message (called from main thread)."""
        if not self.is_streaming or not self.current_bubble:
            return
        display = self.stream_buffer + " ▊" if not self.stream_buffer.endswith("\n") else self.stream_buffer
        self.current_bubble.update_content(display)
        self._scroll_to_bottom()

    def _finish_streaming(self, error: str = ""):
        """Finalize the streaming response."""
        # Ignore if already finished
        if not self.is_streaming:
            return

        if error:
            self.stream_buffer = f"❌ {error}"

        # Save the final message
        if self.stream_buffer:
            final_content = self.stream_buffer
            assistant_msg = ChatMessage("assistant", final_content)
            self.messages.setdefault(self.current_session_id, []).append(assistant_msg)

            if self.current_bubble:
                # Re-render with full markdown formatting
                self.current_bubble.finalize_content(final_content)

            # Update session title
            history = self.agent.context.get_conversation_history(self.current_session_id, limit=1)
            if history:
                first_user = [m for m in history if m["role"] == "user"]
                if first_user:
                    self.chat_title.configure(text=f"💬 {first_user[0]['content'][:50]}...")

        # Reset state
        self.is_streaming = False
        self.stream_buffer = ""
        self.current_bubble = None
        self.send_btn.configure(state="normal", text="➤")
        self.typing_label.configure(text="")
        self._set_status("✅ Ready", COLORS["success"])
        self._refresh_sidebar()
        self._scroll_to_bottom()
        self.input_text.focus()

    # ═══════════════════════════════════════════════════════════
    #  Commands
    # ═══════════════════════════════════════════════════════════

    def _handle_command(self, cmd: str):
        """Handle a slash command."""
        cmd = cmd.strip().lower()

        if cmd == "/help":
            help_text = (
                "**📋 Available Commands**\n\n"
                "• `/help` — Show this help\n"
                "• `/search <query>` — Search the web\n"
                "• `/new` — New conversation\n"
                "• `/sessions` — List all sessions\n"
                "• `/switch <id>` — Switch session\n"
                "• `/facts` — What I know about you\n"
                "• `/notes` — Your saved notes\n"
                "• `/clear` — Clear chat display\n"
                "• `/exit` — Quit"
            )
            msg = ChatMessage("assistant", help_text)
            self._display_message(msg)
            return

        if cmd == "/new":
            self._new_conversation()
            return

        if cmd == "/sessions":
            sessions = self.agent.list_sessions()
            if not sessions:
                msg = ChatMessage("assistant", "📭 No past conversations.")
                self._display_message(msg)
                return
            lines = ["**📋 Your Conversations:**\n"]
            for s in sessions:
                when = s["last_active"][:16].replace("T", " ")
                lines.append(f"• `{s['id']}` — {s['count']} msgs ({when})")
            msg = ChatMessage("assistant", "\n".join(lines))
            self._display_message(msg)
            return

        if cmd.startswith("/switch "):
            sid = cmd[8:].strip()
            self._switch_conversation(sid)
            return

        if cmd == "/facts":
            facts = self.agent.context.get_facts()
            if not facts:
                msg = ChatMessage("assistant", "📭 I don't know anything about you yet. Tell me about yourself!")
                self._display_message(msg)
                return
            lines = ["**📌 What I know about you:**\n"]
            for f in facts[-10:]:
                lines.append(f"• {f['fact']}")
            msg = ChatMessage("assistant", "\n".join(lines))
            self._display_message(msg)
            return

        if cmd == "/notes":
            notes = self.agent.context.get_notes()
            if not notes:
                msg = ChatMessage("assistant", "📭 No notes saved. Use `/note title | content` to add one.")
                self._display_message(msg)
                return
            lines = ["**📝 Your Notes:**\n"]
            for n in notes[-10:]:
                lines.append(f"• **{n['title']}**: {n['content'][:100]}")
            msg = ChatMessage("assistant", "\n".join(lines))
            self._display_message(msg)
            return

        if cmd == "/clear":
            self._clear_chat_area()
            return

        if cmd == "/exit":
            self.destroy()
            return

        # /search query — web search command, send to agent
        if cmd.startswith("/search "):
            self._send_as_normal_message(cmd)
            return

        # Unknown command — send to AI
        self._send_as_normal_message(cmd)

    def _send_as_normal_message(self, content: str):
        """Treat an unrecognized command as a normal message."""
        user_msg = ChatMessage("user", content)
        self._ensure_session_loaded()
        self.messages.setdefault(self.current_session_id, []).append(user_msg)
        self._display_message(user_msg)
        self._scroll_to_bottom()
        self._refresh_sidebar()
        self._start_streaming(content)

    # ═══════════════════════════════════════════════════════════
    #  Status / Helpers
    # ═══════════════════════════════════════════════════════════

    def _set_status(self, text: str, color: str = COLORS["text_muted"]):
        """Update the status bar text."""
        self.status_right.configure(text=text, text_color=color)


def launch_gui():
    """Launch the desktop GUI application."""
    app = ChatApp()
    app.mainloop()
