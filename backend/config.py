import os
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional. Environment variables can still be set externally.
    pass

DEFAULT_BASE_DIRECTORY = "sessions"
DEFAULT_ATTACHMENT_ROOT = os.path.expanduser("~")

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(ROOT_DIR, "chat_config.json")

DEFAULT_CONFIG = {
    "base_directory": DEFAULT_BASE_DIRECTORY,
    "show_md_files": False,
    "model": {
        "think": "deepseek-reasoner",
        "chat": "deepseek-chat"
    },
    "attachment_root_directory": DEFAULT_ATTACHMENT_ROOT,
    "presets": [
        {
            "name": "Summarize",
            "prompt": "Summarize the following text in a concise manner."
        },
        {
            "name": "Explain Simply",
            "prompt": "Explain the following concept as if I were a five-year-old, using simple analogies."
        }
    ]
}

def save_config(config_data):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

base_directory = DEFAULT_BASE_DIRECTORY
attachment_root = DEFAULT_ATTACHMENT_ROOT
show_md_files = False
model = "deepseek-chat"
presets = []

if not os.path.exists(CONFIG_PATH):
    save_config(DEFAULT_CONFIG)

try:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            if isinstance(cfg, dict):
                base_directory = cfg.get("base_directory", base_directory)
                show_md_files = cfg.get("show_md_files", show_md_files)
                model = cfg.get("model", model)
                # Supporting both keys for backward compatibility or just fixing it
                attachment_root = cfg.get("attachment_root_directory", cfg.get("chat_attachment_root", attachment_root))
                presets = cfg.get("presets", presets)
except Exception:
    # Fallback to defaults on any error
    pass

# Allow environment var override
BASE_DIRECTORY = os.getenv("CHAT_BASE_DIRECTORY", base_directory)
SHOW_MD_FILES = os.getenv("CHAT_SHOW_MD_FILES", str(show_md_files)).lower() in ("true", "1", "yes")
MODEL = os.getenv("CHAT_MODEL", model)
ATTACHMENT_ROOT_DIRECTORY = os.getenv("CHAT_ATTACHMENT_ROOT", attachment_root)
PRESETS = presets
