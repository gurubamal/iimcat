#!/usr/bin/env python3
from __future__ import annotations

"""
Archive outputs/ files older than 24 hours into monthly zip files and delete originals once archived.

Usage:
  python archive_outputs.py            # default: 24 hours
  python archive_outputs.py --hours 12 # custom threshold
"""

import argparse
from orchestrator.archive import archive_old_outputs


def main() -> None:
    ap = argparse.ArgumentParser(description="Archive old outputs into monthly zips")
    ap.add_argument("--hours", type=int, default=24, help="Minimum age in hours to archive (default: 24)")
    args = ap.parse_args()
    archived, deleted = archive_old_outputs(min_age_hours=args.hours)
    print(f"Archived {archived} items; deleted {deleted} originals.")


if __name__ == "__main__":
    main()

