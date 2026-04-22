import os
import re


def _extract_interaction_number(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
    except OSError:
        return None

    if first_line.startswith("Interaction:"):
        try:
            return int(first_line.split(":", 1)[1].strip())
        except ValueError:
            return None
    if first_line.startswith("Chat:"):
        try:
            return int(first_line.split(":", 1)[1].strip())
        except ValueError:
            return None
    return None


def load_context(session_path):
    """
    Load and parse all .md interaction files from a session directory.
    Uses regex to split files into User and Assistant messages, preserving 
    any internal Markdown headers (###) within the message content.
    """
    files = [f for f in os.listdir(session_path) if f.endswith(".md")]
    numbered_files = []
    for file in files:
        full_path = os.path.join(session_path, file)
        number = _extract_interaction_number(full_path)
        numbered_files.append(
            (number if number is not None else float("inf"), full_path)
        )

    # Ensure chronological order based on the 'Interaction: N' metadata
    numbered_files.sort(key=lambda x: (x[0], x[1]))

    messages = []
    for _, file_path in numbered_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue

        # Strip the metadata header (e.g., "Interaction: 1")
        lines = content.splitlines()
        if lines and (
            lines[0].startswith("Interaction:") or lines[0].startswith("Chat:")
        ):
            content_body = "\n".join(lines[1:]).strip()
        else:
            content_body = content

        # Use regex to split sections while keeping the role headers.
        # This prevents internal '### Header' markers from breaking the content.
        sections = re.split(r"(###\s+User\n|###\s+Assistant\n)", content_body)
        
        for i in range(1, len(sections), 2):
            header = sections[i].strip()
            # The content is in the next split element
            text = sections[i+1].strip() if i+1 < len(sections) else ""
            
            role = "user" if "User" in header else "assistant"
            messages.append({"role": role, "content": text})
            
    return messages
