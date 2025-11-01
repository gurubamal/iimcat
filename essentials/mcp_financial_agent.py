#!/usr/bin/env python3
"""
MCP Financial Analysis Agent Server
Provides AI-powered financial analysis tools via Model Context Protocol
"""

import asyncio
import json
import subprocess
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListResourcesRequest,
    ReadResourceRequest,
    ServerCapabilities,
    ToolsCapability,
    ResourcesCapability,
)

# Server configuration
server = Server("financial-analysis-agent")
BASE_DIR = Path(__file__).parent
OUTPUTS_DIR = BASE_DIR / "outputs"
LEARNING_DIR = BASE_DIR / "learning"
CONFIGS_DIR = BASE_DIR / "configs"

class FinancialAgent:
    """Core financial analysis agent with MCP interface"""

    def __init__(self):
        self.config_file = CONFIGS_DIR / "maximum_intelligence_config.json"
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load maximum intelligence configuration"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            return self.config
        except Exception as e:
            self.config = self._default_config()
            return self.config

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration if file not found"""
        return {
            "system_intelligence_config": {
                "performance_mode": "maximum",
                "scanning_parameters": {
                    "top_picks_count": 50,
                    "analysis_window_hours": 48,
                    "auto_apply_config": True,
                    "auto_screener": True,
                    "path_mode": "ai",
                    "fresh_data_only": True
                }
            }
        }

    async def run_smart_scan(self, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute smart scan with AI path"""
        try:
            cmd = ["python", "smart_scan.py"]
            if options and options.get("auto", True):
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=BASE_DIR
                )
                stdout, stderr = process.communicate(input="1\n", timeout=300)

                return {
                    "status": "completed" if process.returncode == 0 else "error",
                    "output": stdout,
                    "error": stderr,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Return available options
                return {
                    "status": "options_available",
                    "options": [
                        "1) Run AI Path full auto",
                        "2) Run AI Path (apply config, no screener)",
                        "3) Run AI Path (dry run)",
                        "4) Script Path (original rules)",
                        "5) Backfill learnings (7 days)",
                        "6) Archive old outputs"
                    ]
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def run_swing_analysis(self, **kwargs) -> Dict[str, Any]:
        """Execute swing trading analysis"""
        try:
            cmd = [
                "python", "run_swing_paths.py",
                "--path", kwargs.get("path", "ai"),
                "--top", str(kwargs.get("top", 50)),
                "--hours", str(kwargs.get("hours", 48))
            ]

            if kwargs.get("fresh", True):
                cmd.append("--fresh")
            if kwargs.get("auto_apply_config", True):
                cmd.append("--auto-apply-config")
            if kwargs.get("auto_screener", True):
                cmd.append("--auto-screener")

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=BASE_DIR
            )

            return {
                "status": "completed" if process.returncode == 0 else "error",
                "output": process.stdout,
                "error": process.stderr,
                "command": " ".join(cmd),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def enhanced_news_collection(self, **kwargs) -> Dict[str, Any]:
        """Run enhanced India finance news collection"""
        try:
            cmd = [
                "python", "enhanced_india_finance_collector.py",
                "--tickers-file", kwargs.get("tickers_file", "all.txt"),
                "--hours-back", str(kwargs.get("hours_back", 48)),
                "--max-articles", str(kwargs.get("max_articles", 10))
            ]

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=BASE_DIR
            )

            return {
                "status": "completed" if process.returncode == 0 else "error",
                "output": process.stdout,
                "error": process.stderr,
                "command": " ".join(cmd),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_latest_results(self) -> Dict[str, Any]:
        """Get latest analysis results"""
        try:
            results = {}

            # Find latest files
            if OUTPUTS_DIR.exists():
                latest_files = sorted(OUTPUTS_DIR.glob("*.csv"), key=os.path.getmtime, reverse=True)[:5]
                results["latest_outputs"] = [f.name for f in latest_files]

                # Read latest MIT ranking if available
                mit_files = [f for f in latest_files if "mit_rank" in f.name]
                if mit_files:
                    with open(mit_files[0], 'r') as f:
                        content = f.read()
                        results["latest_mit_ranking"] = {
                            "file": mit_files[0].name,
                            "content": content[:2000]  # First 2000 chars
                        }

                # Read latest AI adjusted results
                ai_files = [f for f in latest_files if "ai_adjusted" in f.name]
                if ai_files:
                    with open(ai_files[0], 'r') as f:
                        content = f.read()
                        results["latest_ai_picks"] = {
                            "file": ai_files[0].name,
                            "content": content[:2000]
                        }

                # Read latest live feedback if available
                fb_files = [f for f in latest_files if "feedback_live_" in f.name]
                if fb_files:
                    with open(fb_files[0], 'r') as f:
                        content = f.read()
                        results["latest_live_feedback"] = {
                            "file": fb_files[0].name,
                            "content": content[:2000]
                        }

            # Learning insights
            if LEARNING_DIR.exists():
                debate_file = LEARNING_DIR / "learning_debate.md"
                if debate_file.exists():
                    with open(debate_file, 'r') as f:
                        content = f.read()
                        results["learning_insights"] = content[:1000]

            return {
                "status": "success",
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_top_recommendations(self, count: int = 10) -> Dict[str, Any]:
        """Extract top swing trading recommendations"""
        try:
            latest_results = await self.get_latest_results()

            recommendations = []

            # Extract from config high confidence opportunities
            if hasattr(self, 'config'):
                high_conf = self.config.get("current_high_confidence_opportunities", [])
                for opp in high_conf[:count]:
                    recommendations.append({
                        "ticker": opp.get("ticker", ""),
                        "target": opp.get("target", ""),
                        "catalyst": opp.get("catalyst", ""),
                        "confidence": opp.get("confidence", "medium"),
                        "source": "configuration"
                    })

            # Add blacklisted tickers warning
            blacklisted = ["RETAIL", "HINDALCO", "APOLLO", "WEL", "BEL"]

            return {
                "status": "success",
                "recommendations": recommendations[:count],
                "avoid_tickers": blacklisted,
                "risk_notice": "Use 8-12% stop loss, target 15-25% gains",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Initialize agent
agent = FinancialAgent()

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available financial analysis tools"""
    return [
        Tool(
            name="run_smart_scan",
            description="Execute comprehensive financial market scan with AI intelligence",
            inputSchema={
                "type": "object",
                "properties": {
                    "auto": {
                        "type": "boolean",
                        "description": "Run automatically with AI Path full auto (default: true)",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="run_swing_analysis",
            description="Execute swing trading analysis with AI-powered stock selection",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Analysis path: 'ai' or 'script'",
                        "default": "ai"
                    },
                    "top": {
                        "type": "integer",
                        "description": "Number of top picks to analyze",
                        "default": 50
                    },
                    "hours": {
                        "type": "integer",
                        "description": "Analysis window in hours",
                        "default": 48
                    },
                    "fresh": {
                        "type": "boolean",
                        "description": "Use fresh data only",
                        "default": True
                    },
                    "auto_apply_config": {
                        "type": "boolean",
                        "description": "Auto-apply intelligent configuration",
                        "default": True
                    },
                    "auto_screener": {
                        "type": "boolean",
                        "description": "Run automatic screening",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="enhanced_news_collection",
            description="Collect enhanced financial news for Indian markets",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers_file": {
                        "type": "string",
                        "description": "File containing all tickers",
                        "default": "all.txt"
                    },
                    "hours_back": {
                        "type": "integer",
                        "description": "Hours to look back for news",
                        "default": 48
                    },
                    "max_articles": {
                        "type": "integer",
                        "description": "Maximum articles per ticker",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="get_latest_results",
            description="Retrieve latest analysis results and insights",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_top_recommendations",
            description="Get top swing trading stock recommendations with risk assessment",
            inputSchema={
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "Number of recommendations to return",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="get_system_status",
            description="Get current system intelligence status and configuration",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution"""
    try:
        if name == "run_smart_scan":
            result = await agent.run_smart_scan(arguments)

        elif name == "run_swing_analysis":
            result = await agent.run_swing_analysis(**arguments)

        elif name == "enhanced_news_collection":
            result = await agent.enhanced_news_collection(**arguments)

        elif name == "get_latest_results":
            result = await agent.get_latest_results()

        elif name == "get_top_recommendations":
            count = arguments.get("count", 10)
            result = await agent.get_top_recommendations(count)

        elif name == "get_system_status":
            result = {
                "status": "active",
                "intelligence_level": "MAXIMUM",
                "performance_mode": agent.config.get("system_intelligence_config", {}).get("performance_mode", "standard"),
                "config_loaded": bool(agent.config),
                "base_directory": str(BASE_DIR),
                "timestamp": datetime.now().isoformat()
            }

        else:
            result = {"status": "error", "error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        error_result = {"status": "error", "error": str(e), "tool": name}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available financial data resources"""
    resources = []

    # Add configuration files
    if CONFIGS_DIR.exists():
        for config_file in CONFIGS_DIR.glob("*.json"):
            resources.append(Resource(
                uri=f"config://{config_file.name}",
                name=f"Configuration: {config_file.name}",
                description=f"Financial analysis configuration: {config_file.name}",
                mimeType="application/json"
            ))

    # Add latest output files
    if OUTPUTS_DIR.exists():
        latest_files = sorted(OUTPUTS_DIR.glob("*.csv"), key=os.path.getmtime, reverse=True)[:10]
        for output_file in latest_files:
            resources.append(Resource(
                uri=f"output://{output_file.name}",
                name=f"Analysis Result: {output_file.name}",
                description=f"Latest financial analysis output: {output_file.name}",
                mimeType="text/csv"
            ))

    # Add learning files
    if LEARNING_DIR.exists():
        for learning_file in LEARNING_DIR.glob("*.md"):
            resources.append(Resource(
                uri=f"learning://{learning_file.name}",
                name=f"Learning Insight: {learning_file.name}",
                description=f"AI learning and recommendations: {learning_file.name}",
                mimeType="text/markdown"
            ))

    return resources

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read financial data resource content"""
    try:
        if uri.startswith("config://"):
            filename = uri.replace("config://", "")
            file_path = CONFIGS_DIR / filename

        elif uri.startswith("output://"):
            filename = uri.replace("output://", "")
            file_path = OUTPUTS_DIR / filename

        elif uri.startswith("learning://"):
            filename = uri.replace("learning://", "")
            file_path = LEARNING_DIR / filename

        else:
            raise ValueError(f"Unsupported resource URI: {uri}")

        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise FileNotFoundError(f"Resource not found: {file_path}")

    except Exception as e:
        return f"Error reading resource {uri}: {str(e)}"

async def main():
    """Run the MCP server"""
    async with stdio_server(server) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="financial-analysis-agent",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    tools=ToolsCapability(list_changed=True),
                    resources=ResourcesCapability(subscribe=False, list_changed=True)
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
