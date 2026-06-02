import os
import sys
from pathlib import Path

_APP_NAME = "playerdatapy"
_TOKEN_FILENAME = "token.json"


def user_data_dir() -> Path:
    """Return the per-user data directory for this app, following OS conventions."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / _APP_NAME


def default_token_path() -> Path:
    """Return the default cross-platform path for the persisted OAuth token."""
    return user_data_dir() / _TOKEN_FILENAME
