#!/usr/bin/env python3
"""
Copilot Agent Auto-Approval Manager
Handles auto-run and approval settings for the investment analysis system
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class CopilotAgent:
    """Manages auto-approval and auto-run settings"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.base_dir = Path(__file__).parent
        self.config_path = config_path or self.base_dir / "configs" / "copilot_agent_config.json"
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load copilot agent configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Config not found: {self.config_path}")
            return self.default_config()
    
    def default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "approval_mode": {"mode": "manual"},
            "auto_run_settings": {},
            "notification_settings": {"show_progress": True}
        }
    
    def save_config(self):
        """Save current configuration"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"✅ Configuration saved to: {self.config_path}")
    
    def get_approval_mode(self) -> str:
        """Get current approval mode"""
        return self.config.get("approval_mode", {}).get("mode", "manual")
    
    def set_approval_mode(self, mode: str):
        """Set approval mode: auto, semi, or manual"""
        if mode not in ["auto", "semi", "manual"]:
            raise ValueError("Mode must be: auto, semi, or manual")
        
        self.config["approval_mode"]["mode"] = mode
        self.save_config()
        print(f"✅ Approval mode set to: {mode}")
    
    def is_auto_approved(self, action: str) -> bool:
        """Check if an action is auto-approved"""
        mode = self.get_approval_mode()
        
        if mode == "auto":
            return True
        
        if mode == "manual":
            return False
        
        # Semi mode - check specific action
        auto_run = self.config.get("auto_run_settings", {})
        action_config = auto_run.get(action, {})
        return action_config.get("auto_approve", False)
    
    def run_command(self, command_name: str, background: bool = False) -> Dict[str, Any]:
        """Run a quick command from config"""
        quick_commands = self.config.get("quick_commands", {})
        
        if command_name not in quick_commands:
            return {"success": False, "error": f"Command '{command_name}' not found"}
        
        cmd_config = quick_commands[command_name]
        command = cmd_config["command"]
        auto_approve = cmd_config.get("auto_approve", False)
        
        # Check approval
        if not auto_approve and not self.is_auto_approved("general"):
            response = input(f"Run '{command}'? [y/N]: ").strip().lower()
            if response not in ['y', 'yes']:
                return {"success": False, "error": "User cancelled"}
        
        print(f"🚀 Running: {command}")
        
        try:
            if background:
                # Run in background
                log_file = f"copilot_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                with open(log_file, 'w') as f:
                    process = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=f,
                        stderr=subprocess.STDOUT,
                        cwd=self.base_dir
                    )
                return {
                    "success": True,
                    "pid": process.pid,
                    "log_file": log_file,
                    "message": f"Running in background (PID: {process.pid})"
                }
            else:
                # Run synchronously
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True
                )
                return {
                    "success": result.returncode == 0,
                    "returncode": result.returncode,
                    "output": result.stdout,
                    "error": result.stderr
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def show_settings(self):
        """Display current settings"""
        mode = self.get_approval_mode()
        
        print("="*80)
        print("🤖 COPILOT AGENT SETTINGS")
        print("="*80)
        print(f"\n📊 Approval Mode: {mode.upper()}")
        
        mode_desc = self.config.get("approval_mode", {}).get("available_modes", {})
        print(f"   {mode_desc.get(mode, 'Unknown mode')}")
        
        print("\n⚙️  Auto-Run Settings:")
        auto_run = self.config.get("auto_run_settings", {})
        for action, settings in auto_run.items():
            if settings.get("enabled"):
                status = "✅ AUTO" if settings.get("auto_approve") else "⚠️  PROMPT"
                print(f"   {status} {action}: {settings.get('description', 'N/A')}")
        
        print("\n🔔 Notifications:")
        notifications = self.config.get("notification_settings", {})
        for key, value in notifications.items():
            if key != "description":
                print(f"   {'✅' if value else '❌'} {key}")
        
        print("\n🚀 Quick Commands:")
        quick_cmds = self.config.get("quick_commands", {})
        for cmd_name, cmd_config in quick_cmds.items():
            status = "AUTO" if cmd_config.get("auto_approve") else "PROMPT"
            print(f"   [{status}] {cmd_name}: {cmd_config.get('description', 'N/A')}")
        
        print("\n" + "="*80)
    
    def interactive_setup(self):
        """Interactive setup wizard"""
        print("="*80)
        print("🔧 COPILOT AGENT SETUP WIZARD")
        print("="*80)
        
        print("\n1. Choose approval mode:")
        print("   a) AUTO - Fully automated, no prompts")
        print("   b) SEMI - Critical actions only")
        print("   c) MANUAL - Approve each action")
        
        choice = input("\nYour choice [a/b/c]: ").strip().lower()
        
        mode_map = {"a": "auto", "b": "semi", "c": "manual"}
        mode = mode_map.get(choice, "manual")
        
        self.set_approval_mode(mode)
        
        if mode == "semi":
            print("\n2. Configure auto-approval for each action:")
            auto_run = self.config.get("auto_run_settings", {})
            
            for action, settings in auto_run.items():
                default = "y" if settings.get("auto_approve") else "n"
                response = input(f"   Auto-approve '{action}'? [y/N] (default: {default}): ").strip().lower()
                if response:
                    settings["auto_approve"] = response in ["y", "yes"]
            
            self.save_config()
        
        print("\n✅ Setup complete!")
        self.show_settings()


def main():
    """CLI interface for copilot agent"""
    import sys
    
    agent = CopilotAgent()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 copilot_agent.py show              # Show current settings")
        print("  python3 copilot_agent.py setup             # Interactive setup")
        print("  python3 copilot_agent.py mode [auto|semi|manual]  # Set mode")
        print("  python3 copilot_agent.py run <command>     # Run quick command")
        print("  python3 copilot_agent.py run <command> -bg # Run in background")
        print("\nQuick commands:")
        for cmd in agent.config.get("quick_commands", {}).keys():
            print(f"  - {cmd}")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "show":
        agent.show_settings()
    
    elif command == "setup":
        agent.interactive_setup()
    
    elif command == "mode":
        if len(sys.argv) < 3:
            print("Error: mode requires argument: auto, semi, or manual")
            sys.exit(1)
        agent.set_approval_mode(sys.argv[2])
        agent.show_settings()
    
    elif command == "run":
        if len(sys.argv) < 3:
            print("Error: run requires command name")
            sys.exit(1)
        
        cmd_name = sys.argv[2]
        background = "-bg" in sys.argv or "--background" in sys.argv
        
        result = agent.run_command(cmd_name, background)
        
        if result["success"]:
            print("✅ Success!")
            if "message" in result:
                print(result["message"])
            if "log_file" in result:
                print(f"📄 Log: {result['log_file']}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
