# Studye Backend Documentation

The backend of Studye is a collection of Python modules that handle configuration, data persistence, LLM communication, and document processing.

## Modules

### 1. `config.py`
Manages application-wide settings and environment variables.
- **Auto-generation**: If `chat_config.json` is missing, it creates a default one.
- **Settings**:
  - `BASE_DIRECTORY`: Root folder for storing chat sessions.
  - `MODEL`: Configuration for LLM models (supports both single model strings and dictionaries for different tasks).
  - `ATTACHMENT_ROOT_DIRECTORY`: Default starting path for the file picker.
  - `PRESETS`: A list of pre-defined prompts for quick access.
- **Environment Overrides**: Supports `.env` files and system environment variables (e.g., `CHAT_BASE_DIRECTORY`, `OPEN_AI_API_KEY`).

### 2. `session_manager.py`
Handles the filesystem structure for chats.
- **Session Structure**: A session is a directory containing a `.session` marker file and multiple `.md` files (interactions).
- **Functions**:
  - `list_sessions()`: Recursively finds all session directories.
  - `create_session(name)`: Creates a new session directory with the required marker.
  - `get_next_filename(session_path)`: Determines the filename for the next interaction (e.g., `0001_interaction.md`).

### 3. `context_parser.py`
Responsible for reading session data and converting it into a format suitable for the LLM.
- **Parsing**: Reads `.md` files, extracts interaction numbers for sorting, and uses regex to separate "User" and "Assistant" blocks.
- **Chronology**: Ensures messages are ordered correctly based on the `Interaction: N` metadata.

### 4. `attachment_handler.py`
Handles document processing for context injection.
- **Extraction**: Supports `.txt`, `.py`, `.pdf` (via `PyPDF2`), and `.docx` (via `python-docx`).
- **Injection**: Wraps extracted text in `<document>` tags to be appended to the LLM prompt.

### 5. `llm_engine.py`
The interface to the Large Language Model.
- **Provider**: Currently configured for OpenAI-compatible APIs (defaulting to DeepSeek).
- **Mocking**: Can be set to mock responses via the `MOCK_LLM=1` environment variable for UI testing.

## Data Storage
Studye uses a file-based storage system. Every interaction is saved as an individual Markdown file within the session folder. This allows for easy manual inspection and portability of data.
