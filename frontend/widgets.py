from textual.widgets import DirectoryTree, Static, Markdown
from textual.containers import Container, Vertical
from textual.app import ComposeResult
from typing import Iterable
from pathlib import Path
from rich.text import Text

from backend.config import SHOW_HIDDEN_FILES, SHOW_MD_FILES
from backend.session_manager import _is_session_dir

class FilteredDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [
            path for path in paths
            if (SHOW_HIDDEN_FILES or not path.name.startswith(".")) and
               (SHOW_MD_FILES or not path.name.endswith(".md"))
        ]

from rich.markdown import Markdown as RichMarkdown

class SessionDirectoryTree(FilteredDirectoryTree):
    def render_label(self, node, base_style, style):
        # Check if we've already determined this is a session directory
        is_session = getattr(node.data, "is_session", None)
        if is_session is None:
            # Only check if it's potentially a directory (has expansion toggle)
            if node._allow_expand:
                is_session = _is_session_dir(str(node.data.path))
            else:
                is_session = False
            # Cache the result on the DirEntry object to avoid future syscalls
            try:
                node.data.is_session = is_session
            except (AttributeError, TypeError):
                pass

        if is_session:
            # Replicate Textual's label rendering but with the session icon
            node_label = node._label.copy()
            node_label.stylize(style)
            
            if not self.is_mounted:
                return node_label
                
            prefix = ("💬 ", base_style)
            # Use cached style if possible to avoid component lookup
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--folder", partial=True)
            )
            return Text.assemble(prefix, node_label)
            
        return super().render_label(node, base_style, style)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [
            path for path in paths
            if (SHOW_HIDDEN_FILES or not path.name.startswith(".")) and
               (SHOW_MD_FILES or not path.name.endswith(".md")) and
               path.name != ".session"
        ]

class ChatMessage(Vertical):
    """A widget for displaying a single chat message."""

    def __init__(self, role: str, content: str):
        super().__init__(classes=f"message-{role}")
        self.role = role
        self.content = content

    def compose(self) -> ComposeResult:
        yield Static(f"[{self.role.upper()}]", classes="message-role")
        yield Static(RichMarkdown(self.content))
