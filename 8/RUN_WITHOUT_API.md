# Run Without API Keys — `run_without_api.sh`

This script runs the real‑time news analysis pipeline without requiring any paid AI API keys. It wires the analyzer to local “bridge” CLIs or a fast heuristic, so you can screen news and rank tickers for opportunities at zero cost.

## What It Does
- Selects an AI provider that does not need API keys: `codex` (heuristic), `claude` (Claude Code CLI), or `gemini` (Gemini agent bridge).
- Exports the correct bridge command via environment variables and enforces strict real‑time grounding.
- Calls `realtime_ai_news_analyzer.py` with sensible defaults to fetch articles and score them live.
- Produces a timestamped CSV of AI‑scored opportunities, and a convenience copy as `realtime_ai_results.csv`.

## File
- `run_without_api.sh`

## Supported Providers
- `codex` (default): Calibrated heuristic via `codex_bridge.py`. Free, instant, no keys.
- `claude`: Uses Anthropic’s Claude Code CLI via `claude_cli_bridge.py`. Requires the `claude` CLI but no API key.
- `gemini`: Uses a local Gemini agent bridge via `gemini_agent_bridge.py`. Free, relies on search quality.

## Prerequisites
- Python 3.9+ and project dependencies: `pip install -r requirements.txt`
- For Claude CLI provider:
  - Install the CLI: `npm install -g @anthropic-ai/claude-code`
  - Set up the token: `claude setup-token`
- For Gemini provider: no API key required; script uses the local bridge `gemini_agent_bridge.py`.

## Usage
- Syntax: `./run_without_api.sh <provider> [tickers_file] [hours_back] [max_articles]`
- Defaults: `provider=codex`, `tickers_file=all.txt`, `hours_back=48`, `max_articles=10`

Examples
- Heuristic (fastest): `./run_without_api.sh codex all.txt 48 10`
- Claude CLI bridge: `./run_without_api.sh claude nifty50.txt 24 5`
- Gemini bridge: `./run_without_api.sh gemini nifty50.txt 24 5`

## What the Script Exports
To ensure analysis is grounded in real‑time inputs and uses the chosen bridge, the script sets:
- `AI_STRICT_CONTEXT=1`, `NEWS_STRICT_CONTEXT=1`, `EXIT_STRICT_CONTEXT=1` — force real‑time grounding and avoid training‑data leakage.
- Provider‑specific bridge variables (auto‑set based on `provider` argument):
  - Claude CLI: `CLAUDE_SHELL_CMD="python3 claude_cli_bridge.py"`, `AI_PROVIDER=claude`
  - Gemini: `GEMINI_SHELL_CMD="python3 gemini_agent_bridge.py"`, `AI_PROVIDER=gemini`
  - Codex heuristic: `CODEX_SHELL_CMD="python3 codex_bridge.py"`, `AI_PROVIDER=codex`

## Analyzer Invocation
The script invokes:

`python3 realtime_ai_news_analyzer.py \
  --tickers-file <tickers_file> \
  --hours-back <hours_back> \
  --max-articles <max_articles> \
  --ai-provider <claude|gemini|codex> \
  --verify-internet \
  --probe-agent \
  --disable-ticker-validation`

Key flags
- `--verify-internet`: Checks general connectivity and AI endpoint reachability.
- `--probe-agent`: For shell bridges, asks the agent to fetch a known URL and verifies a content hash.
- `--disable-ticker-validation`: Skips exchange symbol validation for speed; all tickers in the file are processed.

Input tickers
- Provide one symbol per line in `<tickers_file>` (e.g., `all.txt`). The analyzer normalizes symbols (e.g., strips trailing `.NS`).

## Outputs
- Primary output: a timestamped CSV written by the analyzer (e.g., `realtime_ai_results_YYYY-MM-DD_HH-MM-SS_<provider>.csv`).
- Convenience copy: `realtime_ai_results.csv` is also written by the analyzer for quick access.
- Rejected items (when present): `realtime_ai_results_rejected.csv`.

Note: Some older docs and scripts refer to `realtime_ai_rankings.csv`. The analyzer’s default convenience filename is `realtime_ai_results.csv`.

## Optional Environment Tweaks
- `MIN_CERTAINTY_THRESHOLD` — default 40. Lower to widen candidates.
  - Example: `export MIN_CERTAINTY_THRESHOLD=35`
- `AD_POPULARITY_ENABLED` — default 1. Enables advertorial/popularity filtering.
- `AD_STRICT_REJECT` — default 0. If `1`, rejects likely advertorials aggressively.
- `ALLOW_OFFLINE_NEWS_CACHE` — default 0. If `1`, uses `offline_news_cache.json` as a fallback when no live news.
- `AGENT_PROBE_URL` — URL used by `--probe-agent` for validation (default `https://example.com/`).

## Provider Notes
- codex
  - Pros: free, instant, offline‑friendly; Cons: heuristic accuracy (60–70%).
- claude
  - Requires the `claude` CLI but no API key. Good accuracy (~90%+), ~5s per analysis depending on article fetch.
- gemini
  - Free via local agent bridge; accuracy depends on search quality and article content availability.

## Quick Start
1) Ensure dependencies: `pip install -r requirements.txt`
2) Choose a provider:
   - Heuristic: `./run_without_api.sh codex all.txt 48 10`
   - Claude CLI: `npm i -g @anthropic-ai/claude-code && claude setup-token && ./run_without_api.sh claude all.txt 48 10`
   - Gemini: `./run_without_api.sh gemini all.txt 48 10`
3) Open the results: `realtime_ai_results.csv` (or the timestamped CSV the analyzer prints).

## Troubleshooting
- “claude: command not found”
  - Install and set up: `npm install -g @anthropic-ai/claude-code` then `claude setup-token`.
- No output file found
  - Check analyzer logs for the timestamped filename. A convenience copy is written as `realtime_ai_results.csv`.
- Connectivity checks fail
  - Disable agent probing (`--probe-agent` is on by default in the script) or set `ALLOW_OFFLINE_NEWS_CACHE=1` for cached runs.
- Missing Python packages
  - Run `pip install -r requirements.txt`.

## How It Fits Together
- The shell script chooses the bridge and sets environment.
- `realtime_ai_news_analyzer.py` detects the provider and routes prompts to the shell bridge, ensuring responses are valid JSON.
- Analysis is strictly grounded in fetched article content and real‑time market data; training‑data memory is explicitly disabled via strict context flags.

