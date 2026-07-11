"""
🎨 Desktop GUI for Ed's AI Assistant — built with CustomTkinter.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont
import threading
import time
from datetime import datetime
from typing import Optional
from src.agent import AIAgent
from src.markdown_renderer import MarkdownRenderer

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
        self.bubble.pack(side="right" if is_user else "left", fill="x", pady=(2, 2), padx=(60 if is_user else 4, 4 if is_user else 60))

        # Role label + time
        header_frame = ctk.CTkFrame(self.bubble, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(6, 0))

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
        content_frame.pack(fill="x", padx=4, pady=(2, 6))

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
            pady=4,
            spacing1=1,
            spacing3=2,
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

        # Render initial content and auto-size
        self.md_renderer.render(message.content)
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
        # During streaming, just show plain text with the renderer
        # We use a fast path: clear and show raw text
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", text)
        self.text_widget.see("end")

    def finalize_content(self, text: str = None):
        """Re-render with full markdown formatting after streaming completes."""
        if text is not None:
            self._content = text
        self.md_renderer.render(self._content)
        self._auto_size()


class ConversationItem(ctk.CTkFrame):
    """A clickable conversation item in the sidebar."""

    ACTIVE_BG = "#d0d0d0"
    HOVER_BG = "#dcdcdc"

    def __init__(self, master, session_id: str, preview: str, last_active: str,
                 is_active: bool = False, archived: bool = False,
                 name: str = None,
                 on_click=None, on_archive=None, on_unarchive=None,
                 on_delete=None, on_rename=None, **kwargs):
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
    #  Draggable Divider
    # ═══════════════════════════════════════════════════════════

    def _divider_start(self, event):
        """Begin dragging the sidebar divider."""
        self._divider_dragging = True
        self._divider_start_x = event.x_root

    def _divider_drag(self, event):
        """Drag the divider to resize the sidebar."""
        if not self._divider_dragging:
            return
        dx = event.x_root - self._divider_start_x
        self._divider_start_x = event.x_root
        new_width = self.sidebar.winfo_width() + dx
        new_width = max(self.SIDEBAR_MIN, min(new_width, self.winfo_width() - 300))
        self.sidebar.configure(width=new_width)
        self.update_idletasks()

    def _divider_stop(self, event):
        """Stop dragging the divider."""
        self._divider_dragging = False

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

    SIDEBAR_MIN = 180
    SIDEBAR_DEFAULT = 260

    def _build_ui(self):
        """Build the complete UI layout."""
        self.grid_columnconfigure(0, minsize=self.SIDEBAR_MIN, weight=0)
        self.grid_columnconfigure(1, weight=0)   # divider
        self.grid_columnconfigure(2, weight=1)   # chat area expands
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ─────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=COLORS["sidebar_bg"],
            corner_radius=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.configure(width=self.SIDEBAR_DEFAULT)
        self.sidebar.grid_rowconfigure(2, weight=1)

        # Sidebar header
        header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(14, 8))

        ctk.CTkLabel(
            header,
            text="💬 Conversations",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        # New chat button
        self.new_btn = ctk.CTkButton(
            header,
            text="+",
            width=32,
            height=32,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color="#555555",
            corner_radius=8,
            command=self._new_conversation,
        )
        self.new_btn.pack(side="right")

        # Separator
        ctk.CTkFrame(
            self.sidebar,
            fg_color=COLORS["border"],
            height=1,
        ).grid(row=1, column=0, sticky="ew", padx=8)

        # Conversation list (scrollable)
        self.conv_list_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent"],
        )
        self.conv_list_frame.grid(row=2, column=0, sticky="nsew", padx=6, pady=4)

        # ── Draggable Divider ───────────────────────────────
        self.divider = ctk.CTkFrame(
            self,
            fg_color=COLORS["border"],
            width=5,
            cursor="sb_h_double_arrow",
            corner_radius=0,
        )
        self.divider.grid(row=0, column=1, sticky="ns")
        self._divider_dragging = False

        # Mouse bindings for divider
        self.divider.bind("<Button-1>", self._divider_start)
        self.divider.bind("<B1-Motion>", self._divider_drag)
        self.divider.bind("<ButtonRelease-1>", self._divider_stop)

        # ── Main Chat Area ──────────────────────────────────
        self.chat_container = ctk.CTkFrame(
            self,
            fg_color=COLORS["chat_bg"],
            corner_radius=0,
        )
        self.chat_container.grid(row=0, column=2, sticky="nsew")
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
        self.input_text.bind("<Shift-Return>", lambda e: None)  # Allow shift+enter for newline
        self.input_text.focus()

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

        # ── Status Bar ──────────────────────────────────────
        self.status_bar = ctk.CTkFrame(
            self,
            fg_color=COLORS["sidebar_bg"],
            height=28,
            corner_radius=0,
        )
        self.status_bar.grid(row=1, column=0, columnspan=3, sticky="ew")

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

    # ═══════════════════════════════════════════════════════════
    #  Conversation Management
    # ═══════════════════════════════════════════════════════════

    def _refresh_sidebar(self):
        """Refresh the conversation list in the sidebar with Active/Archived sections."""
        # Clear existing items
        for widget in self.conv_list_frame.winfo_children():
            widget.destroy()

        # Get sessions
        active_sessions = self.agent.context.list_sessions(include_archived=False)
        all_sessions = self.agent.context.list_sessions(include_archived=True)
        archived_sessions = [s for s in all_sessions if s.get("archived", False)]

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
        """Start a new conversation."""
        new_id = self.agent.new_session()
        self.current_session_id = new_id
        self.chat_title.configure(text="💬 New Conversation")
        self._clear_chat_area()
        self._refresh_sidebar()
        self.input_text.focus()
        self._set_status("✅ New conversation started", COLORS["success"])

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

    def _send_message(self):
        """Send the current input as a message."""
        content = self.input_text.get("1.0", "end-1c").strip()
        if not content or self.is_streaming:
            return

        # Clear input
        self.input_text.delete("1.0", "end")

        # Handle commands
        if content.startswith("/"):
            self._handle_command(content)
            return

        # Create user message
        user_msg = ChatMessage("user", content)
        self._ensure_session_loaded()
        self.messages.setdefault(self.current_session_id, []).append(user_msg)
        self._display_message(user_msg)
        self._scroll_to_bottom()

        # Update sidebar with new preview
        self._refresh_sidebar()

        # Start streaming AI response
        self._start_streaming(content)

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
