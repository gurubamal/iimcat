# 🤖 Copilot Agent - Quick Reference Card

## ⚡ One-Line Commands

```bash
# Enable full auto mode (NO PROMPTS)
python3 copilot_agent.py mode auto

# Run full scan automatically
python3 copilot_agent.py run scan_now

# Run in background
python3 copilot_agent.py run scan_now -bg

# Check settings
python3 copilot_agent.py show
```

---

## 🎯 Three Modes

| Mode | Prompts | Use Case |
|------|---------|----------|
| **AUTO** | None | Fully automated, trusted system |
| **SEMI** | Critical only | Balance speed & control |
| **MANUAL** | All actions | Learning or testing |

**Set mode:**
```bash
python3 copilot_agent.py mode [auto|semi|manual]
```

---

## 🚀 Quick Commands

| Command | What It Does |
|---------|--------------|
| `scan_now` | Full enhanced scan (all features) |
| `quick_analysis` | Fast AI analysis on latest news |
| `fresh_scan` | Fetch fresh news + analyze |
| `monitor` | Monitor running scans |

**Usage:**
```bash
python3 copilot_agent.py run <command>
python3 copilot_agent.py run <command> -bg  # background
```

---

## 📋 Existing Script Flags

Scripts already have auto-run support:

```bash
# run_swing_paths.py
python3 run_swing_paths.py --path ai --auto-apply-config --auto-screener

# optimal_scan_config.sh (already auto)
./optimal_scan_config.sh
```

---

## 🔧 Setup Wizard

```bash
python3 copilot_agent.py setup
```

Interactive configuration:
1. Choose mode (auto/semi/manual)
2. Configure per-action approvals
3. Save settings

---

## 📊 What Gets Auto-Approved

When in **AUTO mode**:
- ✅ News collection (48h window, 10 articles/stock)
- ✅ AI analysis (entity resolution, ranking)
- ✅ Enhanced scoring (certainty, fake rally detection)
- ✅ Technical screening (institutional filters)
- ✅ Config updates (recommended changes)
- ✅ Report generation (CSV, MD, JSON)

---

## 🛡️ Safety Limits

Even in AUTO mode:
- Max scan time: 60 minutes
- Max file size: 100 MB
- Max stocks: 3000 per run

---

## 📱 Integration Examples

### Example 1: Morning Automated Scan
```bash
# One-time setup
python3 copilot_agent.py mode auto

# Add to crontab
0 9 * * 1-5 cd /home/vagrant/R/essentials && python3 copilot_agent.py run scan_now -bg
```

### Example 2: On-Demand Analysis
```bash
python3 copilot_agent.py run quick_analysis
```

### Example 3: Monitor Background Scan
```bash
python3 copilot_agent.py run scan_now -bg
python3 copilot_agent.py run monitor
```

---

## 📁 Files

- **Config:** `configs/copilot_agent_config.json`
- **Script:** `copilot_agent.py`
- **Guide:** `COPILOT_AGENT_GUIDE.md` (detailed docs)

---

## 🔍 Troubleshooting

**Not auto-running?**
```bash
python3 copilot_agent.py show  # Check mode
python3 copilot_agent.py mode auto  # Set to auto
```

**Background process stuck?**
```bash
ps aux | grep enhanced_india  # Find PID
kill <PID>  # Stop it
```

---

## ✅ Current Status

**Your system is configured for:**
- Approval Mode: AUTO ✅
- All actions: AUTO-APPROVED ✅
- Enhanced scoring: ACTIVE ✅
- Fake rally detection: ACTIVE ✅

**Just run: `python3 copilot_agent.py run scan_now`**

---

Created: 2025-10-14
Status: Ready to use ✅
