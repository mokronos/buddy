from pathlib import Path
from os import getenv


def buddy_data_dir() -> Path:
    """Return the base data directory for buddy.

    Respects the ``BUDDY_DATA_DIR`` override and the ``XDG_DATA_HOME``
    convention, falling back to ``~/.local/share/buddy``.
    """
    data_root = Path.home() / ".local" / "share"
    data_root = Path(_env("XDG_DATA_HOME", data_root))
    data_root = Path(_env("BUDDY_DATA_DIR", data_root / "buddy"))
    data_root.mkdir(parents=True, exist_ok=True)
    return data_root


def _env(name: str, default: Path) -> Path:
    value = getenv(name)
    return Path(value) if value else default
