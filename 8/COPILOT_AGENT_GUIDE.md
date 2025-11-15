# 🤖 Copilot Agent Auto-Approval Guide

## Quick Start

### 1. Set to Full Auto Mode (No Prompts)
```bash
python3 copilot_agent.py mode auto
```

### 2. Set to Semi-Auto Mode (Critical Only)
```bash
python3 copilot_agent.py mode semi
```

### 3. Set to Manual Mode (All Prompts)
```bash
python3 copilot_agent.py mode manual
```

---

## Interactive Setup

Run the setup wizard:
```bash
python3 copilot_agent.py setup
```

This will guide you through:
1. Choosing approval mode
2. Configuring individual action auto-approvals
3. Setting notification preferences

---

## View Current Settings

```bash
python3 copilot_agent.py show
```

Output example:
```
🤖 COPILOT AGENT SETTINGS
==========================================
📊 Approval Mode: AUTO
   Fully automated - no user prompts

⚙️  Auto-Run Settings:
   ✅ AUTO news_collection: Automatically fetch news
   ✅ AUTO ai_analysis: Automatically run AI analysis
   ✅ AUTO enhanced_scoring: Auto apply filters
   ✅ AUTO technical_screening: Auto run screener
   ✅ AUTO config_updates: Auto apply config changes
```

---

## Quick Commands

### Full Enhanced Scan (Auto)
```bash
python3 copilot_agent.py run scan_now
```

### Quick Analysis (Auto)
```bash
python3 copilot_agent.py run quick_analysis
```

### Fresh News Scan (Auto)
```bash
python3 copilot_agent.py run fresh_scan
```

### Monitor Running Scan
```bash
python3 copilot_agent.py run monitor
```

### Run in Background
```bash
python3 copilot_agent.py run scan_now -bg
python3 copilot_agent.py run fresh_scan --background
```

---

## Configuration File

Location: `configs/copilot_agent_config.json`

### Approval Modes

**AUTO Mode:**
- No prompts
- All actions auto-approved
- Fastest execution
- Use when: You trust the system completely

**SEMI Mode:**
- Critical actions only
- Customize per-action approval
- Balance of speed and control
- Use when: You want oversight on important decisions

**MANUAL Mode:**
- All prompts shown
- User approval required
- Slowest but most controlled
- Use when: Learning the system or testing

---

## Auto-Run Settings

Each action can be individually configured:

```json
{
  "news_collection": {
    "enabled": true,
    "auto_approve": true,
    "hours_back": 48,
    "max_articles": 10
  },
  "ai_analysis": {
    "enabled": true,
    "auto_approve": true,
    "path": "ai",
    "top_picks": 50
  },
  "enhanced_scoring": {
    "enabled": true,
    "auto_approve": true,
    "min_certainty": 40,
    "min_magnitude_cr": 50
  }
}
```

---

## Integration with Existing Scripts

The existing scripts already support auto-flags:

### run_swing_paths.py
```bash
# With auto-approval
python3 run_swing_paths.py --path ai --auto-apply-config --auto-screener

# Manual approval
python3 run_swing_paths.py --path ai
```

### optimal_scan_config.sh
Already configured for auto-run:
```bash
./optimal_scan_config.sh  # Fully automated
```

---

## Environment Variables

You can also control via environment variables:

```bash
# Set auto mode
export COPILOT_MODE=auto

# Run commands
./optimal_scan_config.sh

# Unset
unset COPILOT_MODE
```

---

## Programmatic Usage

### Python API
```python
from copilot_agent import CopilotAgent

# Initialize
agent = CopilotAgent()

# Check if auto-approved
if agent.is_auto_approved("news_collection"):
    # Run without prompting
    pass

# Set mode
agent.set_approval_mode("auto")

# Run command
result = agent.run_command("scan_now", background=True)
print(result["pid"])  # Background process ID
```

---

## Safety Limits

Even in AUTO mode, safety limits apply:

- Max scan time: 60 minutes
- Max file size: 100 MB
- Max stocks per run: 3000

These prevent runaway processes.

---

## Notification Settings

Control what gets displayed:

```json
{
  "notification_settings": {
    "show_progress": true,      # Show progress updates
    "show_warnings": true,       # Show warning messages
    "show_rejections": true,     # Show rejected stocks
    "verbose_mode": false        # Detailed output
  }
}
```

---

## Scheduled Scans (Optional)

Enable scheduled automatic scans:

```json
{
  "schedule_settings": {
    "enabled": true,
    "daily_scan_time": "09:00",
    "weekend_scans": true,
    "scan_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
  }
}
```

Then setup cron:
```bash
crontab -e
# Add:
0 9 * * 1-5 cd /home/vagrant/R/essentials && python3 copilot_agent.py run scan_now -bg
```

---

## Common Use Cases

### 1. Daily Morning Scan (Automated)
```bash
# Setup
python3 copilot_agent.py mode auto

# Create cron job
crontab -e
# Add: 0 9 * * * cd /home/vagrant/R/essentials && ./optimal_scan_config.sh > daily_scan.log 2>&1
```

### 2. On-Demand Analysis (Semi-Auto)
```bash
# Setup
python3 copilot_agent.py mode semi

# Run when needed
python3 copilot_agent.py run quick_analysis
```

### 3. Testing/Learning (Manual)
```bash
# Setup
python3 copilot_agent.py mode manual

# Each action will prompt
./optimal_scan_config.sh
```

---

## Troubleshooting

### "Config not found" error
```bash
# Recreate config
python3 copilot_agent.py setup
```

### Commands not auto-running
```bash
# Check mode
python3 copilot_agent.py show

# Set to auto
python3 copilot_agent.py mode auto
```

### Background process stuck
```bash
# Find PID
ps aux | grep enhanced_india

# Kill if needed
kill <PID>
```

---

## Best Practices

1. **Start with SEMI mode** - Learn what each action does
2. **Move to AUTO mode** - Once comfortable with the system
3. **Use background mode** - For long scans (`-bg` flag)
4. **Check logs** - When running in background
5. **Review rejected stocks** - Learn from filtered results
6. **Set up schedules** - For regular automated scans

---

## Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `show` | Display settings | `python3 copilot_agent.py show` |
| `setup` | Interactive wizard | `python3 copilot_agent.py setup` |
| `mode <type>` | Set approval mode | `python3 copilot_agent.py mode auto` |
| `run <cmd>` | Run quick command | `python3 copilot_agent.py run scan_now` |
| `run <cmd> -bg` | Run in background | `python3 copilot_agent.py run scan_now -bg` |

---

## Files Created

- `configs/copilot_agent_config.json` - Configuration file
- `copilot_agent.py` - Management script
- `COPILOT_AGENT_GUIDE.md` - This guide

---

## Examples

### Example 1: Full Auto Setup
```bash
# Set to auto mode
python3 copilot_agent.py mode auto

# Run full scan (no prompts)
./optimal_scan_config.sh

# Or use copilot agent
python3 copilot_agent.py run scan_now -bg

# Monitor
tail -f copilot_run_*.log
```

### Example 2: Semi-Auto Setup
```bash
# Interactive setup
python3 copilot_agent.py setup
# Choose 'b' for semi-auto
# Select which actions to auto-approve

# Run analysis
python3 copilot_agent.py run quick_analysis
```

### Example 3: Scheduled Daily Scan
```bash
# Set auto mode
python3 copilot_agent.py mode auto

# Add to crontab
crontab -e
# Add:
0 9 * * 1-5 cd /home/vagrant/R/essentials && python3 copilot_agent.py run scan_now -bg

# Check logs later
ls -lt copilot_run_*.log | head -1
```

---

**Created:** 2025-10-14  
**Status:** Production Ready ✅  
**Integration:** Complete ✅

**Just run: `python3 copilot_agent.py mode auto` to enable full automation!**
