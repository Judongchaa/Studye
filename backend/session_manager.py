import os

from .config import BASE_DIRECTORY
from .context_parser import _extract_interaction_number


def _ensure_base_directory():
    if not os.path.exists(BASE_DIRECTORY):
        os.makedirs(BASE_DIRECTORY)


def _is_session_dir(path):
    if not path or not os.path.isdir(path):
        return False
    marker_file = os.path.join(path, ".session")
    if os.path.isfile(marker_file):
        return True
    # legacy support: directories with interaction history are sessions
    try:
        for f in os.listdir(path):
            if f.endswith("_interaction.md"):
                return True
    except Exception:
        pass
    return False


def list_sessions():
    _ensure_base_directory()
    sessions = []
    for root, dirs, _ in os.walk(BASE_DIRECTORY):
        for d in dirs:
            abs_dir = os.path.join(root, d)
            rel_dir = os.path.relpath(abs_dir, BASE_DIRECTORY)
            if _is_session_dir(abs_dir):
                sessions.append(rel_dir)
    return sorted(sessions)


def create_session(name):
    _ensure_base_directory()
    safe_name = os.path.normpath(name).lstrip(os.sep)
    path = os.path.join(BASE_DIRECTORY, safe_name)
    # Protect against path traversal
    if not os.path.abspath(path).startswith(os.path.abspath(BASE_DIRECTORY)):
        raise ValueError("Invalid session name")
    os.makedirs(path, exist_ok=True)
    # mark directory as session (for folder/session differentiation)
    marker_file = os.path.join(path, ".session")
    with open(marker_file, "w", encoding="utf-8") as f:
        f.write("session")
    return path


def get_next_filename(session_path):
    md_files = [f for f in os.listdir(session_path) if f.endswith('.md')]
    numbers = []
    for file in md_files:
        full_path = os.path.join(session_path, file)
        number = _extract_interaction_number(full_path)
        if number is not None:
            numbers.append(number)

    next_num = max(numbers) + 1 if numbers else 1
    return f"{next_num:04d}_interaction.md"