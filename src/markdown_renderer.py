"""
📝 Markdown renderer for tkinter Text widgets.
Converts markdown text into visually formatted rich text.
"""

import re
import tkinter as tk
from tkinter import font as tkfont
from typing import Optional


# ── Tag Configuration ───────────────────────────────────────────

TAG_CONFIGS = {
    "bold": {
        "font_weight": "bold",
    },
    "italic": {
        "font_slant": "italic",
    },
    "bold_italic": {
        "font_weight": "bold",
        "font_slant": "italic",
    },
    "code": {
        "font_family": "Consolas",
        "font_size": 11,
        "background": "#f0f0f0",
        "foreground": "#333333",
        "spacing1": 1,
        "spacing3": 1,
        "lmargin1": 4,
        "lmargin2": 4,
    },
    "code_block": {
        "font_family": "Consolas",
        "font_size": 11,
        "background": "#f5f5f5",
        "foreground": "#222222",
        "spacing1": 4,
        "spacing3": 4,
        "lmargin1": 12,
        "lmargin2": 12,
        "rmargin": 12,
    },
    "heading1": {
        "font_size": 18,
        "font_weight": "bold",
        "foreground": "#000000",
        "spacing1": 8,
        "spacing3": 4,
    },
    "heading2": {
        "font_size": 15,
        "font_weight": "bold",
        "foreground": "#222222",
        "spacing1": 6,
        "spacing3": 3,
    },
    "heading3": {
        "font_size": 13,
        "font_weight": "bold",
        "foreground": "#444444",
        "spacing1": 4,
        "spacing3": 2,
    },
    "bullet": {
        "lmargin1": 16,
        "lmargin2": 20,
    },
    "numbered": {
        "lmargin1": 16,
        "lmargin2": 24,
    },
    "link": {
        "foreground": "#333333",
        "underline": True,
    },
    "blockquote": {
        "foreground": "#666666",
        "font_slant": "italic",
        "lmargin1": 20,
        "lmargin2": 20,
        "rmargin": 8,
        "spacing1": 2,
        "spacing3": 2,
    },
    "hr": {
        "foreground": "#bbbbbb",
        "spacing1": 6,
        "spacing3": 6,
    },
}

# Font sizing (scaled relative to base)
BASE_SIZE = 13
SIZE_SCALE = {
    "heading1": int(BASE_SIZE * 1.4),
    "heading2": int(BASE_SIZE * 1.15),
    "heading3": BASE_SIZE,
    "code": BASE_SIZE - 2,
    "code_block": BASE_SIZE - 2,
}


class MarkdownRenderer:
    """Renders markdown text into a tkinter Text widget with visual formatting."""

    def __init__(self, text_widget: tk.Text, base_font_size: int = 13):
        self.text = text_widget
        self.base_size = base_font_size
        self._configure_tags()

    def _configure_tags(self):
        """Set up all text tags with their visual properties."""
        for tag_name, config in TAG_CONFIGS.items():
            resolved = {}
            for key, value in config.items():
                if key == "font_size":
                    resolved["font"] = self._make_font(size=value)
                elif key == "font_weight":
                    resolved["font"] = self._make_font(weight=value)
                elif key == "font_slant":
                    resolved["font"] = self._make_font(slant=value)
                elif key == "font_family":
                    resolved["font"] = self._make_font(family=value)
                elif key == "foreground":
                    resolved["foreground"] = value
                elif key == "background":
                    resolved["background"] = value
                elif key == "underline":
                    resolved["underline"] = value
                elif key in ("spacing1", "spacing3", "lmargin1", "lmargin2", "rmargin"):
                    resolved[key] = int(value)
            self.text.tag_configure(tag_name, **resolved)

        # Link binding
        self.text.tag_bind("link", "<Button-1>", self._on_link_click)
        self.text.tag_bind("link", "<Enter>", lambda e: self.text.configure(cursor="hand2"))
        self.text.tag_bind("link", "<Leave>", lambda e: self.text.configure(cursor=""))

    def _make_font(self, family: str = "Segoe UI", size: int = None,
                   weight: str = "normal", slant: str = "roman"):
        """Create or retrieve a tkinter Font object."""
        if size is None:
            size = self.base_size
        font_name = f"md_font_{family}_{size}_{weight}_{slant}"
        try:
            return tkfont.Font(name=font_name, exists=font_name)
        except:
            return tkfont.Font(
                family=family,
                size=size,
                weight=weight,
                slant=slant,
            )

    # ══════════════════════════════════════════════════════════════
    #  Main Rendering API
    # ══════════════════════════════════════════════════════════════

    def render(self, markdown_text: str):
        """Clear the widget and render markdown content."""
        self.text.delete("1.0", "end")
        if not markdown_text.strip():
            return
        self._render_blocks(markdown_text)

    def append_streaming(self, text: str):
        """Append raw text during streaming (no formatting for speed)."""
        self.text.insert("end", text)
        self.text.see("end")

    def replace_content(self, markdown_text: str):
        """Replace all content with fully rendered markdown (for stream completion)."""
        self.render(markdown_text)

    # ══════════════════════════════════════════════════════════════
    #  Block-Level Parsing
    # ══════════════════════════════════════════════════════════════

    def _render_blocks(self, text: str):
        """Parse and render block-level elements."""
        lines = text.split("\n")
        i = 0
        in_code_block = False
        code_block_lines = []
        in_list = False
        list_type = None  # 'bullet' or 'numbered'

        while i < len(lines):
            line = lines[i]

            # ── Code block ──────────────────────────────────
            if line.strip().startswith("```"):
                if in_code_block:
                    # End code block
                    code_text = "\n".join(code_block_lines)
                    self._insert_code_block(code_text)
                    code_block_lines = []
                    in_code_block = False
                else:
                    # Start code block
                    in_code_block = True
                    code_block_lines = []
                i += 1
                continue

            if in_code_block:
                code_block_lines.append(line)
                i += 1
                continue

            # ── Horizontal rule ──────────────────────────────
            if re.match(r"^[-*_]{3,}\s*$", line.strip()):
                self._insert_hr()
                in_list = False
                i += 1
                continue

            # ── Heading ─────────────────────────────────────
            heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                content = heading_match.group(2)
                self._insert_heading(content, level)
                in_list = False
                i += 1
                continue

            # ── Blockquote ──────────────────────────────────
            if line.strip().startswith(">"):
                quote_text = line.strip()[1:].strip()
                self._insert_blockquote(quote_text)
                in_list = False
                i += 1
                continue

            # ── List item ───────────────────────────────────
            bullet_match = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
            numbered_match = re.match(r"^(\s*)\d+\.\s+(.+)$", line)

            if bullet_match:
                indent = len(bullet_match.group(1))
                content = bullet_match.group(2)
                self._insert_list_item(content, "bullet", indent)
                in_list = True
                list_type = "bullet"
                i += 1
                continue

            if numbered_match:
                indent = len(numbered_match.group(1))
                content = numbered_match.group(2)
                self._insert_list_item(content, "numbered", indent)
                in_list = True
                list_type = "numbered"
                i += 1
                continue

            # If we were in a list and hit a non-list line, reset
            if in_list and line.strip() == "":
                in_list = False
                list_type = None
                # Add minimal spacing
                self.text.insert("end", "\n", ())
                i += 1
                continue
            elif in_list and line.strip():
                in_list = False

            # ── Regular paragraph ───────────────────────────
            if line.strip() == "":
                # Empty line = paragraph break
                self.text.insert("end", "\n", ())
                i += 1
                continue

            # Regular text line
            self._insert_paragraph(line)
            i += 1

        # Close any open code block
        if in_code_block and code_block_lines:
            self._insert_code_block("\n".join(code_block_lines))

    # ══════════════════════════════════════════════════════════════
    #  Block Insertion Methods
    # ══════════════════════════════════════════════════════════════

    def _insert_code_block(self, code: str):
        """Insert a fenced code block."""
        if self.text.index("end-1c") != "1.0":
            self.text.insert("end", "\n", ())
        # Add a background frame effect by inserting with code_block tag
        lines = code.rstrip("\n").split("\n")
        for j, cl in enumerate(lines):
            prefix = "  "  # slight indent
            self.text.insert("end", prefix + cl + "\n", "code_block")
        self.text.insert("end", "\n", ())

    def _insert_hr(self):
        """Insert a horizontal rule."""
        if self.text.index("end-1c") != "1.0":
            self.text.insert("end", "\n", ())
        width = 50
        self.text.insert("end", "─" * width + "\n", "hr")
        self.text.insert("end", "\n", ())

    def _insert_heading(self, text: str, level: int):
        """Insert a heading with appropriate size."""
        tag = f"heading{level}"
        if self.text.index("end-1c") != "1.0":
            self.text.insert("end", "\n", ())
        self._insert_inline(text + "\n", tag)

    def _insert_blockquote(self, text: str):
        """Insert a blockquote."""
        self._insert_inline("┃ " + text + "\n", "blockquote")

    def _insert_list_item(self, text: str, list_type: str, indent: int = 0):
        """Insert a list item with bullet or number."""
        tag = list_type
        prefix = "  " * indent
        marker = "•" if list_type == "bullet" else "1."
        self._insert_inline(prefix + marker + " " + text + "\n", tag)

    def _insert_paragraph(self, text: str):
        """Insert a paragraph with inline formatting."""
        if text.strip():
            self._insert_inline(text + "\n", ())

    # ══════════════════════════════════════════════════════════════
    #  Inline Formatting
    # ══════════════════════════════════════════════════════════════

    def _insert_inline(self, text: str, base_tag):
        """Parse inline formatting using iterative regex matching, applying base_tag + inline tags."""
        pos = 0
        pattern = re.compile(
            r"\*\*(.+?)\*\*"        # **bold**
            r"|__(.+?)__"           # __bold__
            r"|\*(.+?)\*"           # *italic*
            r"|_(.+?)_"             # _italic_
            r"|`(.+?)`"             # `code`
            r"|\[(.+?)\]\((.+?)\)"  # [link](url]
        )

        # Convert base_tag to a tuple of tag names (ensuring no empty/None values)
        def _tags(*extra):
            """Build a tuple of tag names, filtering out empty/None."""
            result = []
            if base_tag and base_tag != ():
                if isinstance(base_tag, str):
                    result.append(base_tag)
                else:
                    result.extend(t for t in base_tag if t)
            for t in extra:
                if t:
                    result.append(t)
            return tuple(result) if result else ()

        while pos < len(text):
            match = pattern.search(text, pos)
            if not match:
                self.text.insert("end", text[pos:], _tags())
                break

            # Plain text before match
            if match.start() > pos:
                self.text.insert("end", text[pos:match.start()], _tags())

            # Determine which group matched
            if match.group(1):   # **bold**
                self.text.insert("end", match.group(1), _tags("bold"))
            elif match.group(2): # __bold__
                self.text.insert("end", match.group(2), _tags("bold"))
            elif match.group(3): # *italic*
                self.text.insert("end", match.group(3), _tags("italic"))
            elif match.group(4): # _italic_
                self.text.insert("end", match.group(4), _tags("italic"))
            elif match.group(5): # `code`
                self.text.insert("end", match.group(5), _tags("code"))
            elif match.group(6): # [link](url)
                link_text = match.group(6)
                link_url = match.group(7)
                tag_start = self.text.index("end-1c")
                self.text.insert("end", link_text, _tags("link"))
                tag_end = self.text.index("end-1c")
                # Bind click to open URL
                link_tag = f"link_{abs(hash(link_url))}"
                self.text.tag_add(link_tag, tag_start, tag_end)
                self.text.tag_bind(link_tag, "<Button-1>",
                                   lambda e, url=link_url: self._open_url(url))

            pos = match.end()

    # ══════════════════════════════════════════════════════════════
    #  Link Handling
    # ══════════════════════════════════════════════════════════════

    def _on_link_click(self, event):
        """Handle click on a link tag."""
        # We use individual tags per link, so this is fallback
        pass

    def _open_url(self, url: str):
        """Open a URL in the default browser."""
        import webbrowser
        webbrowser.open(url)
