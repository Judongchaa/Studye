from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    DirectoryTree,
    Static,
    Input,
    TextArea,
    Select,
    Button,
    Markdown,
    Label,
    LoadingIndicator,
    ListView,
    ListItem,
)
from textual.containers import Horizontal, Vertical, ScrollableContainer, Container
from textual.reactive import reactive
from textual import on, work
from textual.screen import ModalScreen
from textual.message import Message
from typing import Iterable
from rich.text import Text
import os
import sys
import datetime
from pathlib import Path
from dotenv import load_dotenv

from backend.config import (
    BASE_DIRECTORY,
    MODEL,
    SHOW_MD_FILES,
    SHOW_HIDDEN_FILES,
    ATTACHMENT_ROOT_DIRECTORY,
    PRESETS,
)
from backend.session_manager import (
    list_sessions,
    create_session,
    get_next_filename,
    _is_session_dir,
)
from backend.context_parser import load_context
from backend.attachment_handler import extract_text, inject_attachment
from backend.llm_engine import generate_response

load_dotenv()

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

class FileSelectorModal(ModalScreen[Path | None]):
    """A modal screen for selecting a file from the system."""

    _selected_path: Path | None = None

    def compose(self) -> ComposeResult:
        print("Composing FileSelectorModal")
        with Vertical(id="modal-container"):
            yield Label("SELECT FILE TO ATTACH", classes="modal-title")
            root_dir = os.path.expanduser(ATTACHMENT_ROOT_DIRECTORY)
            print(f"Root dir: {root_dir}")
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
                # We use index as ID because names might have spaces
                items.append(ListItem(Label(preset["name"]), id=f"preset-{index}"))

            yield ListView(*items, id="preset-list")

            with Horizontal(id="modal-buttons"):
                yield Button("Cancel", variant="error", id="btn-modal-cancel")

    @on(ListView.Selected)
    def handle_selection(self, event: ListView.Selected) -> None:
        # Extract index from ID "preset-N"
        try:
            index = int(event.item.id.split("-")[1])
            self.dismiss(PRESETS[index]["prompt"])
        except (ValueError, IndexError):
            self.dismiss(None)

    @on(Button.Pressed, "#btn-modal-cancel")
    def handle_cancel(self) -> None:
        self.dismiss(None)

class SessionDirectoryTree(FilteredDirectoryTree):
    def render_label(self, node, base_style, control_style):
        node_label = node.label.copy()
        node_label.stylize(base_style)

        if node.data.path.is_dir():
            if _is_session_dir(str(node.data.path)):
                return Text("💬 ") + node_label
            return Text("📁 ") + node_label
        return Text("📄 ") + node_label

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
        yield Markdown(self.content) # Modificato da Static a Markdown


class StudyeApp(App):
    CSS = """
    Screen {
        layers: sidebar main;
    }

    ChatMessage {
        height: auto;
        width: 100%;
        margin: 1 0;
        padding: 1;
        border: solid red;
        min-height: 1;

    }

    ChatMessage Static, ChatMessage Markdown {
        height: auto;
        width: 100%;
    }

    .message-user {
        background: $accent;
    }

    .message-assistant {
        background: $boost;
    }

    .message-role {
        text-style: bold;
        margin-bottom: 1;
        color: $secondary;
        width: 100%;
    }

    #sidebar {
        width: 35;
        height: 100%;
        dock: left;
        background: $panel;
        border-right: tall $primary;
    }

    #main {
        height: 100%;
    }

    #chat-container {
        height: 1fr;
        overflow-y: scroll;
        padding: 1;
    }

    #input-area {
        height: auto;
        padding: 1;
        background: $boost;
        border-top: tall $primary;
    }

    #attachment-info {
        color: $warning;
        margin-bottom: 0;
        height: 1;
    }

    #loading-indicator {
        height: 1;
        width: 100%;
        content-align: center middle;
        display: none;
    }

    #loading-indicator.visible {
        display: block;
    }

    #latest-response-container {
        height: 60%;
        border: thick $accent;
        padding: 0;
        background: $boost;
        display: none;
    }

    #latest-response-title {
        text-align: center;
        text-style: bold;
        background: $accent;
        color: $text;
        width: 100%;
        height: 1;
        dock: top;
    }

    #latest-response-content {
        height: auto;
        padding: 1 2;
    }

    #new-item-area {
        height: auto;
        padding: 1;
        background: $panel-lighten-1;
        display: none;
    }

    #new-item-area.visible {
        display: block;
    }

    .title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #sidebar-buttons {
        height: auto;
        layout: vertical;
    }
    
    #sidebar-buttons-row {
        height: auto;
        layout: horizontal;
    }
    
    .sidebar-btn {
        width: 1fr;
        margin: 0;
    }

    #model-select {
        width: 15;
    }

    #chat-input {
        height: 3;
        width: 1fr;
        border: none;
    }

    /* Modal Styles */
    FileSelectorModal {
        align: center middle;
    }

    #modal-container {
        width: 80%;
        height: 80%;
        background: $panel;
        border: thick $primary;
        padding: 1;
    }

    .modal-title {
        text-align: center;
        text-style: bold;
        width: 100%;
        background: $primary;
        margin-bottom: 1;
    }

    #modal-file-tree {
        height: 1fr;
        border: block $surface;
    }

    #modal-selected-path {
        background: $surface;
        padding: 0 1;
        margin: 1 0;
        border: block $primary;
    }

    #modal-buttons {
        height: auto;
        align: right middle;
        margin-top: 1;
    }

    #modal-buttons Button {
        margin-left: 1;
    }

    PresetSelectorModal {
        align: center middle;
    }

    #preset-list {
        height: 1fr;
        border: block $surface;
    }

    #preset-list > ListItem {
        padding: 0 1;
    }

    #preset-list > ListItem:hover {
        background: $accent;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("n", "toggle_new_session", "New Session"),
        ("f", "toggle_new_folder", "New Folder"),
        ("t", "temp_chat", "Temp Chat"),
        ("a", "attach_file", "Attach File"),
        ("p", "select_preset", "Presets"),
    ]

    # --- Reactive States ---
    # current_session: Path to the active chat session directory
    current_session = reactive(None)
    # attached_file: Path to a file staged for the next message
    attached_file = reactive(None)
    # latest_response: The raw string of the most recent LLM answer
    latest_response = reactive("")
    _mode = "session"

    def watch_latest_response(self, response: str) -> None:
        """
        Textual 'Watcher' that triggers UI updates whenever 'latest_response' changes.
        This allows the background worker to update the UI safely via call_from_thread.
        """
        try:
            container = self.query_one("#latest-response-container")
            if response:
                from rich.markdown import Markdown as RichMarkdown
                # We use a Static widget to render Rich's Markdown object
                self.query_one("#latest-response-content", Static).update(RichMarkdown(response))
                container.display = True
                # Automatically reset scroll position to the top for new responses
                container.scroll_home(animate=False)
            else:
                container.display = False
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("STUDYE SESSIONS", classes="title")
                with Vertical(id="new-item-area"):
                    yield Input(placeholder="New session name...", id="new-item-input")
                yield SessionDirectoryTree(BASE_DIRECTORY, id="session-tree")
                with Vertical(id="sidebar-buttons"):
                    with Horizontal(id="sidebar-buttons-row"):
                        yield Button(
                            "Session (N)",
                            id="btn-new-session",
                            variant="primary",
                            classes="sidebar-btn",
                        )
                        yield Button(
                            "Folder (F)",
                            id="btn-new-folder",
                            variant="default",
                            classes="sidebar-btn",
                        )
                    yield Button(
                        "Temp Chat (T)",
                        id="btn-temp-chat",
                        variant="warning",
                        classes="sidebar-btn",
                    )
            with Vertical(id="main"):
                with ScrollableContainer(id="latest-response-container"):
                    yield Label("LATEST ASSISTANT RESPONSE", id="latest-response-title")
                    yield Static("", id="latest-response-content")

                with ScrollableContainer(id="chat-container"):
                    yield Label(
                        "Welcome to Study Chat. Select a session to start.",
                        id="welcome-label",
                    )

                yield LoadingIndicator(id="loading-indicator")

                with Vertical(id="input-area"):
                    yield Label("", id="attachment-info")
                    with Horizontal():
                        model_options = []
                        if isinstance(MODEL, dict):
                            model_options = [(k, k) for k in MODEL.keys()]
                            default_model = list(MODEL.keys())[0]
                        else:
                            model_options = [(str(MODEL), str(MODEL))]
                            default_model = str(MODEL)

                        yield Select(
                            model_options,
                            id="model-select",
                            value=default_model,
                            allow_blank=False,
                        )
                        yield TextArea(id="chat-input")
                        yield Button("Send", id="btn-send", variant="success")
        yield Footer()

    async def on_directory_tree_directory_selected(
        self, event: FilteredDirectoryTree.DirectorySelected
    ) -> None:
        self.select_session(str(event.path))

    async def on_directory_tree_file_selected(
        self, event: FilteredDirectoryTree.FileSelected
    ) -> None:
        """Handle selection of a file in the directory tree."""
        path = str(event.path)
        parent_dir = os.path.dirname(path)
        
        if path.endswith(".md"):
            # If it's a markdown file, we want to preview it.
            if _is_session_dir(parent_dir):
                # If it's inside a session, we also select that session.
                self.select_session(parent_dir, selected_file=path)
            else:
                # If it's just a loose .md file, just show the preview.
                self.update_latest_response_display(parent_dir, selected_file=path)
                self.notify(f"Previewing: {os.path.basename(path)}")
        elif _is_session_dir(parent_dir):
            # For non-md files inside a session, just select the session.
            self.select_session(parent_dir)

    def select_session(self, path: str, selected_file: str = None) -> None:
        """
        Activates a session and optionally previews a specific file.
        
        Args:
            path: Path to the session directory.
            selected_file: Optional path to a specific .md file for immediate preview.
        """
        if _is_session_dir(path):
            # Only reload chat history if we are switching sessions
            if self.current_session != path:
                self.current_session = path
                self.run_worker(self.load_chat_history(path))
                self.query_one("#welcome-label").display = False
                self.notify(f"Session selected: {os.path.basename(path)}")
            
            # Show the preview (either the selected file or the latest interaction)
            self.update_latest_response_display(path, selected_file=selected_file)
            if selected_file:
                self.notify(f"Previewing: {os.path.basename(selected_file)}")

    def update_latest_response_display(self, session_path: str, selected_file: str = None) -> None:
        """
        Updates the 'Latest Assistant Response' panel.
        
        Args:
            session_path: Path to the current session or directory.
            selected_file: If provided, this file's content will be shown instead of the last response.
        """
        messages = load_context(session_path, selected_file=selected_file)
        if messages:
            # Try to find the last assistant message
            assistant_messages = [m for m in messages if m["role"] == "assistant"]
            if assistant_messages:
                self.latest_response = assistant_messages[-1]["content"]
            else:
                # If no assistant message, fallback to the last message (e.g. user message or raw md content)
                self.latest_response = messages[-1]["content"]
        else:
            self.latest_response = ""

    async def load_chat_history(self, session_path: str) -> None:
        self.log(f"Loading chat history from {session_path}")
        chat_container = self.query_one("#chat-container")
        
        # 1. Elimina i vecchi messaggi aspettando che il DOM si sia svuotato
        await chat_container.query(ChatMessage).remove()

        messages = load_context(session_path)
        
        # 2. Pre-costruisci tutti i widget in memoria
        widgets_to_mount = [ChatMessage(msg["role"], msg["content"]) for msg in messages]
        
        # 3. Montali tutti in blocco (evita il ricalcolo continuo del layout)
        if widgets_to_mount:
            await chat_container.mount_all(widgets_to_mount)

        chat_container.scroll_end(animate=False)

    def action_toggle_new_session(self) -> None:
        area = self.query_one("#new-item-area")
        inp = self.query_one("#new-item-input")
        if "visible" in area.classes and self._mode == "session":
            area.remove_class("visible")
        else:
            area.add_class("visible")
            inp.placeholder = "New session name..."
            inp.focus()
            self._mode = "session"

    def action_toggle_new_folder(self) -> None:
        area = self.query_one("#new-item-area")
        inp = self.query_one("#new-item-input")
        if "visible" in area.classes and self._mode == "folder":
            area.remove_class("visible")
        else:
            area.add_class("visible")
            inp.placeholder = "New folder name..."
            inp.focus()
            self._mode = "folder"

    @on(Input.Submitted, "#new-item-input")
    def handle_new_input_submit(self, event: Input.Submitted) -> None:
        name = event.value.strip()
        if name:
            try:
                tree = self.query_one("#session-tree")
                base = BASE_DIRECTORY
                if tree.cursor_node and tree.cursor_node.data.path.is_dir():
                    base = str(tree.cursor_node.data.path)

                target_path = os.path.join(base, name)

                if self._mode == "session":
                    rel_target = os.path.relpath(target_path, BASE_DIRECTORY)
                    create_session(rel_target)
                    self.notify(f"Session '{name}' created")
                    self.select_session(target_path)
                else:
                    os.makedirs(target_path, exist_ok=True)
                    self.notify(f"Folder '{name}' created")

                self.query_one("#session-tree").reload()
                self.query_one("#new-item-area").remove_class("visible")
                self.query_one("#new-item-input").value = ""
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")

    @on(TextArea.Changed, "#chat-input")
    def on_input_change(self, event: TextArea.Changed) -> None:
        """Adjust the height of the chat input based on its content."""
        lines = len(event.text_area.document.lines)
        new_height = min(max(lines + 2, 3), 10)
        event.text_area.styles.height = new_height

    async def on_key(self, event: Message) -> None:
        """Handle global keys for the app."""
        if isinstance(event, Message) and hasattr(event, "key"):
            if event.key == "enter" and self.focused and self.focused.id == "chat-input":
                # Check for shift key
                # Note: In some terminals/textual versions shift+enter is just enter
                # but we'll try to prevent default and send
                event.prevent_default()
                await self.handle_send()

    @on(Button.Pressed, "#btn-new-session")
    def on_btn_new_session(self) -> None:
        self.action_toggle_new_session()

    @on(Button.Pressed, "#btn-new-folder")
    def on_btn_new_folder(self) -> None:
        self.action_toggle_new_folder()

    @on(Button.Pressed, "#btn-temp-chat")
    def action_temp_chat(self) -> None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"tmp_{timestamp}"
        try:
            tmp_folder_path = os.path.join(BASE_DIRECTORY, "tmp")
            os.makedirs(tmp_folder_path, exist_ok=True)

            target_path = os.path.join(tmp_folder_path, name)
            rel_target = os.path.relpath(target_path, BASE_DIRECTORY)
            create_session(rel_target)

            self.query_one("#session-tree").reload()
            self.select_session(target_path)
        except Exception as e:
            self.notify(f"Error creating temp session: {e}", severity="error")

    @on(Button.Pressed, "#btn-send")
    async def handle_send(self) -> None:
        if not self.current_session:
            self.notify("Select a session first!", severity="error")
            return

        input_widget = self.query_one("#chat-input", TextArea)
        prompt = input_widget.text.strip()
        if not prompt:
            return

        model_key = self.query_one("#model-select").value
        actual_model = (
            MODEL.get(model_key, model_key) if isinstance(MODEL, dict) else MODEL
        )

        original_prompt = prompt

        if self.attached_file:
            try:
                text = extract_text(str(self.attached_file))
                prompt = inject_attachment(prompt, text)
                self.attached_file = None
                self.query_one("#attachment-info").update("")
            except Exception as e:
                self.notify(f"Error processing attachment: {e}", severity="error")
                return

        chat_container = self.query_one("#chat-container")
        await chat_container.mount(ChatMessage("user", original_prompt))
        chat_container.scroll_end()

        input_widget.load_text("")

        self.query_one("#loading-indicator").add_class("visible")
        self.generate_and_display_response(
            prompt, original_prompt, actual_model, self.current_session
        )

    @work(exclusive=True, thread=True)
    def generate_and_display_response(
        self, prompt: str, original_prompt: str, model: str, session_path: str
    ) -> None:
        messages = load_context(session_path)
        messages.append({"role": "user", "content": prompt})

        try:
            # 1. Genera la risposta dall'LLM
            response = generate_response(messages, model)
            
            # 2. Salva tutto nel nuovo file .md
            filename = get_next_filename(session_path)
            interaction_number = int(filename.split("_")[0]) if filename.split("_")[0].isdigit() else None
            filepath = os.path.join(session_path, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                if interaction_number is not None:
                    f.write(f"Interaction: {interaction_number}\n\n")
                for p in PRESETS:
                    if p["prompt"] in original_prompt:
                        original_prompt = p["name"]
                        break

                f.write(f"### User\n{original_prompt}\n\n### Assistant\n{response}\n")

            # 3. FIX: Richiama la UI per aggiornare SOLO il File Tree
            self.app.call_from_thread(self.on_response_saved, response)
            
        except Exception as e:
            self.app.call_from_thread(self.notify, f"LLM Error: {e}", severity="error")
        finally:
            self.app.call_from_thread(self.hide_loading)

        
    def on_response_saved(self, last_resp: str = None) -> None:
        """Metodo chiamato quando il file .md è stato scritto su disco."""
        
        try:
            tree = self.query_one("#session-tree")
            tree.reload()
            
            if last_resp:
                self.latest_response = last_resp
            elif self.current_session:
                self.update_latest_response_display(self.current_session)
        except Exception as e:
            self.log(f"Impossibile ricaricare il tree o aggiornare la risposta: {e}")

    def hide_loading(self) -> None:
        """Hide the loading indicator from the UI."""
        self.query_one("#loading-indicator").remove_class("visible")

    @work
    async def action_attach_file(self) -> None:
        """Open file picker and stage an attachment for the next message."""
        file_path = await self.push_screen_wait(FileSelectorModal())
        if file_path:
            self.attached_file = file_path
            self.query_one("#attachment-info").update(f"Attached: {file_path.name}")
            self.notify(f"Attached {file_path.name}")

    @work
    async def action_select_preset(self) -> None:
        """Open preset selection modal and load the prompt into the text area."""
        if not PRESETS:
            self.notify("No presets configured in chat_config.json", severity="warning")
            return

        preset_prompt = await self.push_screen_wait(PresetSelectorModal())
        if preset_prompt:
            input_widget = self.query_one("#chat-input", TextArea)
            input_widget.load_text(preset_prompt)
            input_widget.focus()



if __name__ == "__main__":
    app = StudyeApp()
    app.run()
