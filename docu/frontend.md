# Studye Frontend Documentation

The frontend of Studye is built using the **Textual** TUI (Terminal User Interface) framework for Python. It provides a responsive, keyboard-driven interface for managing study sessions.

## UI Architecture

The interface is divided into two main areas:
1.  **Sidebar**: Session management, folder navigation, and quick action buttons.
2.  **Main Area**: Chat history display, model selection, and the message input area.

## Components

### 1. `StudyeApp` (Main Application)
The central controller that manages the UI state and orchestrates communication between the backend and the interface.
- **Key Bindings**:
  - `q`: Quit
  - `n`: New Session
  - `f`: New Folder
  - `t`: Temporary Chat
  - `a`: Attach File
  - `p`: Select Preset
  - `c`: Clear/Refresh Chat

### 2. `SessionDirectoryTree`
A customized directory tree that identifies session directories (marked with 💬) versus regular folders (📁).

### 3. `ChatMessage`
A custom widget for displaying individual messages. It uses the `Markdown` widget to render rich text, including code blocks and formatting.

### 4. Modals
- **`FileSelectorModal`**: A system-wide file picker for selecting attachments.
- **`PresetSelectorModal`**: A list of pre-configured prompts for rapid interaction.

## State Management

The app uses Textual's **Reactive** properties to manage dynamic UI updates:
- `current_session`: Tracks the active path.
- `attached_file`: Stores the path of the file staged for the next message.
- `latest_response`: Holds the text of the most recent assistant answer, which is also displayed in a dedicated "Latest Response" container.

## Concurrency

Long-running tasks like LLM response generation are handled using Textual's `@work` decorator and background threads. This ensures the UI remains responsive (animations and input don't freeze) while waiting for the API.

## Styling

The UI is styled using CSS-like syntax within the `StudyeApp` class, defining colors, borders, and layout behaviors for various terminal themes.
 stone colors.
