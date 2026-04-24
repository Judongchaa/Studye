# Studye Frontend Documentation

The frontend of Studye is built using the **Textual** TUI (Terminal User Interface) framework for Python. It provides a responsive, keyboard-driven interface for managing study sessions.

## UI Architecture

The frontend is organized into several modules for better maintainability:

1.  **`frontend/app.py`**: The main application controller.
2.  **`frontend/widgets.py`**: Custom TUI widgets and components.
3.  **`frontend/modals.py`**: Modal screens for user interaction.
4.  **`frontend/styles.tcss`**: Externalized styling (CSS-like) for the interface.

## UI Components

### 1. `StudyeApp` (`frontend/app.py`)
The central controller that manages the UI state and orchestrates communication between the backend and the interface.
- **Key Bindings**:
  - `q`: Quit
  - `n`: New Session
  - `f`: New Folder
  - `t`: Temporary Chat
  - `a`: Attach File
  - `p`: Select Preset
- **Styling**: Loads styles from `frontend/styles.tcss`.

### 2. Custom Widgets (`frontend/widgets.py`)
- **`SessionDirectoryTree`**: A customized directory tree that identifies session directories (marked with 💬). It extends `FilteredDirectoryTree` and implements node-level caching for session status to ensure high-performance rendering during scrolling.
- **`ChatMessage`**: An optimized widget for displaying individual messages. It uses `Static` with `RichMarkdown` for faster rendering compared to the standard `Markdown` widget.
- **`FilteredDirectoryTree`**: Base class for trees that filters hidden files and system markers using a single-pass filtering algorithm for better efficiency.

### 3. Modals (`frontend/modals.py`)
- **`FileSelectorModal`**: A system-wide file picker for selecting attachments.
- **`PresetSelectorModal`**: A list of pre-configured prompts for rapid interaction.

## State Management

The app uses Textual's **Reactive** properties to manage dynamic UI updates:
- `current_session`: Tracks the active path.
- `attached_file`: Stores the path of the file staged for the next message.
- `latest_response`: Holds the text of the most recent assistant answer or the content of a selected `.md` file, which is displayed in a dedicated "Latest Response" container.

## Concurrency

The application prioritizes a responsive UI by offloading all potentially blocking operations to background workers using Textual's `@work` decorator:
- **Chat Loading**: `load_chat_history` runs on the main thread but offloads the blocking filesystem I/O to a thread pool, ensuring the TUI never freezes during session selection.
- **Response Preview**: `update_latest_response_display` runs in a dedicated thread to load and parse markdown files.
- **LLM Generation**: Response generation is handled in an exclusive background thread.

This multi-threaded approach ensures smooth interaction even on hardware with power-saving constraints.
