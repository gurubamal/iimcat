#!/usr/bin/env python3
"""
Natural-language scan runner.

Examples:
  python smart_scan.py run scan
  python smart_scan.py load context and run scan
  python smart_scan.py load context and give me top picks
  python smart_scan.py

Understands intent and forwards to run_swing_paths.py with the right options,
favoring AI Path with self-learning by default.
"""

from __future__ import annotations

import os
import sys
import subprocess
from orchestrator.config import LEARNING_DIR
from orchestrator.priorities import ensure_core_priorities

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    phrase = " ".join(sys.argv[1:]).strip().lower()
    if not phrase:
        try:
            phrase = input("Command (e.g., 'load context and run scan'): ").strip().lower()
        except EOFError:
            phrase = "run scan"

    # Defaults
    path = "ai"
    auto_apply = False
    auto_screener = False
    top = "25"
    just_top = False
    show_menu = False
    show_context = False

    # Intent parsing
    if "full auto" in phrase or ("run" in phrase and "scan" in phrase and "context" in phrase):
        auto_apply = True
        auto_screener = True
    if "give me top picks" in phrase or "top picks" in phrase:
        just_top = True
        auto_screener = False
    if "script" in phrase:
        path = "script"
    if "menu" in phrase or phrase in ("run scan", "load context and run scan"):
        show_menu = True
    if "read context" in phrase or ("load context" in phrase and "run" not in phrase and "scan" not in phrase and "top" not in phrase):
        show_context = True
        show_menu = True

    # Optional: show latest learning context (read-only)
    if show_context:
        ctx = os.path.join(LEARNING_DIR, "learning_context.md")
        debate = os.path.join(LEARNING_DIR, "learning_debate.md")
        priorities = os.path.join(LEARNING_DIR, "core_priorities.md")
        print("\n=== Core Priorities ===")
        try:
            with open(priorities, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                print("".join(lines[-200:]))
        except Exception:
            print("(no core priorities yet)")
        print("\n=== Latest Learning Context (tail) ===")
        try:
            with open(ctx, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-40:]
                print("".join(lines))
        except Exception:
            print("(no learning_context.md yet)")
        print("\n=== Latest Debate & Recommendations (tail) ===")
        try:
            with open(debate, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-40:]
                print("".join(lines))
        except Exception:
            print("(no learning_debate.md yet)")

        # If the intent is context-only, exit without further actions or writes
        if (
            ("run" not in phrase)
            and ("scan" not in phrase)
            and ("top" not in phrase)
            and ("menu" not in phrase)
        ):
            return

    # For non-context-only runs, ensure core priorities exist before proceeding
    try:
        pr_path = ensure_core_priorities()
    except Exception:
        pr_path = None

    # Menu if requested or ambiguous
    if show_menu and not just_top:
        print("Options:\n  1) Run AI Path full auto\n  2) Run AI Path (apply config, no screener)\n  3) Run AI Path (dry run: no config apply, no screener)\n  4) Script Path (original rules)\n  5) Backfill learnings (7 days)\n  6) Archive old outputs (>24h) and clean")
        try:
            sel = input("Enter 1-4 [default 1]: ").strip()
        except EOFError:
            sel = "1"
        if sel == "2":
            path = "ai"; auto_apply = True; auto_screener = False
        elif sel == "3":
            path = "ai"; auto_apply = False; auto_screener = False
        elif sel == "4":
            path = "script"; auto_apply = False; auto_screener = False
        elif sel == "5":
            # Backfill mode
            cmd = [sys.executable, os.path.join(BASE_DIR, "backfill_learnings.py"), "--days", "7", "--top", "100", "--apply-config"]
            print(f"Launching: {' '.join(cmd)}")
            subprocess.run(cmd)
            print("\nDone. For summaries, open learning_context.md and learning_debate.md.")
            return
        elif sel == "6":
            cmd = [sys.executable, os.path.join(BASE_DIR, "archive_outputs.py")]
            print(f"Launching: {' '.join(cmd)}")
            subprocess.run(cmd)
            print("\nDone. See monthly zips under archives/YYYY-MM/ .")
            return
        else:
            path = "ai"; auto_apply = True; auto_screener = True

    # Build command
    # Default to fresh fetch for last 10 hours as requested
    cmd = [sys.executable, os.path.join(BASE_DIR, "run_swing_paths.py"), "--path", path, "--top", top, "--fresh", "--hours", "10"]
    if auto_apply:
        cmd.append("--auto-apply-config")
    if auto_screener:
        cmd.append("--auto-screener")

    print(f"Launching: {' '.join(cmd)}")
    proc = subprocess.run(cmd)
    print("\nDone. For detailed reasoning, open learning_debate.md (latest entry). For context updates, see learning_context.md.")


if __name__ == "__main__":
    # Ensure UTF-8 output
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    main()
