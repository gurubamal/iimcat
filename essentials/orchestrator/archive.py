from __future__ import annotations

import os
import time
import zipfile
from datetime import datetime
from typing import Iterable, List, Tuple

from orchestrator.config import OUTPUTS_DIR


ARCHIVES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "archives")


def _ensure_dir(p: str) -> None:
    try:
        os.makedirs(p, exist_ok=True)
    except Exception:
        pass


def _month_key(ts: float) -> Tuple[int, int]:
    dt = datetime.fromtimestamp(ts)
    return dt.year, dt.month


def _monthly_zip_path(year: int, month: int) -> str:
    _ensure_dir(ARCHIVES_DIR)
    sub = os.path.join(ARCHIVES_DIR, f"{year:04d}-{month:02d}")
    _ensure_dir(sub)
    return os.path.join(sub, f"outputs_{year:04d}_{month:02d}.zip")


def _iter_candidates(root: str, min_age_sec: int, suffixes: Iterable[str]) -> List[str]:
    out: List[str] = []
    now = time.time()
    if not os.path.isdir(root):
        return out
    for name in os.listdir(root):
        p = os.path.join(root, name)
        try:
            if not os.path.isfile(p):
                continue
            if not any(name.lower().endswith(s) for s in suffixes):
                continue
            age = now - os.path.getmtime(p)
            if age >= min_age_sec:
                out.append(p)
        except OSError:
            continue
    return out


def archive_old_outputs(min_age_hours: int = 24, include_suffixes: Iterable[str] = (".csv", ".txt", ".json", ".xlsx")) -> Tuple[int, int]:
    """
    Archive files in outputs/ older than min_age_hours into monthly zip files and
    delete originals after confirming inclusion. Returns (archived_count, deleted_count).
    """
    min_age_sec = int(min_age_hours * 3600)
    files = _iter_candidates(OUTPUTS_DIR, min_age_sec, include_suffixes)
    if not files:
        return 0, 0

    # Group by month of modification
    groups: dict[Tuple[int, int], List[str]] = {}
    for p in files:
        ts = os.path.getmtime(p)
        key = _month_key(ts)
        groups.setdefault(key, []).append(p)

    archived = 0
    deleted = 0

    for (year, month), paths in groups.items():
        zpath = _monthly_zip_path(year, month)
        # Build arcnames relative to outputs dir
        rels = [(p, os.path.relpath(p, OUTPUTS_DIR)) for p in paths]
        # Append to zip
        _ensure_dir(os.path.dirname(zpath))
        with zipfile.ZipFile(zpath, mode="a", compression=zipfile.ZIP_DEFLATED) as zf:
            existing = set(zf.namelist())
            for abspath, arcname in rels:
                if arcname in existing:
                    # Already archived; delete original and continue
                    try:
                        os.remove(abspath)
                        deleted += 1
                    except OSError:
                        pass
                    continue
                try:
                    zf.write(abspath, arcname)
                    archived += 1
                except Exception:
                    continue
        # After writing, verify and delete originals
        try:
            with zipfile.ZipFile(zpath, mode="r") as zf:
                present = set(zf.namelist())
            for abspath, arcname in rels:
                if arcname in present:
                    try:
                        os.remove(abspath)
                        deleted += 1
                    except OSError:
                        pass
        except Exception:
            # If we can't verify, do not delete
            pass

    return archived, deleted

