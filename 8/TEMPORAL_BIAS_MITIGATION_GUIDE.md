# Temporal Bias Mitigation Guide for AI-Driven Stock Analysis

## Executive Summary

This document provides guidance for identifying and mitigating temporal bias in AI-driven financial analysis systems that process real-time data using Large Language Models (LLMs) with outdated training data.

**Problem**: When an LLM with a knowledge cutoff date (e.g., April 2024) analyzes recent financial data (8-18 hours old), it may misinterpret current events by applying outdated knowledge from its training data, leading to incorrect stock rankings or analysis.

**Solution**: A diagnostic-first approach that validates the problem exists, then implements targeted mitigations through prompt engineering and selective data timestamping.

**Target System**: Stock analysis pipeline using Claude Sonnet via `run_without_api.sh` script, processing data from `all.txt` with configurable time windows.

---

## Table of Contents

1. [Understanding Temporal Bias](#understanding-temporal-bias)
2. [Diagnostic Methodology](#diagnostic-methodology)
3. [Mitigation Strategies](#mitigation-strategies)
4. [Implementation Guide](#implementation-guide)
5. [Validation and Testing](#validation-and-testing)
6. [Operational Monitoring](#operational-monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Appendices](#appendices)

---

## 1. Understanding Temporal Bias

### 1.1 What is Temporal Bias?

Temporal bias occurs when an AI model trained on historical data (with a knowledge cutoff date) misinterprets or contradicts current information due to conflicts with its training data.

### 1.2 Manifestations in Financial Analysis

**Type A: Non-Recognition of Recency**
- AI treats current data as historical
- Outputs use past tense for recent events
- Model expresses uncertainty about "future" events that already occurred

**Type B: Outdated Knowledge Application**
- AI contradicts provided current data with stale training knowledge
- References outdated facts (former executives, old regulations, historical market conditions)
- Applies obsolete market dynamics or company information

**Type C: Mixed/Subtle Bias**
- Correct analysis with occasional anachronistic references
- Hedging language suggesting uncertainty about provided data
- Ranking discrepancies when recent events contradict training data patterns

### 1.3 Impact on Stock Analysis

- **Stock Rankings**: Misranking due to outdated company information or market conditions
- **Risk Assessment**: Incorrect risk profiles based on obsolete regulatory or competitive landscapes
- **Sentiment Analysis**: Misinterpreting news sentiment through outdated context
- **Event Impact**: Underestimating or overestimating impact of recent events

### 1.4 Root Cause Distinction

**Before assuming AI temporal bias, verify:**

| Scenario | Root Cause | Solution |
|----------|------------|----------|
| Input data is actually stale (days/weeks old) | Upstream data pipeline | Fix data collection, not AI prompts |
| Input data is fresh but lacks timestamps | Data formatting | Add explicit temporal markers |
| Input data is fresh with dates, but AI ignores them | AI temporal bias | Prompt engineering + reinforcement |
| AI correctly processes timestamps but applies outdated knowledge anyway | Training data conflict | Context prioritization prompts |

---

## 2. Diagnostic Methodology

### 2.1 Phase 1: System Understanding (Discovery)

**Objectives:**
- Map complete data flow from input to AI to output
- Locate prompt construction code
- Verify AI integration method
- Validate parameter meanings

**Actions:**
1. Read `TECHNICAL_ARCHITECTURE.md` for system design overview
2. Examine `run_without_api.sh` to understand:
   - How Claude is invoked (API, wrapper, etc.)
   - Parameter meanings (e.g., `8` = hours of data, `10` = batch size)
   - Prompt assembly mechanism
3. Locate actual prompt template files or code generators
4. Document data flow diagram

**Validation Checklist:**
- [ ] Complete data flow documented from `all.txt` → Claude → output
- [ ] Prompt construction code located and understood
- [ ] Claude integration method confirmed
- [ ] All script parameters meanings verified
- [ ] Current prompt templates inventoried

### 2.2 Phase 2: Input Data Validation

**Objectives:**
- Verify input data is actually fresh (8-18 hours old)
- Check for existing temporal markers
- Rule out upstream data staleness

**Actions:**
1. Examine `all.txt` structure and content
2. Verify timestamps or date references in data
3. Validate timestamps show data is from expected time window
4. Cross-reference sample news items with known recent events

**Validation Checklist:**
- [ ] `all.txt` exists and contains expected data format
- [ ] Data includes timestamps or date markers
- [ ] Timestamps confirm data is from last 8-18 hours (not older)
- [ ] Sample verification against known recent events confirms freshness
- [ ] Temporal context (dates, "today", relative times) present or absent documented

**Decision Point:** If data is stale, STOP and fix data pipeline before proceeding.

### 2.3 Phase 3: Temporal Bias Detection

**Objectives:**
- Confirm temporal bias exists in production outputs
- Categorize bias type (A, B, or C)
- Document specific manifestations
- Assess severity and impact

**Actions:**
1. Collect 2-3 recent production output files
2. Analyze for temporal bias indicators:
   - Outdated facts (old executives, regulations, company info)
   - Contradictions between AI output and provided data
   - Hedging or uncertainty about recent data
   - Past tense usage for current events
   - References to "future" events that already occurred
3. Categorize bias type
4. Document specific examples with context

**Temporal Bias Indicators Checklist:**
- [ ] AI references facts contradicted by provided data
- [ ] AI mentions outdated people/roles/regulations
- [ ] AI uses past tense for recent/current events
- [ ] AI expresses uncertainty about clearly stated recent data
- [ ] Stock rankings seem disconnected from recent major events
- [ ] Analysis includes anachronistic market condition references

**Severity Assessment:**
- **Critical**: Bias causes material ranking errors affecting investment decisions
- **Moderate**: Bias present in commentary but rankings generally correct
- **Minor**: Occasional anachronistic references without analysis impact
- **None**: No detectable temporal bias

**Decision Point:** If no bias detected, document findings and implement lightweight monitoring only.

### 2.4 Phase 4: Quick Diagnostic Test

**Objectives:**
- Test if explicit temporal markers are processed correctly
- Inform prompt engineering strategy

**Actions:**
1. Create test copy of `all.txt` in isolated directory
2. Prepend: `"Today is [CURRENT_DATE]. All data below is from today and is current."`
3. Run single analysis with test input
4. Observe if AI acknowledges date and treats data as current

**Expected Outcomes:**
- **Good**: AI explicitly acknowledges date and treats all data as current
- **Partial**: AI processes date but still applies some outdated knowledge
- **Poor**: AI ignores date marker entirely

---

## 3. Mitigation Strategies

### 3.1 Strategy Selection Matrix

| Bias Type | Severity | Recommended Strategy | Implementation Complexity |
|-----------|----------|---------------------|---------------------------|
| Type A (Non-recognition) | Any | Prompt Engineering + Timestamps | Low-Medium |
| Type B (Outdated knowledge) | Minor-Moderate | Context Prioritization Prompts | Low |
| Type B (Outdated knowledge) | Critical | Prompts + Timestamps + Validation | Medium-High |
| Type C (Mixed) | Any | Phased approach: Prompts first, add timestamps if needed | Low-High |

### 3.2 Primary Mitigation: Prompt Engineering

**Core Principles:**
1. **Explicit Temporal Framing**: State current date and data recency upfront
2. **Context Prioritization**: Instruct AI to treat provided data as authoritative
3. **Avoid Impossible Instructions**: Don't ask AI to "ignore training data" (it can't)
4. **Clear Conflict Resolution**: Specify that provided data overrides training knowledge

**Effective Prompt Pattern:**

```
You are analyzing financial data from [TODAY'S DATE: YYYY-MM-DD].

All information provided below is current as of today. This data includes recent news,
financial metrics, and market events from the last [N] hours.

IMPORTANT: If any information in the provided data contradicts your training knowledge,
the provided data is correct and current. Base your analysis solely on the information
given below. Do not apply historical knowledge about these companies unless it remains
currently relevant.

[DATA BEGINS HERE]
```

**What NOT to say:**
- ❌ "Ignore your training cutoff" (impossible for LLM to do)
- ❌ "Forget what you know about these companies" (confusing and ineffective)
- ❌ "Only use information after April 2024" (too vague)

**What TO say:**
- ✅ "Provided data is from [TODAY'S DATE]"
- ✅ "If data contradicts training knowledge, the data is correct"
- ✅ "Base analysis solely on provided information"

### 3.3 Secondary Mitigation: Selective Timestamp Injection

**When to Use:**
- Prompt engineering alone shows insufficient improvement
- Type A bias persists (non-recognition of recency)
- Token budget allows for overhead

**Implementation Approach:**

**Full Timestamping** (if token budget allows):
```
AS OF 2025-01-09T14:30:00Z: [Company X] reports Q4 earnings beat expectations
AS OF 2025-01-09T13:15:00Z: [Metric] = [Value]
AS OF 2025-01-09T12:00:00Z: [News headline and content]
```

**Selective Timestamping** (token-conscious):
- Timestamp NEWS ITEMS only (highest bias risk)
- Timestamp EVENT-DRIVEN data (earnings, announcements, regulatory)
- Skip timestamps for static metrics (market cap, P/E ratios)

**Format Requirements:**
- Use ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`
- Include timezone (UTC recommended)
- Place timestamp at beginning of each item
- Use consistent prefix: `"AS OF [TIMESTAMP]:"`

### 3.4 Token Budget Management

**Before implementing timestamps:**

1. **Measure Current Baseline:**
   ```bash
   # Log token usage from recent runs
   # Calculate average tokens per analysis
   ```

2. **Estimate Overhead:**
   - Each ISO timestamp ≈ 10-15 tokens
   - Count data items requiring timestamps
   - Calculate: `total_new_tokens = items × 12 (avg)`

3. **Verify Headroom:**
   - Current usage + overhead < API limit?
   - Cost increase acceptable?
   - Context window sufficient?

4. **Adjust Strategy if Needed:**
   - Use selective timestamping
   - Compress other prompt sections
   - Consider summarizing verbose data

### 3.5 Tertiary Mitigation: Post-Processing Validation (Optional)

**Use Only If:**
- Temporal bias persists after S3.2 and S3.3
- Bias follows predictable patterns
- Manual review capacity exists

**Simple Validation Approach:**

1. **Create Known Issues List:**
   - Document specific outdated facts observed in S2.3
   - Example: "Former CEO John Smith (replaced in 2024)"
   - Example: "Old regulation XYZ (repealed in 2024)"

2. **Implement Keyword Flagging:**
   ```python
   # Simple regex-based flagging
   outdated_patterns = [
       r"CEO John Smith",  # Replaced in 2024
       r"Regulation XYZ",  # Repealed
       # Add observed patterns
   ]

   for pattern in outdated_patterns:
       if re.search(pattern, ai_output):
           flag_for_review(ai_output, pattern)
   ```

3. **Manual Review Process:**
   - Flagged outputs reviewed by analyst
   - False positives expected and acceptable
   - Used for monitoring, not blocking

**Avoid Over-Engineering:**
- Don't build comprehensive knowledge bases
- Don't create complex validation logic
- Don't block outputs automatically
- Do use as monitoring and quality assurance

---

## 4. Implementation Guide

### 4.1 Pre-Implementation Checklist

- [ ] Completed diagnostic phases 2.1-2.3
- [ ] Confirmed temporal bias exists and severity warrants mitigation
- [ ] Input data freshness validated (not a data pipeline issue)
- [ ] Token budget analyzed and headroom confirmed
- [ ] Backup of current system created
- [ ] Test environment prepared

### 4.2 Implementation Phase 1: Prompt Engineering

**Step 1: Locate Prompt Templates**

Find where prompts are constructed in your codebase:
```bash
# Search for prompt-related files
grep -r "prompt" /path/to/codebase --include="*.sh" --include="*.py"
grep -r "claude" /path/to/codebase --include="*.sh" --include="*.py"
```

**Step 2: Modify Prompt Template**

Add temporal context wrapper at the beginning of system or user prompt:

```python
# Example: Python prompt construction
from datetime import datetime

temporal_context = f"""You are analyzing financial data from {datetime.now().strftime('%Y-%m-%d')}.

All information provided below is current as of today. This data includes recent news,
financial metrics, and market events from the last {hours} hours.

IMPORTANT: If any information in the provided data contradicts your training knowledge,
the provided data is correct and current. Base your analysis solely on the information
given below.

"""

# Prepend to existing prompt
full_prompt = temporal_context + original_prompt
```

**Step 3: Implement Feature Flag**

Allow easy rollback via environment variable:

```bash
# In run_without_api.sh or equivalent
USE_TEMPORAL_CONTEXT="${USE_TEMPORAL_CONTEXT:-true}"

if [ "$USE_TEMPORAL_CONTEXT" = "true" ]; then
    # Use new temporal-aware prompt
    prompt_file="prompts/temporal_aware_prompt.txt"
else
    # Use original prompt
    prompt_file="prompts/original_prompt.txt"
fi
```

**Step 4: Test Single Run**

```bash
# Test with new prompt
USE_TEMPORAL_CONTEXT=true ./run_without_api.sh claude all.txt 8 10

# Compare output to baseline
diff output_baseline.txt output_temporal_context.txt
```

**Step 5: Validate Token Usage**

```bash
# Log token counts
# Verify increase is within acceptable range (<20% increase)
```

**Step 6: Version Control**

```bash
git add prompts/temporal_aware_prompt.txt run_without_api.sh
git commit -m "feat: Add temporal context to prompts to mitigate training data bias

- Added explicit date and recency framing
- Instructed AI to prioritize provided data over training knowledge
- Implemented USE_TEMPORAL_CONTEXT feature flag for rollback
- Token usage increased by ~X% (within budget)

Addresses temporal bias where AI applies outdated knowledge to recent data."
```

### 4.3 Implementation Phase 2: Selective Timestamp Injection (If Needed)

**Step 1: Identify Timestamp Injection Points**

Locate data preprocessing code:
```bash
grep -r "all.txt" /path/to/codebase
# Find where all.txt is created or processed
```

**Step 2: Implement Timestamp Preprocessing**

```python
# Example: Python preprocessing
from datetime import datetime, timezone

def add_timestamps_to_news(data_items, timestamp=None):
    """Add ISO timestamps to news items and events."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    timestamped_items = []
    for item in data_items:
        if item['type'] in ['news', 'event', 'announcement']:
            # Add timestamp to high-priority items
            item_timestamp = item.get('timestamp', timestamp)
            timestamped_text = f"AS OF {item_timestamp.isoformat()}: {item['content']}"
            timestamped_items.append(timestamped_text)
        else:
            # Skip timestamp for metrics and static data
            timestamped_items.append(item['content'])

    return timestamped_items
```

**Step 3: Implement Feature Flag**

```bash
# In run_without_api.sh
USE_TIMESTAMPS="${USE_TIMESTAMPS:-false}"

if [ "$USE_TIMESTAMPS" = "true" ]; then
    python3 preprocess_with_timestamps.py all.txt > all_timestamped.txt
    input_file="all_timestamped.txt"
else
    input_file="all.txt"
fi
```

**Step 4: Test Token Impact**

```bash
# Test with timestamps
USE_TIMESTAMPS=true ./run_without_api.sh claude all.txt 8 10

# Verify token usage within budget
# Check output quality
```

**Step 5: Version Control**

```bash
git add preprocess_with_timestamps.py run_without_api.sh
git commit -m "feat: Add selective timestamp injection for temporal context reinforcement

- Timestamps added to news items and events only (token-conscious)
- ISO 8601 format for machine readability
- USE_TIMESTAMPS feature flag for easy disable
- Token overhead: ~X% (selective approach)

Used in combination with temporal-aware prompts for Type A bias mitigation."
```

### 4.4 Rollback Procedures

**Immediate Rollback (Feature Flags):**
```bash
# Disable temporal context prompts
export USE_TEMPORAL_CONTEXT=false

# Disable timestamps
export USE_TIMESTAMPS=false

# Run with original configuration
./run_without_api.sh claude all.txt 8 10
```

**Git Rollback (if feature flags fail):**
```bash
# Identify commit before changes
git log --oneline

# Revert to previous version
git revert <commit_hash>

# Or hard reset (use with caution)
git reset --hard <commit_before_changes>
```

**Partial Rollback:**
```bash
# Keep prompts, disable timestamps
export USE_TEMPORAL_CONTEXT=true
export USE_TIMESTAMPS=false
```

---

## 5. Validation and Testing

### 5.1 Validation Test Plan

**Test 1: Baseline Comparison**

```bash
# Before implementation: save baseline
./run_without_api.sh claude all.txt 8 10 > output_baseline.txt

# After implementation: compare
USE_TEMPORAL_CONTEXT=true USE_TIMESTAMPS=true \
./run_without_api.sh claude all.txt 8 10 > output_mitigated.txt

# Analyze differences
diff output_baseline.txt output_mitigated.txt > changes.diff
```

**Test 2: Temporal Bias Indicator Check**

Review output for improvements:
- [ ] Fewer outdated fact references
- [ ] No contradictions between AI output and provided data
- [ ] Appropriate tense usage (present for current events)
- [ ] Confident analysis without hedging about data recency
- [ ] Rankings align with recent major events

**Test 3: Quality Assurance**

Ensure no degradation:
- [ ] Analysis depth maintained
- [ ] Ranking logic still sound
- [ ] No new errors or hallucinations introduced
- [ ] Output format unchanged
- [ ] Execution time within acceptable range (+/- 20%)

**Test 4: Token Usage Validation**

```bash
# Log token counts before and after
# Verify increase is within budget
# Calculate cost impact
```

**Test 5: Known Event Validation**

Select 3-5 stocks with major recent events (last 24-48 hours):
- Earnings surprises
- Executive changes
- Regulatory announcements
- Merger/acquisition news

Verify AI analysis correctly incorporates these events without applying outdated context.

### 5.2 Success Criteria

**Minimum Acceptable:**
- 70%+ reduction in temporal bias indicators from baseline
- No quality degradation in core analysis
- Token usage increase ≤ 20%
- Execution time increase ≤ 20%

**Target Goals:**
- 90%+ reduction in temporal bias indicators
- Stock rankings demonstrably aligned with recent events
- Zero instances of AI contradicting provided current data
- Maintained or improved analysis quality

### 5.3 Edge Cases to Test

1. **Very Recent Events (< 4 hours old)**
   - Test if AI handles breaking news correctly
   - Verify no confusion between "just announced" vs "historical"

2. **Conflicting Information**
   - Provide data that contradicts training data
   - Verify AI prioritizes provided data

3. **Historical Context Legitimately Needed**
   - Ensure AI doesn't over-correct and ignore relevant history
   - Example: Year-over-year comparisons should still work

4. **Ambiguous Temporal References**
   - Data with unclear dates
   - Verify AI doesn't make unwarranted assumptions

---

## 6. Operational Monitoring

### 6.1 Ongoing Monitoring Procedures

**Monthly Spot-Check Review (15-30 minutes):**

1. **Select Random Sample:**
   - 5-10 recent analysis outputs
   - Include variety of market conditions

2. **Review for Temporal Bias Indicators:**
   - Outdated facts or references
   - Contradictions with recent known events
   - Inappropriate hedging or uncertainty
   - Ranking misalignments

3. **Document Findings:**
   - Log any bias instances discovered
   - Note patterns or trends
   - Flag for investigation if bias increasing

**Event-Triggered Review:**

Perform spot-check review after:
- Major market events (crashes, rallies)
- Significant news affecting multiple stocks
- Claude API version updates
- System or prompt modifications

### 6.2 Key Performance Indicators (KPIs)

**Bias Metrics:**
- Number of outdated references per output
- Instances of AI contradicting provided data
- Rankings misaligned with recent major events

**Quality Metrics:**
- Analysis depth and thoroughness
- Ranking accuracy vs. market performance
- User/analyst satisfaction scores

**Performance Metrics:**
- Token usage per analysis
- Execution time
- API error rates

**Target Thresholds:**
- Temporal bias instances: < 1 per 10 outputs
- Token usage: stable or increasing < 5% per quarter
- Execution time: stable or improving

### 6.3 Alert Conditions

**Immediate Investigation Needed:**
- Sudden increase in temporal bias instances (> 2x normal rate)
- Multiple outputs contradicting recent major events
- Claude API version change notification
- Token usage approaching limits

**Scheduled Review Needed:**
- Gradual increase in bias instances over 2+ months
- User reports of outdated analysis
- New types of temporal bias manifesting

### 6.4 Monitoring Checklist Template

```markdown
## Monthly Temporal Bias Review - [Month/Year]

**Reviewer:** [Name]
**Date:** [YYYY-MM-DD]
**Sample Size:** [N outputs]
**Date Range of Samples:** [YYYY-MM-DD to YYYY-MM-DD]

### Temporal Bias Indicators
- [ ] Outdated fact references: [Count] instances
  - Details: [list specific examples if any]
- [ ] Data contradictions: [Count] instances
  - Details: [list specific examples if any]
- [ ] Inappropriate hedging: [Count] instances
  - Details: [list specific examples if any]
- [ ] Ranking misalignments: [Count] instances
  - Details: [list specific examples if any]

### Quality Assessment
- [ ] Analysis depth: [Maintained / Improved / Degraded]
- [ ] Overall quality: [Score 1-5]
- [ ] Notable improvements: [observations]
- [ ] Notable issues: [observations]

### Performance Metrics
- Average token usage: [N tokens] (Change from baseline: [+/- X%])
- Average execution time: [N seconds] (Change from baseline: [+/- X%])

### Recommendations
- [ ] Continue current approach - no changes needed
- [ ] Minor adjustments recommended: [describe]
- [ ] Investigation needed: [describe concern]
- [ ] Escalate to development team: [describe issue]

### Next Review Date
[YYYY-MM-DD]
```

---

## 7. Troubleshooting

### 7.1 Common Issues and Solutions

**Issue 1: Temporal bias persists after prompt engineering**

**Symptoms:**
- AI still references outdated facts
- Contradictions continue
- Minimal improvement from baseline

**Diagnostic Steps:**
1. Verify prompt changes are actually being applied
   ```bash
   # Check if USE_TEMPORAL_CONTEXT is being used
   echo $USE_TEMPORAL_CONTEXT

   # Verify prompt file being loaded
   cat prompts/temporal_aware_prompt.txt
   ```

2. Review actual prompt sent to Claude
   - Add debug logging to capture full prompt
   - Verify temporal context appears at beginning

3. Check if data itself lacks temporal markers
   - Review all.txt for dates and timestamps
   - Verify data freshness

**Solutions:**
- Strengthen prompt language (more explicit instructions)
- Add timestamp injection (Phase 2)
- Consider more aggressive context prioritization prompts

---

**Issue 2: Token usage exceeds budget**

**Symptoms:**
- API errors about context length
- Cost significantly higher than baseline
- Slow performance

**Diagnostic Steps:**
1. Measure token breakdown
   ```python
   # Count tokens in different sections
   prompt_tokens = count_tokens(prompt)
   data_tokens = count_tokens(data)
   timestamp_tokens = count_tokens(timestamps)
   ```

2. Identify overhead sources
   - Prompt additions: X tokens
   - Timestamps: Y tokens
   - Total overhead: X + Y

**Solutions:**
- Use selective timestamping (news only)
- Compress prompt language
- Reduce data verbosity in preprocessing
- Consider summarizing lengthy news articles

---

**Issue 3: Quality degradation in analysis**

**Symptoms:**
- Shallower analysis than baseline
- Missing insights
- Over-reliance on provided data ignoring relevant context

**Diagnostic Steps:**
1. Compare baseline vs. mitigated outputs side-by-side
2. Identify specific quality issues:
   - Missing historical context that is relevant?
   - Less detailed reasoning?
   - Factual errors introduced?

**Solutions:**
- Revise prompt to allow relevant historical context
   ```
   "Use historical context when relevant to understanding trends,
   but prioritize provided current data for facts and events."
   ```
- Remove overly restrictive language
- Test iterative prompt refinements

---

**Issue 4: Timestamps confusing the AI**

**Symptoms:**
- AI references timestamps in odd ways
- Timestamps treated as content
- Format errors in output

**Diagnostic Steps:**
1. Review timestamp format being used
2. Check if timestamps are properly formatted
3. Verify AI is parsing timestamps correctly

**Solutions:**
- Try different timestamp formats:
  - `AS OF [DATE]:`
  - `[DATE] -`
  - `Published: [DATE]`
- Add prompt instruction about timestamp format
- Use more natural language timestamps
  ```
  "The following news is from today, [Month Day, Year]:"
  ```

---

**Issue 5: Rollback doesn't restore baseline behavior**

**Symptoms:**
- Feature flags set to false but behavior still different
- Output doesn't match original baseline

**Diagnostic Steps:**
1. Verify environment variables
   ```bash
   env | grep TEMPORAL
   env | grep TIMESTAMP
   ```

2. Check if cached prompts or state exists
3. Verify original code paths are being executed

**Solutions:**
- Restart processes to clear any cached state
- Git reset to known good commit
- Clear any temporary files
- Check for unintended code changes

---

### 7.2 When to Seek Alternative Approaches

Consider fundamentally different approaches if:

1. **Temporal bias persists at critical severity** after implementing all mitigations
2. **Token budget constraints** make effective mitigation impossible
3. **Quality degradation** is unacceptable despite multiple prompt iterations
4. **Performance impact** exceeds acceptable thresholds

**Alternative Approaches to Consider:**

**Option A: Retrieval-Augmented Generation (RAG) with Temporal Reasoning**
- Embed data with explicit temporal metadata
- Use vector database with temporal filtering
- Retrieve only strictly relevant recent context

**Option B: Fine-tuned Model**
- Fine-tune model on recent financial data
- Update periodically (monthly/quarterly)
- Higher cost but potentially better temporal awareness

**Option C: Hybrid System**
- Use AI for sentiment/analysis
- Use rule-based system for rankings
- Combine outputs with weighted approach

**Option D: Model Ensemble**
- Use multiple models with different cutoff dates
- Compare outputs for consistency
- Flag discrepancies for human review

---

## 8. Appendices

### Appendix A: Temporal Bias Detection Examples

**Example 1: Type A Bias (Non-Recognition)**

**Input Data:**
```
Tesla announces record Q4 2024 deliveries, beating analyst expectations by 15%.
Stock surges 8% in pre-market trading on January 9, 2025.
```

**Biased Output:**
```
Tesla's historical delivery patterns suggest strong performance in Q4.
If the company were to beat expectations, we would likely see positive
market reaction.
```

**Issue**: Using future tense and hypothetical language for event that already occurred.

---

**Example 2: Type B Bias (Outdated Knowledge)**

**Input Data:**
```
Apple Inc. CEO Tim Cook announces new AI initiative in partnership with OpenAI,
effective January 2025. This marks Apple's major entry into generative AI market.
```

**Biased Output:**
```
While Apple has historically been conservative about AI investments,
the company has not made significant moves in generative AI space as of
my last update. Tim Cook has generally focused on privacy and hardware innovation.
```

**Issue**: Contradicting provided current data with outdated training knowledge.

---

**Example 3: Type C Bias (Mixed)**

**Input Data:**
```
Meta Platforms announces 12% increase in ad revenue for Q4 2024, driven by
AI-powered ad targeting improvements. Mark Zuckerberg highlights success of
Reels monetization strategy implemented in 2024.
```

**Biased Output:**
```
Meta Platforms shows strong performance with 12% ad revenue growth, likely
driven by AI improvements. However, the company has historically struggled
with Reels monetization compared to TikTok. Former executive Sheryl Sandberg's
advertising expertise will be crucial for continued growth.
```

**Issue**: Correct analysis of current data, but includes outdated reference to Sheryl Sandberg (departed in 2022).

---

### Appendix B: Effective Prompt Templates

**Template 1: Minimal Temporal Context (Low Token Overhead)**

```
Analysis Date: {current_date}

All data below is from today. Base analysis on provided information only.

[DATA]
```

**Template 2: Standard Temporal Context (Recommended)**

```
You are analyzing financial data from {current_date}.

All information provided below is current as of today. This data includes
recent news, financial metrics, and market events from the last {hours} hours.

IMPORTANT: If any information in the provided data contradicts your training
knowledge, the provided data is correct and current. Base your analysis solely
on the information given below.

[DATA]
```

**Template 3: Aggressive Temporal Context (For Severe Bias)**

```
TEMPORAL CONTEXT:
- Today's Date: {current_date}
- Data Recency: Last {hours} hours
- All information below is CURRENT and VERIFIED

INSTRUCTIONS:
1. Treat all provided data as authoritative and current
2. If data contradicts your training knowledge, the DATA IS CORRECT
3. Do not apply historical assumptions unless explicitly relevant to trends
4. Use present tense for current events described below
5. Do not hedge or express uncertainty about data recency

CRITICAL: Your training data may be outdated. TRUST THE PROVIDED DATA.

[DATA]
```

**Template 4: Balanced Context (Allows Relevant History)**

```
You are analyzing financial data from {current_date}.

All information below is current as of today ({current_date}). This includes
recent news and financial metrics from the last {hours} hours.

GUIDANCE:
- Provided current data is authoritative - if it conflicts with your training
  knowledge, the provided data is correct
- You may reference relevant historical trends and patterns to provide context
- Clearly distinguish between current facts (from data) and historical context
  (from your knowledge)
- If uncertain about whether something has changed, trust the provided data

[DATA]
```

---

### Appendix C: Token Budget Calculation Worksheet

**Step 1: Measure Current Baseline**
```
Average input tokens: ______
Average output tokens: ______
Total per analysis: ______
API limit: ______
Current headroom: ______ tokens (______ %)
```

**Step 2: Estimate Prompt Overhead**
```
Original prompt tokens: ______
Temporal context addition tokens: ______
Prompt overhead: ______ tokens (+______ %)
```

**Step 3: Estimate Timestamp Overhead**
```
Number of timestampable items: ______
Tokens per timestamp (avg 12): × 12
Total timestamp overhead: ______ tokens

Percentage of input data: ______ %
```

**Step 4: Calculate Total Impact**
```
Current total: ______
+ Prompt overhead: ______
+ Timestamp overhead: ______
= New estimated total: ______

Percentage increase: ______ %
Remaining headroom: ______ tokens (______ %)
```

**Step 5: Decision**
```
[ ] Proceed with full implementation (headroom > 20%)
[ ] Use selective timestamping (headroom 10-20%)
[ ] Prompt-only approach (headroom < 10%)
[ ] Revise data preprocessing to reduce baseline usage
```

---

### Appendix D: Git Commit Message Templates

**Prompt Engineering Implementation:**
```
feat: Add temporal context to prompts for training data bias mitigation

- Added explicit current date and data recency framing
- Instructed AI to prioritize provided data over training knowledge
- Implemented USE_TEMPORAL_CONTEXT feature flag for easy rollback
- Token usage increased by {X}% (within acceptable budget)

Addresses issue where Claude's April 2024 knowledge cutoff was causing
misinterpretation of recent financial events. Testing showed {Y}%
reduction in temporal bias indicators.

Modified files:
- prompts/system_prompt.txt
- run_without_api.sh
- config/environment.sh
```

**Timestamp Injection Implementation:**
```
feat: Add selective timestamp injection for temporal context reinforcement

- Timestamps added to news items and events only (token-conscious approach)
- ISO 8601 format for machine and human readability
- Implemented USE_TIMESTAMPS feature flag for optional activation
- Token overhead: ~{X}% (selective approach keeps overhead minimal)

Used in combination with temporal-aware prompts to reinforce data recency.
Particularly effective for Type A temporal bias (non-recognition of recency).

Modified files:
- scripts/preprocess_data.py
- run_without_api.sh
- config/environment.sh
```

**Rollback Commit:**
```
revert: Roll back temporal bias mitigations due to {reason}

Reverting commits:
- {commit_hash}: Prompt engineering changes
- {commit_hash}: Timestamp injection

Reason: {Quality degradation / Token budget exceeded / Performance impact}

Detailed findings:
- {observation 1}
- {observation 2}

Will explore alternative approach: {description}
```

---

### Appendix E: References and Further Reading

**LLM Temporal Bias Research:**
- "Temporal Misalignment in Large Language Models" - Understanding how training cutoffs affect model outputs
- "Grounding LLMs with Current Information" - Techniques for incorporating recent data

**Prompt Engineering Resources:**
- Claude Prompt Engineering Guide: https://docs.anthropic.com/claude/docs/prompt-engineering
- Best practices for context prioritization
- Token optimization strategies

**Financial AI Applications:**
- Temporal considerations in financial ML models
- Real-time data integration in AI-driven trading systems
- Bias detection in automated financial analysis

**System Documentation:**
- TECHNICAL_ARCHITECTURE.md - System design and data flow
- run_without_api.sh - Main execution script
- Project-specific prompt templates and configuration files

---

### Appendix F: Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-01-09 | 1.0 | Initial document creation based on execution plan and critic feedback | [Name] |
| | | | |
| | | | |

---

## Document Maintenance

**Review Schedule:**
- **Quarterly**: Review for accuracy and relevance
- **After Major Changes**: Update when system architecture changes significantly
- **After Claude Updates**: Review when Claude API version changes

**Ownership:**
- **Primary Maintainer**: [Name/Team]
- **Stakeholders**: Data Science Team, Operations Team, Trading Desk
- **Approval Required**: Technical Lead, Risk Management

**Feedback:**
Please submit feedback, corrections, or suggestions to [contact/repo]

---

*Last Updated: 2025-01-09*
*Document Version: 1.0*
*System Version: [Current System Version]*
