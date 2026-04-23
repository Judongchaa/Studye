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
- **`SessionDirectoryTree`**: A customized directory tree that identifies session directories (marked with 💬). It extends `FilteredDirectoryTree` and overrides `render_label` to inject session icons while preserving standard Textual highlighting and selection styles.
- **`ChatMessage`**: A custom widget for displaying individual messages using Markdown rendering.
- **`FilteredDirectoryTree`**: Base class for trees that filters hidden files and system markers.

### 3. Modals (`frontend/modals.py`)
- **`FileSelectorModal`**: A system-wide file picker for selecting attachments.
- **`PresetSelectorModal`**: A list of pre-configured prompts for rapid interaction.

## State Management

The app uses Textual's **Reactive** properties to manage dynamic UI updates:
- `current_session`: Tracks the active path.
- `attached_file`: Stores the path of the file staged for the next message.
- `latest_response`: Holds the text of the most recent assistant answer or the content of a selected `.md` file, which is displayed in a dedicated "Latest Response" container.

## Concurrency

Long-running tasks like LLM response generation are handled using Textual's `@work` decorator and background threads. This ensures the UI remains responsive while waiting for the API.
