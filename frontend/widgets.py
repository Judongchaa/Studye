from textual.widgets import DirectoryTree, Static, Markdown
from textual.containers import Container, Vertical
from textual.app import ComposeResult
from typing import Iterable
from pathlib import Path
from rich.text import Text

from backend.config import SHOW_HIDDEN_FILES, SHOW_MD_FILES
from backend.session_manager import _is_session_dir

class FilteredDirectoryTree(DirectoryTree):
    def filter_hidden(self, paths: Iterable[Path]) -> Iterable[Path]:
        if SHOW_HIDDEN_FILES:
            return paths
        filtered = [path for path in paths if not path.name.startswith(".")]
        return filtered
    
    def filter_md_files(self, paths: Iterable[Path]) -> Iterable[Path]:
        if SHOW_MD_FILES:
            return paths
        filtered = [path for path in paths if not path.name.endswith(".md")]
        return filtered

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        paths = self.filter_hidden(paths)
        paths = self.filter_md_files(paths)
        return paths

class SessionDirectoryTree(FilteredDirectoryTree):
    def render_label(self, node, base_style, style):
        label = super().render_label(node, base_style, style)
        if node.data.path.is_dir() and _is_session_dir(str(node.data.path)):
            # Use the provided 'style' for the new icon to ensure highlighting works
            return Text("💬 ", style=style) + label[2:]
        return label

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        paths = super().filter_paths(paths)
        return [path for path in paths if path.name != ".session"]

class ChatMessage(Vertical):
    """A widget for displaying a single chat message."""

    def __init__(self, role: str, content: str):
        super().__init__(classes=f"message-{role}")
        self.role = role
        self.content = content

    def compose(self) -> ComposeResult:
        yield Static(f"[{self.role.upper()}]", classes="message-role")
        yield Markdown(self.content)
