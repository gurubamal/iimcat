# AI Conversation Logging for Quality Assurance

This document explains how to enable and use AI conversation logging to review the quality of AI responses.

## Overview

AI conversation logging captures both **requests** (prompts) and **responses** from all AI providers for quality assurance purposes. This allows you to:

- Review what was sent to the AI
- Analyze the AI's responses
- Identify patterns of good/bad responses
- Debug issues with AI analysis
- Improve prompts over time

## Quick Start

### Enable Logging

```bash
# Enable AI conversation logging
export AI_LOG_ENABLED=true

# Optional: Customize log location (default: ./logs/ai_conversations)
export AI_LOG_DIR=./qa_logs

# Optional: Choose log format (json, text, or both; default: both)
export AI_LOG_FORMAT=both

# Run your normal commands
./run_without_api.sh codex all.txt 18 10
# OR
./run_without_api.sh claude all.txt 18 10
```

### View Logs

```bash
# List all logged conversations
ls -lth logs/ai_conversations/

# View a specific conversation (text format)
cat logs/ai_conversations/20250128_143025_claude-cli_a3f2b1c8.txt

# View a specific conversation (JSON format)
cat logs/ai_conversations/20250128_143025_claude-cli_a3f2b1c8.json
```

## Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `AI_LOG_ENABLED` | `false` | Enable/disable AI conversation logging |
| `AI_LOG_DIR` | `./logs/ai_conversations` | Directory to store logs |
| `AI_LOG_FORMAT` | `both` | Log format: `json`, `text`, or `both` |
| `AI_LOG_MAX_PROMPT` | `5000` | Max characters to log from prompt (prevents huge files) |
| `AI_LOG_MAX_RESPONSE` | `10000` | Max characters to log from response |

## Log File Formats

### File Naming Convention

```
YYYYMMDD_HHMMSS_<provider>_<hash>.json
YYYYMMDD_HHMMSS_<provider>_<hash>.txt
```

Example: `20250128_143025_claude-cli_a3f2b1c8.json`

### Text Format (.txt)

Human-readable format for easy review:

```
================================================================================
AI CONVERSATION LOG
================================================================================
Conversation ID: a3f2b1c8e9d4f5a6...
Timestamp: 2025-01-28T14:30:25.123456
Provider: claude-cli
Prompt Length: 450 chars
Response Length: 850 chars

METADATA:
  model: sonnet
  timeout: 90
  bridge: claude_cli_bridge.py
  system_prompt_length: 523

--------------------------------------------------------------------------------
PROMPT:
--------------------------------------------------------------------------------
Analyze this stock news:
RELIANCE - Reports Q4 profit of ₹18,000 crores, up 12% YoY...

--------------------------------------------------------------------------------
RESPONSE:
--------------------------------------------------------------------------------
{
  "score": 85,
  "sentiment": "positive",
  "impact": "high",
  "catalysts": ["Strong profit growth", "Above estimates"],
  ...
}
================================================================================
```

### JSON Format (.json)

Machine-readable format for automated analysis:

```json
{
  "conversation_id": "a3f2b1c8e9d4f5a6...",
  "timestamp": "2025-01-28T14:30:25.123456",
  "provider": "claude-cli",
  "prompt": "Analyze this stock news:\nRELIANCE - Reports Q4 profit...",
  "response": "{\n  \"score\": 85,\n  \"sentiment\": \"positive\"...",
  "error": null,
  "metadata": {
    "model": "sonnet",
    "timeout": 90,
    "bridge": "claude_cli_bridge.py",
    "system_prompt_length": 523
  },
  "prompt_length": 450,
  "response_length": 850
}
```

## Provider-Specific Logging

### Claude CLI (`claude-cli`)

When using `./run_without_api.sh claude all.txt 18 10`:

- **Provider**: `claude-cli`
- **Metadata includes**: model, timeout, bridge script, system prompt length
- **Logs**: Full prompt with system prompt, raw CLI response

### Codex/Heuristic (`codex-heuristic`)

When using `./run_without_api.sh codex all.txt 18 10`:

- **Provider**: `codex-heuristic`
- **Metadata includes**: bridge script, type (heuristic_analysis), URLs fetched
- **Logs**: Enhanced prompt with fetched article content, heuristic analysis result

### Claude API (`claude`)

When using Claude API with `ANTHROPIC_API_KEY`:

- **Provider**: `claude`
- **Metadata includes**: model, temperature, max_tokens, API version
- **Logs**: Exact prompt sent to API, raw API response

### OpenAI API (`openai`)

When using OpenAI API with `OPENAI_API_KEY`:

- **Provider**: `openai`
- **Metadata includes**: model, temperature, max_tokens
- **Logs**: Exact prompt sent to API, raw API response

## Quality Assurance Workflows

### 1. Review All Conversations from a Run

```bash
# Enable logging
export AI_LOG_ENABLED=true

# Run analysis
./run_without_api.sh claude all.txt 18 10

# Review all conversations
ls -lth logs/ai_conversations/ | head -20

# Read specific ones
for f in logs/ai_conversations/*.txt; do
    echo "=== $f ==="
    cat "$f"
    echo ""
done
```

### 2. Find Errors

```bash
# Find all logs with errors (JSON format)
grep -l '"error": "[^n]' logs/ai_conversations/*.json

# View error details
for f in $(grep -l '"error": "[^n]' logs/ai_conversations/*.json); do
    echo "=== $f ==="
    jq '.error' "$f"
done
```

### 3. Analyze Response Quality

```bash
# Extract all scores from responses
for f in logs/ai_conversations/*.json; do
    echo -n "$(basename $f): "
    jq -r '.response | fromjson | .score' "$f" 2>/dev/null || echo "N/A"
done

# Find low-certainty responses
for f in logs/ai_conversations/*.json; do
    certainty=$(jq -r '.response | fromjson | .certainty' "$f" 2>/dev/null)
    if [ "$certainty" != "null" ] && [ "$certainty" -lt 50 ]; then
        echo "Low certainty ($certainty): $(basename $f)"
    fi
done
```

### 4. Compare Prompts and Responses

```bash
# Create a summary of all conversations
python3 << 'EOF'
import json
import glob

for log_file in sorted(glob.glob('logs/ai_conversations/*.json')):
    with open(log_file) as f:
        data = json.load(f)
        response = json.loads(data['response'])
        print(f"{data['provider']}: score={response.get('score', 'N/A')}, "
              f"certainty={response.get('certainty', 'N/A')}, "
              f"recommendation={response.get('recommendation', 'N/A')}")
EOF
```

## Log Analysis Tools

### Built-in Test/Summary Tool

```bash
# Test the logger and see summary
python3 ai_conversation_logger.py
```

Output:
```
AI Conversation Logger - Test Mode
================================================================================
✅ Logging is ENABLED
Log directory: ./logs/ai_conversations
Log format: both

✅ Test conversation logged to: logs/ai_conversations/20250128_143025_test_a3f2b1c8.json

Summary:
{
  "enabled": true,
  "log_directory": "./logs/ai_conversations",
  "total_conversations": 15,
  "log_format": "both",
  "by_provider": {
    "claude-cli": 8,
    "codex-heuristic": 5,
    "claude": 2
  }
}
```

### Custom Analysis Script

Create `analyze_logs.py`:

```python
#!/usr/bin/env python3
import json
import glob
from pathlib import Path

log_dir = Path('./logs/ai_conversations')

# Collect all logs
logs = []
for log_file in log_dir.glob('*.json'):
    with open(log_file) as f:
        data = json.load(f)
        try:
            response = json.loads(data['response'])
            logs.append({
                'file': log_file.name,
                'provider': data['provider'],
                'score': response.get('score', 0),
                'certainty': response.get('certainty', 0),
                'recommendation': response.get('recommendation', 'HOLD'),
                'timestamp': data['timestamp']
            })
        except:
            pass

# Sort by score
logs.sort(key=lambda x: x['score'], reverse=True)

# Display top 10
print("Top 10 Highest Scores:")
for i, log in enumerate(logs[:10], 1):
    print(f"{i}. {log['file']}: score={log['score']}, "
          f"certainty={log['certainty']}, rec={log['recommendation']}")
```

## Best Practices

### 1. Enable Logging During Development

```bash
# Add to your .bashrc or .env
export AI_LOG_ENABLED=true
export AI_LOG_DIR=./qa_logs
```

### 2. Periodic Review

- Review logs weekly to identify patterns
- Look for consistently low certainty scores
- Check if prompts are too vague or too specific
- Validate that the AI understands your domain

### 3. Log Rotation

```bash
# Archive old logs monthly
mkdir -p archives/$(date +%Y%m)
mv logs/ai_conversations/*.json archives/$(date +%Y%m)/
mv logs/ai_conversations/*.txt archives/$(date +%Y%m)/
```

### 4. Compare Providers

```bash
# Run the same analysis with different providers
export AI_LOG_ENABLED=true

./run_without_api.sh codex all.txt 18 10
./run_without_api.sh claude all.txt 18 10

# Compare results
diff logs/ai_conversations/*codex*.txt logs/ai_conversations/*claude*.txt
```

## Troubleshooting

### Logs Not Being Created

```bash
# Check if logging is enabled
echo $AI_LOG_ENABLED  # Should be "true"

# Check if directory exists
ls -ld logs/ai_conversations/  # Should exist

# Check permissions
mkdir -p logs/ai_conversations
chmod 755 logs/ai_conversations
```

### Log Files Too Large

```bash
# Reduce max lengths
export AI_LOG_MAX_PROMPT=2000
export AI_LOG_MAX_RESPONSE=3000

# Or use JSON-only format
export AI_LOG_FORMAT=json
```

### Performance Impact

Logging has minimal performance impact:
- JSON write: ~10ms per conversation
- Text write: ~15ms per conversation
- No impact on AI API calls themselves

Disable logging for maximum performance:
```bash
export AI_LOG_ENABLED=false
```

## Integration with Existing Scripts

All existing scripts now support logging automatically:

- `./run_without_api.sh` - ✅ Supports logging
- `./optimal_scan_config.sh` - ✅ Supports logging
- `python3 realtime_ai_news_analyzer.py` - ✅ Supports logging
- `python3 run_swing_paths.py` - ✅ Supports logging (via analyzer)

No code changes needed - just set the environment variables!

## Summary

1. **Enable logging**: `export AI_LOG_ENABLED=true`
2. **Run your commands**: `./run_without_api.sh codex all.txt 18 10`
3. **Review logs**: `ls -lth logs/ai_conversations/`
4. **Analyze quality**: Use the tools and scripts provided above
5. **Improve prompts**: Based on your findings

For questions or issues, check the implementation in `ai_conversation_logger.py`.
