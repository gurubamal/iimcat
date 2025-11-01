# Real-time AI: Codex Shell Bridge (No API Keys)

This document explains how to run Stage 2 with “Codex” without using external API keys by routing prompts to a local shell bridge.

## Overview

- Two-stage flow (used by `run_realtime_ai_scan.sh`):
  - Stage 1: Heuristic-only scan over tickers (fast shortlist, zero API usage).
  - Stage 2: External AI on the shortlist. With this bridge, Stage 2 works without API keys.
- Default tickers: `nifty50_tickers.txt` (override by passing a file path as the first arg).

## Prerequisites

- Python 3 available in PATH.
- This repo checked out with the provided scripts.

## Setup (Shell Bridge)

1) Use the included bridge script:

```bash
cd /home/vagrant/R/essentials
chmod +x codex_bridge.py
```

2) Export environment variables to activate the bridge:

```bash
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 codex_bridge.py"
```

Optional custom guidance (the bridge will include this in its internal reasoning pipeline):

```bash
export AI_SHELL_INSTRUCTION="Assess quarterly profit growth, magnitude vs capacity, 1-2 day volume rise, buyer dominance, etc."
```

## Run Examples

Top‑10 NIFTY scan (48h window):

```bash
./run_realtime_ai_scan.sh nifty50_tickers.txt 48
```

Focus on any 10 specific NIFTY tickers:

```bash
cat > top10_nifty.txt <<'EOF'
RELIANCE
TCS
HDFCBANK
ICICIBANK
INFY
ITC
SBIN
BHARTIARTL
MARUTI
WIPRO
EOF

TOP_FOCUS=10 AI_MAX_CALLS=30 MAX_ARTICLES_STAGE2=2 ./run_realtime_ai_scan.sh top10_nifty.txt 48
```

## Tuning (Env Vars)

- `TOP_FOCUS` — number of tickers to refine with external AI in Stage 2 (default: 15)
- `MAX_ARTICLES_STAGE1` — heuristic pass articles per ticker (default: 10)
- `MAX_ARTICLES_STAGE2` — Stage 2 articles per ticker (default: 3)
- `AI_MAX_CALLS` — hard cap on external AI calls before auto‑fallback to heuristics (default: 60)
- `AI_PROVIDER` — `codex` to use the bridge, `heuristic` to force heuristics, `auto` to auto‑select
- `CODEX_SHELL_CMD` — command to execute; must read prompt on stdin and print JSON on stdout
- `AI_SHELL_INSTRUCTION` — optional free‑form guidance for the bridge

## Outputs

- Results CSV: `realtime_ai_analysis_*.csv`
- Log file: `realtime_ai_*.log`
- Stage 1 shortlist (CSV): `realtime_ai_stage1_*.csv`

## Notes

- Stage 1 will log “heuristic” by design; Stage 2 will show `Codex-shell` if the bridge is active.
- The included `codex_bridge.py` currently leverages the built‑in heuristic analyzer to produce structured JSON. Replace its internals if you want to call your own local LLM or CLI tool.

## Troubleshooting

- “Codex selected but no OPENAI_API_KEY…”: Ensure `CODEX_SHELL_CMD` is set and executable.
- “Shell bridge produced no output”: Your command must print JSON only to stdout.
- “No recent articles found”: Expand `HOURS_BACK`, increase `MAX_ARTICLES_STAGE1`, or verify network.

