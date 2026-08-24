from __future__ import annotations

import json
from pathlib import Path

from .model import Diagram


def load_diagram(path: str | Path) -> Diagram:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return Diagram.from_dict(data)


def save_diagram(diagram: Diagram, path: str | Path) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(diagram.to_dict(), handle, indent=2, ensure_ascii=False)
