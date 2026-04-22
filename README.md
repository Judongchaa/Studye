# Studye

**⚠️ WARNING: Personal Use Only - Experimental Software ⚠️**

This is a personal study-facilitation application designed and vibecoded for my own workflow. It is highly experimental, contains **tons of bugs, problems, and unfinished features**. Use it at your own risk. This project is not intended for production use or as a polished consumer product.

## Overview

Studye is a TUI (Terminal User Interface) application built with Python and Textual, designed to help organize study sessions and interact with LLMs (specifically DeepSeek/OpenAI) using local documents as context.

### Key Features
- **Session-Based Organization**: Group your learning by topics or sessions.
- **Document Context**: Attach `.txt`, `.py`, `.pdf`, or `.docx` files to your queries.
- **Preset Prompts**: Quickly apply complex pedagogical instructions.
- **Markdown-First**: All interactions are stored as standard Markdown files.
- **Dual Display**: View the full chat history or focus on the latest response.

## Installation

1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your environment variables in a `.env` file:
   ```env
   OPEN_AI_API_KEY=your_key_here
   ```

## Configuration

The application uses a `chat_config.json` file for settings. If it doesn't exist, it will be automatically generated on first run. You can customize:
- `base_directory`: Where sessions are stored.
- `attachment_root_directory`: Default folder for the file picker.
- `model`: The LLM model to use.
- `presets`: Your custom prompt library.

## Usage

Run the application:
```bash
python main.py
```

### Shortcuts
- `n`: Create a new session.
- `a`: Attach a file to the current prompt.
- `p`: Open the preset selector.
- `Enter`: Send message (within the text area).
- `q`: Quit.

## Known Issues 
- File paths with spaces might cause issues in some components.
- Large PDF extraction can be slow and might block the UI occasionally.
- Layout may break on very small terminal windows.
- The session tree doesn't always refresh perfectly after folder deletion (which currently must be done manually).
- **And many more...**

## License
Do whatever you want
