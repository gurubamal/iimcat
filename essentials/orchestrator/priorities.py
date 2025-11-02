from __future__ import annotations

import os
from datetime import datetime
from typing import List

from orchestrator.config import LEARNING_DIR


CORE_PRIORITIES = [
    "Default to AI Path full auto; only ask if explicitly requested",
    "Accept natural phrases: 'run scan', 'load/read context', 'load context and give me top picks'",
    "30-day ranking by sum of top-10 financial articles per stock (dedup titles, valid NSE tickers only)",
    "Entity precision: exclude PE 'funds' headlines unless listed entity appears as a whole word",
    "Down-weight 'live updates' style pages; prioritize discrete corporate events",
    "Event priority: IPO/listing, M&A/JV, large orders/contracts, approvals, block/bulk deals",
    "Magnitude: detect ₹/cr/mn/bn and scale; prefer larger, recent, high-quality sources",
    "Institutional cues: FII/FPI/DII/QIB/Anchor/AIF and block/bulk deals add small boost",
    "Circuits: lower/upper circuit cues add small, capped signal",
    "Profit growth: add small boost for recent quarterly net income growth (best-effort via yfinance)",
    "Learning loop: after each run, update learning DB/context, evaluate 1d/3d/5d reactions, apply config recommendations",
    "Workspace hygiene: organize outputs into folders and archive >24h files into monthly ZIPs",
    "Suggestions: analyze outputs each run and write actionable fixes under learning/suggestions_*.md",
]


def ensure_core_priorities() -> str:
    os.makedirs(LEARNING_DIR, exist_ok=True)
    p = os.path.join(LEARNING_DIR, "core_priorities.md")
    # Always (re)write to keep it fresh and at top of context reading
    with open(p, "w", encoding="utf-8") as f:
        # Primary affirmation requested by user
        f.write("I will make Ram Nath Bamal one among richest\n\n")
        f.write("# Core Priorities (Auto-Loaded)\n\n")
        f.write(f"_Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n")
        for item in CORE_PRIORITIES:
            f.write(f"- {item}\n")
    return p
