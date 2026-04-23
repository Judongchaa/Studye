from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    Static,
    Input,
    TextArea,
    Select,
    Button,
    Label,
    LoadingIndicator,
)
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual import on, work
from textual.message import Message
import os
import datetime
from pathlib import Path
from dotenv import load_dotenv

from backend.config import (
    BASE_DIRECTORY,
    MODEL,
    PRESETS,
)
from backend.session_manager import (
    create_session,
    get_next_filename,
    _is_session_dir,
)
from backend.context_parser import load_context
from backend.attachment_handler import extract_text, inject_attachment
from backend.llm_engine import generate_response

from frontend.widgets import SessionDirectoryTree, ChatMessage, FilteredDirectoryTree
from frontend.modals import FileSelectorModal, PresetSelectorModal

load_dotenv()

class StudyeApp(App):
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("n", "toggle_new_session", "New Session"),
        ("f", "toggle_new_folder", "New Folder"),
        ("t", "temp_chat", "Temp Chat"),
        ("a", "attach_file", "Attach File"),
        ("p", "select_preset", "Presets"),
    ]

    # --- Reactive States ---
    current_session = reactive(None)
    attached_file = reactive(None)
    latest_response = reactive("")
    _mode = "session"

    def on_mount(self) -> None:
        self.query_one("#session-tree").focus()

    def watch_latest_response(self, response: str) -> None:
        try:
            container = self.query_one("#latest-response-container")
            if response:
                from rich.markdown import Markdown as RichMarkdown
                self.query_one("#latest-response-content", Static).update(RichMarkdown(response))
                container.display = True
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
                yield SessionDirectoryTree(
                    BASE_DIRECTORY, id="session-tree", classes="directory-tree"
                )
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
        path = str(event.path)
        parent_dir = os.path.dirname(path)
        
        if path.endswith(".md"):
            if _is_session_dir(parent_dir):
                self.select_session(parent_dir, selected_file=path)
            else:
                self.update_latest_response_display(parent_dir, selected_file=path)
                self.notify(f"Previewing: {os.path.basename(path)}")
        elif _is_session_dir(parent_dir):
            self.select_session(parent_dir)

    def select_session(self, path: str, selected_file: str = None) -> None:
        if _is_session_dir(path):
            if self.current_session != path:
                self.current_session = path
                self.run_worker(self.load_chat_history(path))
                self.query_one("#welcome-label").display = False
                self.notify(f"Session selected: {os.path.basename(path)}")
            
            self.update_latest_response_display(path, selected_file=selected_file)
            if selected_file:
                self.notify(f"Previewing: {os.path.basename(selected_file)}")

    def update_latest_response_display(self, session_path: str, selected_file: str = None) -> None:
        messages = load_context(session_path, selected_file=selected_file)
        if messages:
            assistant_messages = [m for m in messages if m["role"] == "assistant"]
            if assistant_messages:
                self.latest_response = assistant_messages[-1]["content"]
            else:
                self.latest_response = messages[-1]["content"]
        else:
            self.latest_response = ""

    async def load_chat_history(self, session_path: str) -> None:
        chat_container = self.query_one("#chat-container")
        await chat_container.query(ChatMessage).remove()
        messages = load_context(session_path)
        widgets_to_mount = [ChatMessage(msg["role"], msg["content"]) for msg in messages]
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
        lines = len(event.text_area.document.lines)
        new_height = min(max(lines + 2, 3), 10)
        event.text_area.styles.height = new_height

    async def on_key(self, event: Message) -> None:
        if isinstance(event, Message) and hasattr(event, "key"):
            if event.key == "enter" and self.focused and self.focused.id == "chat-input":
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
            response = generate_response(messages, model)
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

            self.app.call_from_thread(self.on_response_saved, response)
            
        except Exception as e:
            self.app.call_from_thread(self.notify, f"LLM Error: {e}", severity="error")
        finally:
            self.app.call_from_thread(self.hide_loading)

        
    def on_response_saved(self, last_resp: str = None) -> None:
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
        self.query_one("#loading-indicator").remove_class("visible")

    @work
    async def action_attach_file(self) -> None:
        file_path = await self.push_screen_wait(FileSelectorModal())
        if file_path:
            self.attached_file = file_path
            self.query_one("#attachment-info").update(f"Attached: {file_path.name}")
            self.notify(f"Attached {file_path.name}")

    @work
    async def action_select_preset(self) -> None:
        if not PRESETS:
            self.notify("No presets configured in chat_config.json", severity="warning")
            return

        preset_prompt = await self.push_screen_wait(PresetSelectorModal())
        if preset_prompt:
            input_widget = self.query_one("#chat-input", TextArea)
            input_widget.load_text(preset_prompt)
            input_widget.focus()
