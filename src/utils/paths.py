from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", project_root()))
    else:
        base = project_root()
    return base.joinpath(*parts)


def data_dir() -> Path:
    if getattr(sys, "frozen", False):
        path = Path.home() / ".tour_agency_ais"
    else:
        path = project_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path
