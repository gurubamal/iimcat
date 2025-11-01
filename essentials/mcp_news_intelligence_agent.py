#!/usr/bin/env python3
"""
MCP News Intelligence Agent
Provides a Model Context Protocol server that can fetch full news for
all tickers listed in all.txt and run the AI investment scan pipeline.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    TextContent,
    Tool,
    ServerCapabilities,
    ToolsCapability,
    ResourcesCapability,
)

from learning_db import (
    ensure_db as ensure_learning_db,
    generate_self_assessment,
    get_assistant_attempts,
    get_latest_run_info,
    get_run_snapshot,
    harvest_price_feedback,
    record_assistant_feedback,
    record_decision_feedback,
    build_verdict_summary,
)

server = Server("news-intelligence-agent")
BASE_DIR = Path(__file__).parent.resolve()
OUTPUTS_DIR = BASE_DIR / "outputs"
LEARNING_DIR = BASE_DIR / "learning"
CONFIGS_DIR = BASE_DIR / "configs"
AGGREGATED_PREFIX = "aggregated_full_articles_"
MAX_CAPTURE = 6000


def _iso(ts: float | None = None) -> str:
    when = datetime.utcnow() if ts is None else datetime.fromtimestamp(ts)
    return when.isoformat()


def _truncate(text: str, limit: int = MAX_CAPTURE) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


class NewsIntelligenceAgent:
    def __init__(self) -> None:
        self.collector_script = BASE_DIR / "fetch_full_articles.py"
        self.analysis_script = BASE_DIR / "run_swing_paths.py"
        self.tickers_file = BASE_DIR / "all.txt"
        self.learning_db_path = LEARNING_DIR / "learning.db"
        self.assistant_config_file = CONFIGS_DIR / "assistant_channels.json"
        self.assistant_prompt_dir = OUTPUTS_DIR / "assistant_requests"
        self._assistant_channels_cache: Optional[List[Dict[str, Any]]] = None

    def _load_all_tickers(self, limit: int = 0) -> List[str]:
        if not self.tickers_file.exists():
            return []
        tickers: List[str] = []
        with open(self.tickers_file, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                symbol = line.strip()
                if not symbol or symbol.startswith("#"):
                    continue
                tickers.append(symbol)
                if limit and len(tickers) >= limit:
                    break
        return tickers

    def _iter_aggregated_candidates(self) -> List[Path]:
        roots = [BASE_DIR, OUTPUTS_DIR / "aggregates"]
        candidates: List[Path] = []
        for root in roots:
            if not root.exists():
                continue
            for path in root.glob(f"{AGGREGATED_PREFIX}*"):
                if not path.is_file():
                    continue
                try:
                    path.stat()
                except FileNotFoundError:
                    continue
                candidates.append(path)
        return candidates

    def _list_aggregated(self, limit: int = 8) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        candidates = self._iter_aggregated_candidates()
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for path in candidates[:limit]:
            stat = path.stat()
            rows.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "modified": _iso(stat.st_mtime),
                    "size_bytes": stat.st_size,
                }
            )
        return rows

    def _detect_new_aggregated(self, before: set[str], since_ts: float) -> Optional[Path]:
        freshly: List[tuple[float, Path]] = []
        for path in self._iter_aggregated_candidates():
            if path.name in before:
                continue
            try:
                mtime = path.stat().st_mtime
            except FileNotFoundError:
                continue
            if mtime + 1 < since_ts:
                continue
            freshly.append((mtime, path))
        if freshly:
            freshly.sort(reverse=True)
            return freshly[0][1]
        # Fallback to latest overall to keep pipeline usable
        candidates = self._iter_aggregated_candidates()
        if not candidates:
            return None
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0]

    def _list_output_files(self, limit: int = 6) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        if not OUTPUTS_DIR.exists():
            return rows
        files: List[Path] = []
        for pattern in (
            "ai_adjusted_top25_*.csv",
            "swing_top25_*.txt",
            "ranking_config_recommendation_*.json",
            "all_news_screen.csv",
            "verdict_helper_*.md",
            "verdict_helper_latest.md",
        ):
            files.extend(OUTPUTS_DIR.glob(pattern))
        files = [p for p in files if p.is_file()]
        unique: List[Path] = []
        seen = set()
        for p in files:
            key = p.resolve()
            if key in seen:
                continue
            seen.add(key)
            unique.append(p)
        unique.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        files = unique
        for path in files[:limit]:
            stat = path.stat()
            rows.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "modified": _iso(stat.st_mtime),
                    "size_bytes": stat.st_size,
                }
            )
        return rows

    def _ensure_learning_db(self) -> Path:
        ensure_learning_db(str(self.learning_db_path))
        return self.learning_db_path

    def _load_assistant_channels(self) -> List[Dict[str, Any]]:
        if self._assistant_channels_cache is not None:
            return self._assistant_channels_cache
        if not self.assistant_config_file.exists():
            self._assistant_channels_cache = []
            return []
        try:
            data = json.loads(self.assistant_config_file.read_text(encoding="utf-8"))
            channels = data.get("assistants", [])
            if not isinstance(channels, list):
                channels = []
        except Exception:
            channels = []
        normalised: List[Dict[str, Any]] = []
        for item in channels:
            if isinstance(item, dict):
                normalised.append(item)
        self._assistant_channels_cache = normalised
        return normalised

    async def _build_run_prompt(self, run_id: int, top_n: int = 5) -> Dict[str, Any]:
        snapshot = await asyncio.to_thread(get_run_snapshot, str(self.learning_db_path), run_id, top_n)
        if not snapshot:
            return {"prompt": "", "snapshot": {}}
        lines: List[str] = []
        lines.append(f"Financial scan run {run_id}")
        lines.append(f"Timestamp: {snapshot.get('timestamp', '')}")
        agg_file = snapshot.get("agg_file") or ""
        if agg_file:
            lines.append(f"Aggregated file: {agg_file}")
        lines.append("")
        lines.append("Top opportunities:")
        picks = snapshot.get("picks", []) or []
        if picks:
            for pick in picks:
                rank = pick.get("rank")
                ticker = pick.get("ticker") or ""
                score = pick.get("adj_score")
                title = (pick.get("title") or "").strip()
                source = (pick.get("source") or "").strip()
                event = (pick.get("event_type") or "").strip()
                if isinstance(score, (int, float)):
                    score_txt = f"{score:.3f}"
                else:
                    score_txt = str(score or "")
                lines.append(f"{rank}. {ticker} (score {score_txt}) [{event}] - {title} ({source})")
        else:
            lines.append("(No picks recorded)")
        lines.append("")
        lines.append("Please review these results and share any buy/sell/hold suggestions or risks we should record.")
        aggregate_excerpt = ""
        if agg_file:
            agg_path = Path(agg_file)
            if not agg_path.is_absolute():
                agg_path = BASE_DIR / agg_path
            if agg_path.exists():
                try:
                    aggregate_excerpt = agg_path.read_text(encoding="utf-8", errors="ignore")[:2000]
                except Exception:
                    aggregate_excerpt = ""
        if aggregate_excerpt:
            lines.append("")
            lines.append("Aggregated news excerpt:")
            lines.append(aggregate_excerpt)
        prompt_text = "\n".join(lines)
        return {"prompt": prompt_text, "snapshot": snapshot, "aggregate_excerpt": aggregate_excerpt}

    async def collect_assistant_feedback(
        self,
        run_id: Optional[int] = None,
        assistants: Optional[Iterable[str]] = None,
        top_n: int = 5,
    ) -> Dict[str, Any]:
        db_path = self._ensure_learning_db()
        if run_id is None:
            latest = await asyncio.to_thread(get_latest_run_info, str(db_path))
            run_id = latest.get("run_id") if latest else None
        if not run_id:
            return {"status": "empty", "message": "No AI runs recorded yet."}
        prompt_payload = await self._build_run_prompt(run_id, top_n=top_n)
        prompt_text = prompt_payload.get("prompt") or ""
        channels = self._load_assistant_channels()
        if not channels:
            return {"status": "empty", "message": "No assistant channels configured.", "run_id": run_id}
        assistant_filter = {name.lower() for name in assistants} if assistants else None
        entries: List[Dict[str, Any]] = []
        attempts: List[Dict[str, Any]] = []
        if prompt_text:
            try:
                self.assistant_prompt_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
        for channel in channels:
            if not isinstance(channel, dict):
                continue
            name = str(channel.get("name") or "").strip()
            if not name:
                continue
            if not channel.get("enabled", True):
                continue
            if assistant_filter and name.lower() not in assistant_filter:
                continue
            input_mode = str(channel.get("input_mode") or "stdin").lower()
            shell_command = channel.get("shell_command")
            timeout = int(channel.get("timeout") or 180)
            formatted_command = ""
            response = ""
            error = ""
            status = "skipped"
            if not shell_command:
                status = "error"
                error = "No shell_command configured."
            else:
                context = {
                    "run_id": run_id,
                    "assistant": name,
                }
                if input_mode == "file":
                    prompt_file = self.assistant_prompt_dir / f"run_{run_id}_{name}.txt"
                    try:
                        prompt_file.write_text(prompt_text, encoding="utf-8")
                        context["input_path"] = str(prompt_file)
                    except Exception as exc:
                        status = "error"
                        error = f"Unable to write prompt file: {exc}"
                if status != "error":
                    try:
                        formatted_command = shell_command.format(**context)
                    except KeyError as exc:
                        status = "error"
                        error = f"Missing placeholder {exc!s} in shell_command."
                if status != "error":
                    args = ["bash", "-lc", formatted_command]
                    try:
                        proc = await asyncio.create_subprocess_exec(
                            *args,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            cwd=str(BASE_DIR),
                        )
                        if input_mode == "stdin":
                            stdout_b, stderr_b = await asyncio.wait_for(
                                proc.communicate(prompt_text.encode("utf-8")),
                                timeout=timeout,
                            )
                        else:
                            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                        status = "success" if proc.returncode == 0 else "error"
                        response = stdout_b.decode("utf-8", errors="ignore")
                        error = stderr_b.decode("utf-8", errors="ignore")
                    except asyncio.TimeoutError:
                        status = "timeout"
                        response = ""
                        error = "Assistant command timed out."
                    except FileNotFoundError as exc:
                        status = "error"
                        response = ""
                        error = f"Executable not found: {exc}"
                    except Exception as exc:
                        status = "error"
                        response = ""
                        error = str(exc)
            entries.append({
                "assistant": name,
                "status": status,
                "command": formatted_command,
                "response": response[:2000] if response else "",
                "error": error[:2000] if error else "",
            })
            attempts.append({
                "assistant": name,
                "status": status,
                "command": formatted_command,
                "response_preview": response[:200] if response else "",
                "error_preview": error[:200] if error else "",
            })
        db_result = await asyncio.to_thread(
            record_assistant_feedback,
            str(db_path),
            run_id,
            entries,
        )
        return {
            "status": "completed" if attempts else "empty",
            "run_id": run_id,
            "attempts": attempts,
            "db_result": db_result,
            "prompt_excerpt": prompt_text[:500] if prompt_text else "",
        }

    async def _persist_verdict_summary(self, run_id: int, summary: str) -> Optional[str]:
        if not summary:
            return None
        def _write() -> str:
            OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            target = OUTPUTS_DIR / f"verdict_helper_run_{run_id}_{timestamp}.md"
            target.write_text(summary, encoding="utf-8")
            latest = OUTPUTS_DIR / "verdict_helper_latest.md"
            latest.write_text(summary, encoding="utf-8")
            return str(target)
        return await asyncio.to_thread(_write)

    async def get_verdict_helper(self, run_id: Optional[int] = None, top_n: int = 10) -> Dict[str, Any]:
        db_path = self._ensure_learning_db()
        if run_id is None:
            latest = await asyncio.to_thread(get_latest_run_info, str(db_path))
            run_id = latest.get("run_id") if latest else None
        if not run_id:
            return {"status": "empty", "message": "No AI runs recorded yet."}
        assistant_attempts = await asyncio.to_thread(get_assistant_attempts, str(db_path), run_id)
        learning_snapshot = await asyncio.to_thread(generate_self_assessment, str(db_path), 10)
        summary = await asyncio.to_thread(
            build_verdict_summary,
            str(db_path),
            run_id,
            assistant_attempts=assistant_attempts,
            learning_report={"self_assessment": learning_snapshot} if isinstance(learning_snapshot, dict) else None,
            top_n=min(top_n, 10),
        )
        return {
            "status": "success",
            "run_id": run_id,
            "summary": summary,
            "assistant_attempts": assistant_attempts,
        }
    async def _run_subprocess(self, cmd: List[str], timeout: int = 900) -> Dict[str, Any]:
        start = datetime.utcnow()
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(BASE_DIR),
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {
                "returncode": None,
                "stdout": "",
                "stderr": "Command timed out",
                "started": start.isoformat(),
                "ended": _iso(),
                "command": cmd,
                "duration_seconds": (datetime.utcnow() - start).total_seconds(),
            }
        stdout = stdout_b.decode("utf-8", errors="ignore")
        stderr = stderr_b.decode("utf-8", errors="ignore")
        return {
            "returncode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "started": start.isoformat(),
            "ended": _iso(),
            "command": cmd,
            "duration_seconds": (datetime.utcnow() - start).total_seconds(),
        }

    async def record_feedback(self, entries: List[Dict[str, Any]], include_assessment: bool = True) -> Dict[str, Any]:
        if not entries:
            return {"status": "error", "error": "No feedback entries provided."}
        db_path = self._ensure_learning_db()

        def _write_and_summarize() -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
            result = record_decision_feedback(str(db_path), entries)
            summary = generate_self_assessment(str(db_path)) if include_assessment else None
            return result, summary

        stats, summary = await asyncio.to_thread(_write_and_summarize)
        payload: Dict[str, Any] = {
            "status": "recorded",
            "stats": stats,
        }
        if summary:
            payload["self_assessment"] = summary
        return payload

    async def auto_learning_cycle(self, min_hours: int = 24, run_limit: int = 10) -> Dict[str, Any]:
        db_path = self._ensure_learning_db()

        def _cycle() -> Tuple[Dict[str, Any], Dict[str, Any]]:
            harvest = harvest_price_feedback(str(db_path), min_hours=min_hours)
            summary = generate_self_assessment(str(db_path), run_limit)
            return harvest, summary

        harvest_result, summary = await asyncio.to_thread(_cycle)
        return {
            "status": "completed",
            "harvest": harvest_result,
            "self_assessment": summary,
        }

    async def self_assessment(self, run_limit: int = 10) -> Dict[str, Any]:
        db_path = self._ensure_learning_db()
        return await asyncio.to_thread(generate_self_assessment, str(db_path), run_limit)

    async def collect_full_news(
        self,
        hours_back: int = 24,
        limit: int = 0,
        max_articles: int = 2,
        concurrency: int = 6,
        per_host: int = 2,
        per_host_interval: float = 0.6,
        publishers_only: bool = True,
        no_per_ticker: bool = True,
        output_prefix: Optional[str] = None,
        timeout: int = 1200,
    ) -> Dict[str, Any]:
        if not self.collector_script.exists():
            return {"status": "error", "error": f"Collector script missing: {self.collector_script}"}
        if not self.tickers_file.exists():
            return {"status": "error", "error": f"Tickers file missing: {self.tickers_file}"}
        before = {p.name for p in self._iter_aggregated_candidates()}
        start_ts = datetime.utcnow().timestamp()
        cmd = [
            sys.executable,
            str(self.collector_script),
            "--tickers-file",
            str(self.tickers_file),
            "--hours-back",
            str(int(hours_back)),
            "--max-articles",
            str(int(max_articles)),
            "--concurrency",
            str(int(max(concurrency, 1))),
            "--per-host",
            str(int(max(per_host, 1))),
            "--per-host-interval",
            str(float(per_host_interval)),
        ]
        if limit and limit > 0:
            cmd.extend(["--limit", str(int(limit))])
        if publishers_only:
            cmd.append("--publishers-only")
        if no_per_ticker:
            cmd.append("--no-per-ticker")
        if output_prefix:
            cmd.extend(["--output-file", output_prefix])
        result = await self._run_subprocess(cmd, timeout=timeout)
        aggregated_path = self._detect_new_aggregated(before, start_ts)
        status = "completed" if result.get("returncode") == 0 else "error"
        return {
            "status": status,
            "command": " ".join(cmd),
            "aggregated_file": str(aggregated_path) if aggregated_path else None,
            "stdout": _truncate(result.get("stdout", "")),
            "stderr": _truncate(result.get("stderr", "")),
            "started": result.get("started"),
            "ended": result.get("ended"),
            "duration_seconds": result.get("duration_seconds"),
        }

    async def run_investment_scan(
        self,
        path: str = "ai",
        top: int = 25,
        auto_apply_config: bool = True,
        auto_screener: bool = False,
        deadline_mins: int = 15,
        hours: int = 24,
        fresh_fetch: bool = False,
        fetch_limit: int = 0,
        timeout: int = 900,
        auto_learning: bool = True,
        learning_min_hours: int = 24,
        assessment_runs: int = 10,
        assistant_feedback: bool = False,
        assistant_list: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if fresh_fetch:
            fetch_result = await self.collect_full_news(
                hours_back=hours,
                limit=fetch_limit,
                max_articles=2,
                publishers_only=True,
                no_per_ticker=True,
                timeout=timeout,
            )
            if fetch_result.get("status") != "completed":
                return {
                    "status": "error",
                    "error": "Fresh fetch failed",
                    "fetch_result": fetch_result,
                }
        if not self.analysis_script.exists():
            return {"status": "error", "error": f"Analysis script missing: {self.analysis_script}"}
        latest_agg = self._detect_new_aggregated(set(), datetime.utcnow().timestamp() - 3600)
        if not latest_agg or not latest_agg.exists():
            return {
                "status": "error",
                "error": "No aggregated_full_articles_* file available. Run collect_full_news first.",
            }
        cmd = [
            sys.executable,
            str(self.analysis_script),
            "--path",
            path,
            "--top",
            str(int(top)),
            "--hours",
            str(int(hours)),
            "--deadline-mins",
            str(int(deadline_mins)),
        ]
        if auto_apply_config:
            cmd.append("--auto-apply-config")
        if auto_screener:
            cmd.append("--auto-screener")
        result = await self._run_subprocess(cmd, timeout=timeout)
        status = "completed" if result.get("returncode") == 0 else "error"
        learning_report: Optional[Dict[str, Any]] = None
        if status == "completed" and auto_learning:
            try:
                learning_report = await self.auto_learning_cycle(
                    min_hours=learning_min_hours,
                    run_limit=assessment_runs,
                )
            except Exception as exc:  # noqa: BLE001
                learning_report = {"status": "error", "error": str(exc)}
        latest_info = await asyncio.to_thread(get_latest_run_info, str(self.learning_db_path))
        run_id = latest_info.get('run_id') if latest_info else None
        assistant_result: Optional[Dict[str, Any]] = None
        assistant_attempts_for_summary: Optional[List[Dict[str, Any]]] = None
        if status == "completed" and assistant_feedback:
            try:
                assistant_result = await self.collect_assistant_feedback(
                    run_id=run_id,
                    assistants=assistant_list,
                    top_n=min(top, 10),
                )
            except Exception as exc:  # noqa: BLE001
                assistant_result = {"status": "error", "error": str(exc)}
            else:
                if isinstance(assistant_result, dict):
                    assistant_attempts_for_summary = assistant_result.get('attempts')
        verdict_summary = ''
        verdict_path: Optional[str] = None
        if run_id:
            if assistant_attempts_for_summary is None:
                assistant_attempts_for_summary = await asyncio.to_thread(
                    get_assistant_attempts,
                    str(self.learning_db_path),
                    run_id,
                )
            learning_context = learning_report
            if not learning_context:
                manual_sa = await asyncio.to_thread(
                    generate_self_assessment,
                    str(self.learning_db_path),
                    min(assessment_runs, 10),
                )
                if isinstance(manual_sa, dict):
                    learning_context = {"self_assessment": manual_sa}
            verdict_summary = await asyncio.to_thread(
                build_verdict_summary,
                str(self.learning_db_path),
                run_id,
                assistant_attempts=assistant_attempts_for_summary,
                learning_report=learning_context,
                top_n=min(top, 10),
            )
            verdict_path = await self._persist_verdict_summary(run_id, verdict_summary)
        stdout_text = result.get("stdout", "") or ""
        if verdict_summary:
            stdout_text = f"{stdout_text}\n\n== Verdict Helper ==\n{verdict_summary}\n"
        return {
            "status": status,
            "command": " ".join(cmd),
            "stdout": _truncate(stdout_text),
            "stderr": _truncate(result.get("stderr", "")),
            "started": result.get("started"),
            "ended": result.get("ended"),
            "duration_seconds": result.get("duration_seconds"),
            "latest_aggregated_used": latest_agg.name if latest_agg else None,
            "auto_learning": learning_report,
            "assistant_feedback": assistant_result,
            "verdict_summary": verdict_summary,
            "verdict_summary_path": verdict_path,
        }


    async def pipeline_status(self, max_items: int = 5) -> Dict[str, Any]:
        status: Dict[str, Any] = {
            "timestamp": _iso(),
            "aggregated_news": self._list_aggregated(limit=max_items),
            "outputs": self._list_output_files(limit=max_items),
            "tickers_in_all_txt": len(self._load_all_tickers()),
        }
        learning_files: List[Dict[str, Any]] = []
        if LEARNING_DIR.exists():
            for name in ("learning_context.md", "learning_debate.md", "core_priorities.md"):
                path = LEARNING_DIR / name
                if not path.exists() or not path.is_file():
                    continue
                stat = path.stat()
                learning_files.append(
                    {
                        "name": path.name,
                        "path": str(path),
                        "modified": _iso(stat.st_mtime),
                        "size_bytes": stat.st_size,
                    }
                )
        status["learning_files"] = learning_files
        return status


agent = NewsIntelligenceAgent()


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [
        Tool(
            name="collect_full_news",
            description="Fetch aggregated full-text news for all tickers in all.txt",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours_back": {"type": "integer", "default": 24, "minimum": 1, "maximum": 168},
                    "limit": {"type": "integer", "default": 0, "minimum": 0},
                    "max_articles": {"type": "integer", "default": 2, "minimum": 1, "maximum": 10},
                    "concurrency": {"type": "integer", "default": 6, "minimum": 1, "maximum": 16},
                    "per_host": {"type": "integer", "default": 2, "minimum": 1, "maximum": 6},
                    "per_host_interval": {"type": "number", "default": 0.6, "minimum": 0.1, "maximum": 2.0},
                    "publishers_only": {"type": "boolean", "default": True},
                    "no_per_ticker": {"type": "boolean", "default": True},
                    "output_prefix": {"type": "string"},
                    "timeout": {"type": "integer", "default": 1200, "minimum": 60, "maximum": 3600},
                },
            },
        ),
        Tool(
            name="run_investment_scan",
            description="Run AI investment scan using latest aggregated news file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "enum": ["ai", "script"], "default": "ai"},
                    "top": {"type": "integer", "default": 25, "minimum": 10, "maximum": 100},
                    "auto_apply_config": {"type": "boolean", "default": True},
                    "auto_screener": {"type": "boolean", "default": False},
                    "deadline_mins": {"type": "integer", "default": 15, "minimum": 5, "maximum": 60},
                    "hours": {"type": "integer", "default": 24, "minimum": 6, "maximum": 168},
                    "fresh_fetch": {"type": "boolean", "default": False},
                    "fetch_limit": {"type": "integer", "default": 0, "minimum": 0},
                    "timeout": {"type": "integer", "default": 900, "minimum": 60, "maximum": 3600},
                    "auto_learning": {"type": "boolean", "default": True},
                    "learning_min_hours": {"type": "integer", "default": 24, "minimum": 6, "maximum": 168},
                    "assessment_runs": {"type": "integer", "default": 10, "minimum": 3, "maximum": 40},
                    "assistant_feedback": {"type": "boolean", "default": False},
                    "assistant_list": {"type": "array", "items": {"type": "string"}},
                },
            },
        ),
        Tool(
            name="log_feedback",
            description="Record outcome feedback to refine reliability and learning metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "entries": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "run_id": {"type": "integer"},
                                "ticker": {"type": "string"},
                                "verdict": {"type": "string", "description": "win/loss/neutral etc"},
                                "expected_return": {"type": "number"},
                                "actual_return": {"type": "number"},
                                "rating": {"type": "number", "description": "0-10 sentiment or confidence"},
                                "confidence": {"type": "number"},
                                "notes": {"type": "string"}
                            },
                            "required": ["ticker"],
                        },
                    },
                    "include_assessment": {"type": "boolean", "default": True},
                },
                "required": ["entries"],
            },
        ),
        Tool(
            name="self_assessment",
            description="Generate compact self-learning metrics across recent runs",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_limit": {"type": "integer", "default": 10, "minimum": 3, "maximum": 40}
                },
            },
        ),
        Tool(
            name="auto_learning_cycle",
            description="Harvest stored price feedback and refresh self-assessment in one call",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_hours": {"type": "integer", "default": 24, "minimum": 6, "maximum": 168},
                    "run_limit": {"type": "integer", "default": 10, "minimum": 3, "maximum": 40}
                },
            },
        ),
        Tool(
            name="get_verdict_helper",
            description="View the latest verdict helper summary or a specific run",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer"},
                    "top_n": {"type": "integer", "default": 5, "minimum": 3, "maximum": 25}
                },
            },
        ),
        Tool(
            name="pipeline_status",
            description="Summarize recent news runs, outputs, and learning files",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_items": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
                },
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    try:
        if name == "collect_full_news":
            result = await agent.collect_full_news(**arguments)
        elif name == "run_investment_scan":
            result = await agent.run_investment_scan(**arguments)
        elif name == "log_feedback":
            entries = arguments.get("entries", [])
            include = arguments.get("include_assessment", True)
            result = await agent.record_feedback(entries, include_assessment=include)
        elif name == "self_assessment":
            run_limit = arguments.get("run_limit", 10)
            result = await agent.self_assessment(run_limit=run_limit)
        elif name == "auto_learning_cycle":
            min_hours = arguments.get("min_hours", 24)
            run_limit = arguments.get("run_limit", 10)
            result = await agent.auto_learning_cycle(min_hours=min_hours, run_limit=run_limit)
        elif name == "get_verdict_helper":
            run_id = arguments.get("run_id")
            top_n = arguments.get("top_n", 5)
            result = await agent.get_verdict_helper(run_id=run_id, top_n=top_n)
        elif name == "pipeline_status":
            max_items = arguments.get("max_items", 5)
            result = await agent.pipeline_status(max_items=max_items)
        else:
            result = {"status": "error", "error": f"Unknown tool: {name}"}
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as exc:  # noqa: BLE001
        error_payload = {"status": "error", "error": str(exc), "tool": name}
        return [TextContent(type="text", text=json.dumps(error_payload, indent=2))]


@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    resources: List[Resource] = []
    for entry in agent._list_aggregated(limit=10):
        resources.append(
            Resource(
                uri=f"news://{entry['name']}",
                name=f"Aggregated News: {entry['name']}",
                description=f"Aggregated news run captured on {entry['modified']}",
                mimeType="text/plain",
            )
        )
    for entry in agent._list_output_files(limit=10):
        resources.append(
            Resource(
                uri=f"output://{entry['name']}",
                name=f"Output: {entry['name']}",
                description=f"Investment output generated on {entry['modified']}",
                mimeType="text/plain" if entry['name'].endswith(".txt") else "text/csv",
            )
        )
    if LEARNING_DIR.exists():
        for name in ("learning_context.md", "learning_debate.md", "core_priorities.md"):
            path = LEARNING_DIR / name
            if not path.exists() or not path.is_file():
                continue
            resources.append(
                Resource(
                    uri=f"learning://{name}",
                    name=f"Learning: {name}",
                    description="AI learning context and recommendations",
                    mimeType="text/markdown",
                )
            )
    return resources


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    try:
        if uri.startswith("news://"):
            target = uri.replace("news://", "", 1)
            for path in agent._iter_aggregated_candidates():
                if path.name == target:
                    return path.read_text(encoding="utf-8", errors="ignore")
            raise FileNotFoundError(target)
        if uri.startswith("output://"):
            target = uri.replace("output://", "", 1)
            candidates = list((OUTPUTS_DIR / "").glob(target))
            if not candidates:
                candidates = [OUTPUTS_DIR / target]
            for path in candidates:
                if path.exists() and path.is_file():
                    return path.read_text(encoding="utf-8", errors="ignore")
            raise FileNotFoundError(target)
        if uri.startswith("learning://"):
            name = uri.replace("learning://", "", 1)
            path = LEARNING_DIR / name
            if path.exists() and path.is_file():
                return path.read_text(encoding="utf-8", errors="ignore")
            raise FileNotFoundError(name)
        raise ValueError(f"Unsupported resource URI: {uri}")
    except Exception as exc:  # noqa: BLE001
        return f"Error reading resource {uri}: {exc}"


async def main() -> None:
    async with stdio_server(server) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="news-intelligence-agent",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    tools=ToolsCapability(list_changed=True),
                    resources=ResourcesCapability(subscribe=False, list_changed=True)
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
