# AI-Driven Health Data Collection - Integration Guide

## Overview

A completely dynamic, AI-powered system that:
- ✅ Uses Claude AI to generate search queries (NO hardcoding)
- ✅ Searches the web for recent financial data
- ✅ Uses Claude AI to extract metrics from results
- ✅ Uses Claude AI to analyze financial health
- ✅ Returns structured health reports
- ✅ Detects profit/loss status accurately

**Key Feature: ZERO hardcoding - all queries and extractions are AI-generated and flexible**

---

## Architecture

### 1. **Claude Health AI Client** (`claude_health_ai_client.py`)
- Handles all Claude API/CLI calls
- Generates search queries dynamically
- Extracts metrics from search results
- Analyzes health status

### 2. **Health Data Collector** (`ai_health_data_collector.py`)
- Orchestrates the data collection process
- Uses AI to generate queries
- Executes web searches
- Uses AI to extract and analyze data
- Returns structured `StockHealthReport`

### 3. **Integration Module** (`health_data_integration.py`)
- Integrates with realtime_ai_news_analyzer.py
- Provides high-level API for analyzer
- Handles caching
- Generates warnings for critical health issues

---

## How It Works

```
┌─────────────────────────────────────────┐
│ 1. Analyzer Asks: Get health data for BLACKBUCK
│                          │
│                          ▼
├─────────────────────────────────────────┤
│ 2. AI Generates Search Queries (Claude)
│    - "BLACKBUCK Q2 FY26 quarterly results"
│    - "BLACKBUCK latest profit loss financial"
│    - "BLACKBUCK consecutive loss quarters"
│    - (6-8 unique, optimal queries)
│                          │
│                          ▼
├─────────────────────────────────────────┤
│ 3. Execute Web Searches
│    - Search for each query
│    - Get raw search results
│    - Collect 6-8 different sources
│                          │
│                          ▼
├─────────────────────────────────────────┤
│ 4. AI Extracts Metrics (Claude)
│    From raw search results, extract:
│    - Quarterly profit/loss: ₹29 Cr (Q2 FY26)
│    - Revenue: ₹151 Cr
│    - YoY growth: -15.3%
│    - Health status: warning
│    - Consecutive losses: 2 quarters
│                          │
│                          ▼
├─────────────────────────────────────────┤
│ 5. AI Analyzes Health (Claude)
│    - Is company profitable? NO
│    - Risk level? HIGH
│    - Warning flags? Yes - consecutive losses
│    - Data consistency: 95%
│                          │
│                          ▼
├─────────────────────────────────────────┤
│ 6. Return Structured Report
│    StockHealthReport with:
│    - is_profitable: False
│    - latest_profit_loss: "Loss of ₹33.7 Cr"
│    - health_status: "critical"
│    - warning_flags: ["5 consecutive losses"]
│    - ai_analysis: "Detailed analysis..."
│                          │
│                          ▼
├─────────────────────────────────────────┤
│ 7. Integrate with Analysis
│    - Add health data to stock analysis
│    - Override scores if critical
│    - Generate warnings
│    - Flag for manual review
└─────────────────────────────────────────┘
```

---

## Integration with Analyzer

### Step 1: Add imports to `realtime_ai_news_analyzer.py`

```python
from claude_health_ai_client import create_client as create_health_client
from health_data_integration import integrate_with_analyzer
```

### Step 2: Initialize in `RealTimeAINewsAnalyzer.__init__`

```python
def __init__(self, ...):
    # ... existing code ...

    # Initialize health data collector
    health_ai_client = create_health_client(use_cli=True)  # Use Claude CLI if available
    self.health_integration = integrate_with_analyzer(self, health_ai_client)
```

### Step 3: Call in `analyze_ticker` method

```python
def analyze_ticker(self, ticker, headline, full_text, url):
    # ... existing analysis code ...

    # Get analysis result
    result = self.analyze_news_instant(ticker, headline, full_text, url)

    # NEW: Add health data
    result = self.health_integration.update_analysis_with_health(result, ticker)

    # NEW: Check for health warnings
    health_warning = self.health_integration.generate_health_warning(ticker, result)
    if health_warning:
        logger.warning(f"🚨 HEALTH WARNING: {health_warning}")

    return result
```

### Step 4: Save health data to CSV

```python
# In save_results() method, add new columns:
writer.writerow([
    # ... existing columns ...
    # Health data columns (NEW):
    'health_is_profitable',
    'health_profit_loss',
    'health_profit_loss_period',
    'health_status',
    'health_consecutive_losses',
    'health_warning_flags',
    'health_ai_analysis'
])

# Write health data:
health_data = result.get('health_data', {})
writer.writerow([
    # ... existing data ...
    # Health data:
    ('TRUE' if health_data.get('is_profitable') else 'FALSE'),
    health_data.get('latest_profit_loss', ''),
    health_data.get('profit_loss_period', ''),
    health_data.get('health_status', ''),
    health_data.get('consecutive_loss_quarters', '0'),
    '; '.join(health_data.get('warning_flags', [])),
    health_data.get('ai_analysis', '')[:200]
])
```

---

## Example Output

### Screen Display

```
🔍 HEALTH DATA COLLECTION
─────────────────────────────────────────

BLACKBUCK:
  Searching for quarterly results...
  🔎 "BLACKBUCK Q2 FY26 quarterly results profit loss"
  🔎 "BLACKBUCK latest earnings financial 2025"
  🔎 "BLACKBUCK revenue growth recent quarters"
  ...

  Extracting metrics from search results...
  ✅ Found: Quarterly profit ₹29 Cr (Q2 FY26)
  ✅ Found: Revenue ₹151 Cr
  ✅ Found: YoY growth -15.3%
  ✅ Found: Health status: warning

  Analyzing health...
  ✅ Analysis: Company profitable in Q2, but recent quarters show losses
  Health status: WARNING
  Risk level: MEDIUM

  Summary:
  - Is profitable: FALSE (overall)
  - Latest: Profit of ₹29 Cr (Q2 FY26)
  - Health: WARNING
  - Consecutive losses: 2 quarters
```

### CSV Output

```
ticker,health_is_profitable,health_profit_loss,health_status,health_warning_flags
BLACKBUCK,FALSE,"Loss ₹33.7 Cr",warning,"Recent losses | Mixed results"
IDEAFORGE,FALSE,"Loss ₹19.62 Cr",critical,"5 consecutive losses | Revenue -85% YoY"
SBIN,TRUE,"Profit ₹1,234 Cr",healthy,""
```

### JSON Output (health_data field)

```json
{
  "ticker": "BLACKBUCK",
  "health_data": {
    "is_profitable": false,
    "latest_profit_loss": "Loss of ₹33.7 Cr",
    "profit_loss_period": "Q1 FY26",
    "latest_revenue": "₹159.56 Cr",
    "revenue_period": "Q1 FY26",
    "yoy_growth": -62.3,
    "health_status": "warning",
    "consecutive_loss_quarters": 2,
    "data_consistency": 0.92,
    "warning_flags": [
      "Recent quarterly losses despite revenue growth",
      "Q1 loss: ₹33.7 Cr",
      "Monitor profitability trend"
    ],
    "collection_time": "2025-11-15T03:05:56.000Z",
    "ai_analysis": "Company shows strong revenue growth (110% QoQ) but is currently unprofitable due to high operating expenses exceeding revenue growth..."
  }
}
```

---

## NO HARDCODING - Fully Dynamic

### Example: Different Search Queries for Different Stocks

For **BLACKBUCK** (transportation/logistics):
```
AI generates:
- "BLACKBUCK quarterly results FY26"
- "BlackBuck profit loss recent quarters"
- "BLACKBUCK earnings revenue trend"
- Etc. (6-8 unique queries)
```

For **IDEAFORGE** (drone/tech):
```
AI generates:
- "IDEAFORGE Q2 FY26 quarterly results"
- "ideaForge Technology losses revenue decline"
- "IDEAFORGE financial health latest results"
- Etc. (6-8 unique queries)
```

For **RELIANCE** (conglomerate):
```
AI generates:
- "RELIANCE Q2 results profit earnings"
- "RELIANCE consolidated quarterly results"
- "RIL financial performance latest quarter"
- Etc. (6-8 unique queries)
```

**Each stock gets optimal, AI-generated queries** - NOT hardcoded!

---

## Features

### 1. Dynamic Query Generation
- AI creates optimal search queries for each stock
- Queries adapt to company type, sector, size
- Multiple queries ensure comprehensive data

### 2. Multi-source Data Collection
- Searches multiple financial sources
- Cross-references data across sources
- Assigns confidence scores to each data point

### 3. Intelligent Metric Extraction
- AI extracts metrics from raw search results
- Handles different formats (₹Cr, $M, percentages)
- Assigns confidence levels (0-1)

### 4. Health Status Analysis
- Determines: healthy / warning / critical
- Identifies consecutive loss quarters
- Calculates data consistency score
- Generates human-readable reasoning

### 5. Warning System
- Flags critical financial issues
- Detects revenue collapse (>50% decline)
- Identifies profitability problems
- Alerts on consecutive losses

---

## Usage Examples

### Quick Usage

```python
from health_data_integration import integrate_with_analyzer
from claude_health_ai_client import create_client

# Initialize
ai_client = create_client(use_cli=True)
health_integration = integrate_with_analyzer(analyzer, ai_client)

# Get health data
health_report = health_integration.get_health_data("BLACKBUCK")
print(f"Is profitable: {health_report.is_profitable}")
print(f"Health status: {health_report.health_status}")
print(f"Warning flags: {health_report.warning_flags}")

# Update analysis
analysis = {"score": 75, "sentiment": "bullish"}
analysis = health_integration.update_analysis_with_health(analysis, "BLACKBUCK")

# Generate warning
warning = health_integration.generate_health_warning("BLACKBUCK", analysis)
if warning:
    print(f"⚠️  {warning}")
```

### Advanced Usage

```python
from ai_health_data_collector import AIHealthDataCollector
from claude_health_ai_client import create_client

# Initialize with custom web search
def my_web_search(query):
    # Custom implementation
    return search_results

collector = AIHealthDataCollector(ai_client=create_client())
collector.set_search_function(my_web_search)

# Collect health data
report = collector.collect_health_data("BLACKBUCK", "Blackbuck Ltd")

# Access detailed data
print(f"All data points: {len(report.all_data_points)}")
for dp in report.all_data_points:
    print(f"  {dp.metric}: {dp.value} {dp.unit} (confidence: {dp.confidence})")
```

---

## Data Flow

```
Analyzer
  │
  ├─> Health Integration
  │     │
  │     ├─> Get Health Data (cache check)
  │     │     │
  │     │     ├─> Health Data Collector
  │     │     │     │
  │     │     │     ├─> Claude: Generate Queries
  │     │     │     │
  │     │     │     ├─> Web Search (6-8 queries)
  │     │     │     │
  │     │     │     ├─> Claude: Extract Metrics
  │     │     │     │
  │     │     │     ├─> Claude: Analyze Health
  │     │     │     │
  │     │     │     └─> Build Report
  │     │     │
  │     │     └─> Cache Result
  │     │
  │     └─> Update Analysis + Generate Warnings
  │
  └─> Save to CSV + Display
```

---

## Benefits

✅ **Dynamic**: No hardcoding - AI generates all queries and extractions
✅ **Accurate**: Cross-references multiple sources
✅ **Flexible**: Works with any stock, any sector
✅ **Intelligent**: AI understands context and adapts
✅ **Transparent**: Confidence scores and sources provided
✅ **Integrated**: Seamlessly works with existing analyzer
✅ **Cached**: Avoids redundant API calls
✅ **Structured**: Returns well-defined data structures

---

## Integration Checklist

- [ ] Add `claude_health_ai_client.py` to codebase
- [ ] Add `ai_health_data_collector.py` to codebase
- [ ] Add `health_data_integration.py` to codebase
- [ ] Update `realtime_ai_news_analyzer.py` imports
- [ ] Initialize health integration in `__init__`
- [ ] Call health data collection in `analyze_ticker`
- [ ] Add health columns to CSV output
- [ ] Test with BLACKBUCK, IDEAFORGE
- [ ] Verify warnings are generated for loss-making stocks
- [ ] Document in README

---

## Testing

```bash
# Test the health data collector
python3 ai_health_data_collector.py

# Test the integration
python3 health_data_integration.py

# Test with analyzer
./run_without_api.sh claude just.txt 8 10 1
# Should now include health data in output
```

---

## Next Steps

1. Integrate with analyzer
2. Test with real stocks (BLACKBUCK, IDEAFORGE, SBIN, etc.)
3. Verify accuracy against internet sources
4. Monitor for false positives/negatives
5. Adjust AI prompts if needed
6. Add health data to CSV export
7. Display health data in final report

