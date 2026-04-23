from textual.screen import ModalScreen
from textual.widgets import Label, Button, ListView, ListItem
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from textual import on
from pathlib import Path
import os

from frontend.widgets import FilteredDirectoryTree
from backend.config import ATTACHMENT_ROOT_DIRECTORY, PRESETS

class FileSelectorModal(ModalScreen[Path | None]):
    """A modal screen for selecting a file from the system."""

    _selected_path: Path | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label("SELECT FILE TO ATTACH", classes="modal-title")
            root_dir = os.path.expanduser(ATTACHMENT_ROOT_DIRECTORY)
            yield FilteredDirectoryTree(root_dir, id="modal-file-tree")
            yield Label("No file selected", id="modal-selected-path")
            with Horizontal(id="modal-buttons"):
                yield Button("Select", variant="success", id="btn-modal-select")
                yield Button("Cancel", variant="error", id="btn-modal-cancel")

    @on(FilteredDirectoryTree.FileSelected)
    def handle_file_selection(self, event: FilteredDirectoryTree.FileSelected) -> None:
        self._selected_path = event.path
        self.query_one("#modal-selected-path").update(
            f"Selected: [bold]{event.path}[/bold]"
        )

    @on(Button.Pressed, "#btn-modal-select")
    def handle_select(self) -> None:
        if self._selected_path:
            self.dismiss(self._selected_path)
        else:
            self.app.notify("No file selected!", severity="warning")

    @on(Button.Pressed, "#btn-modal-cancel")
    def handle_cancel(self) -> None:
        self.dismiss(None)

class PresetSelectorModal(ModalScreen[str | None]):
    """A modal screen for selecting a preset prompt."""

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label("SELECT PRESET PROMPT", classes="modal-title")
            items = []
            for index, preset in enumerate(PRESETS):
                items.append(ListItem(Label(preset["name"]), id=f"preset-{index}"))

            yield ListView(*items, id="preset-list")

            with Horizontal(id="modal-buttons"):
                yield Button("Cancel", variant="error", id="btn-modal-cancel")

    @on(ListView.Selected)
    def handle_selection(self, event: ListView.Selected) -> None:
        try:
            index = int(event.item.id.split("-")[1])
            self.dismiss(PRESETS[index]["prompt"])
        except (ValueError, IndexError):
            self.dismiss(None)

    @on(Button.Pressed, "#btn-modal-cancel")
    def handle_cancel(self) -> None:
        self.dismiss(None)
