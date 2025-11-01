# AI Conversation Logging - Quick Start Guide

## What This Does

Logs all AI conversations (requests + responses) to files so you can review them later for quality assurance.

## 1-Minute Setup

```bash
# Enable logging for your current session
export AI_LOG_ENABLED=true

# Run your normal commands
./run_without_api.sh codex all.txt 18 10
# OR
./run_without_api.sh claude all.txt 18 10

# View what was logged
./ai_log_helper.sh list
```

That's it! All AI conversations are now being logged.

## View Your Logs

```bash
# Show status and recent logs
./ai_log_helper.sh status

# List all logs
./ai_log_helper.sh list

# View a specific log
./ai_log_helper.sh view claude

# See summary statistics
./ai_log_helper.sh summary
```

## Where Are Logs Stored?

**Default location**: `./logs/ai_conversations/`

Each conversation creates two files:
- `.json` - Machine-readable format
- `.txt` - Human-readable format

**Example files**:
```
20251028_143025_claude-cli_a3f2b1c8.json
20251028_143025_claude-cli_a3f2b1c8.txt
```

## What Gets Logged?

For each AI call, you get:

1. **Full Prompt** - Exactly what was sent to the AI
2. **Full Response** - Exactly what the AI returned
3. **Metadata** - Model, temperature, timeout, provider
4. **Errors** - If anything went wrong
5. **Timestamp** - When the call happened

## Example Log (Text Format)

```
================================================================================
AI CONVERSATION LOG
================================================================================
Conversation ID: a3f2b1c8...
Timestamp: 2025-10-28T14:30:25
Provider: claude-cli
Prompt Length: 450 chars
Response Length: 850 chars

METADATA:
  model: sonnet
  timeout: 90
  bridge: claude_cli_bridge.py

--------------------------------------------------------------------------------
PROMPT:
--------------------------------------------------------------------------------
Analyze this stock news:
RELIANCE - Reports Q4 profit of ₹18,000 crores, up 12% YoY
**URL**: https://economictimes.com/...

Provide your analysis in JSON format...

--------------------------------------------------------------------------------
RESPONSE:
--------------------------------------------------------------------------------
{
  "score": 85,
  "sentiment": "positive",
  "impact": "high",
  "catalysts": ["Strong profit growth", "Beat estimates"],
  "certainty": 90,
  "recommendation": "BUY",
  "reasoning": "Solid profit growth with earnings beat..."
}
================================================================================
```

## Configuration Options

```bash
# Required: Enable logging
export AI_LOG_ENABLED=true

# Optional: Custom log directory
export AI_LOG_DIR=./my_qa_logs

# Optional: Log format (json, text, or both)
export AI_LOG_FORMAT=both

# Optional: Limit log sizes
export AI_LOG_MAX_PROMPT=5000
export AI_LOG_MAX_RESPONSE=10000
```

## Permanent Setup

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# AI Conversation Logging
export AI_LOG_ENABLED=true
export AI_LOG_DIR=./logs/ai_conversations
export AI_LOG_FORMAT=both
```

Or use the helper:
```bash
./ai_log_helper.sh enable
source <(./ai_log_helper.sh env)
```

## Common Tasks

### Compare AI Providers

```bash
export AI_LOG_ENABLED=true

# Run with Codex
./run_without_api.sh codex all.txt 18 10

# Run with Claude
./run_without_api.sh claude all.txt 18 10

# Compare the logs
./ai_log_helper.sh summary
```

### Find Low-Quality Responses

```bash
# View summary to see average scores
./ai_log_helper.sh summary

# Manually review low scores
for f in logs/ai_conversations/*.json; do
  score=$(jq -r '.response | fromjson | .score' "$f" 2>/dev/null)
  if [ "$score" -lt 50 ] 2>/dev/null; then
    echo "Low score ($score): $(basename $f)"
  fi
done
```

### Archive Old Logs

```bash
# Archive and clean (with confirmation)
./ai_log_helper.sh clean

# Or manually
mkdir -p archives/$(date +%Y%m)
mv logs/ai_conversations/* archives/$(date +%Y%m)/
```

## Supported AI Providers

All providers are automatically logged:

| Provider | When Used | Logged As |
|----------|-----------|-----------|
| Claude CLI | `./run_without_api.sh claude` | `claude-cli` |
| Codex/Heuristic | `./run_without_api.sh codex` | `codex-heuristic` |
| Claude API | With `ANTHROPIC_API_KEY` | `claude` |
| OpenAI API | With `OPENAI_API_KEY` | `openai` |

## Performance Impact

**Minimal** - Each log write takes ~10-15ms
- No impact on AI API call speed
- Small disk space usage (~1-5 KB per conversation)
- Disable for maximum performance: `export AI_LOG_ENABLED=false`

## Troubleshooting

### Logs not being created?

```bash
# Check if enabled
echo $AI_LOG_ENABLED  # Should show "true"

# Test the logger
./ai_log_helper.sh test

# Check permissions
ls -ld logs/ai_conversations
```

### Can't find a specific log?

```bash
# List all logs
./ai_log_helper.sh list

# Search for a pattern
ls logs/ai_conversations/*claude*

# View most recent
ls -lt logs/ai_conversations/ | head -3
```

## Helper Commands Reference

```bash
./ai_log_helper.sh status    # Show current status
./ai_log_helper.sh enable    # Enable logging
./ai_log_helper.sh disable   # Disable logging
./ai_log_helper.sh list      # List all logs
./ai_log_helper.sh view X    # View specific log
./ai_log_helper.sh summary   # Statistics
./ai_log_helper.sh clean     # Archive & clean
./ai_log_helper.sh test      # Test logging
```

## Next Steps

1. **Enable logging** (see 1-Minute Setup above)
2. **Run your analysis** as normal
3. **Review the logs** periodically for quality
4. **Improve your prompts** based on what you learn

For detailed documentation, see: `AI_CONVERSATION_LOGGING.md`

For implementation details, see: `ai_conversation_logger.py`

---

**Questions?** Check the full documentation or run `./ai_log_helper.sh help`
