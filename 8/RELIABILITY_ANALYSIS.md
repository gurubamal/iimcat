# 🔴 RELIABILITY ISSUES IDENTIFIED

## Critical Problems with Current System:

### 1. **Broken Entity Resolution**
- News about "Trump" gets matched to "TRU" ticker (Trucap Finance)
- News about "Trust" gets matched to multiple trust companies
- News about "Global spice industry" matched to "Global Education"
- **This is completely wrong!**

### 2. **News Relevance**
- Articles are about global industries, not specific companies
- Ticker matching is doing keyword search, not entity matching
- Example: "Global spice industry" ≠ "Global Education Limited"

### 3. **Deal Size Attribution**
- ₹2,000 crore deals attributed to wrong companies
- News about one sector matched to completely different sector
- Magnitude extraction not validated against company

### 4. **Certainty Scores Misleading**
- High scores based on keyword matches, not actual relevance
- Multiple articles doesn't mean they're about the company
- Source credibility irrelevant if news isn't about the company

### 5. **Expected Rise Calculations**
- Based on wrong deal-to-market-cap ratios
- Using news from unrelated companies
- Mathematical precision hiding fundamental errors

---

## What Needs to Be Fixed:

### A. **Proper Entity Resolution**
```
Current: Keyword matching (broken)
Needed: 
- Match ticker to official company name
- Verify company name appears in article
- Check if article is actually about the company
- Validate business sector alignment
```

### B. **News Validation**
```
Current: Any mention counts
Needed:
- Company name must appear in headline or first paragraph
- Deal/event must be attributed to specific company
- Cross-reference with company sector
- Verify deal size is realistic for company
```

### C. **Quality Verification**
```
Current: Algorithmic scoring
Needed:
- Human-readable explanation of why news is relevant
- Show exact text that mentions the company
- Sector consistency check
- Deal size sanity check against market cap
```

### D. **Honest Reporting**
```
Current: Presents uncertain data as facts
Needed:
- Clear uncertainty indicators
- "Unable to verify" for unclear matches
- Show confidence breakdown
- Reject if company name not in article
```

---

## Recommended Approach:

### 1. **Conservative Entity Matching**
- Company name MUST appear in article text
- Ticker alone is NOT sufficient
- Business sector must align with news sector
- Reject ambiguous matches

### 2. **Transparency in Results**
- Show exact quote from article mentioning company
- Indicate if match is uncertain
- Separate "verified" from "possible" matches
- Provide manual verification links

### 3. **Realistic Expectations**
- Don't claim 50-100% rises without basis
- Be honest about small data samples
- Acknowledge limitations
- Focus on process, not promises

---

## Honest Assessment of Current Scan:

**Truth:**
- We have 78 articles from financial news
- Many are about macro trends (spice industry, global markets)
- Entity resolution is matching keywords, not companies
- Most "matches" are false positives
- Deal sizes are likely from wrong companies

**What Actually Works:**
- News collection is working (78 articles)
- Sources are credible (ET, BS, LiveMint)
- Fake rally detection logic is sound
- Magnitude filtering concept is good

**What Doesn't Work:**
- Ticker-to-company-to-news mapping
- Entity resolution accuracy
- Confidence in recommendations
- Expected rise calculations based on wrong data

---

## What Should We Do Instead?

### Option 1: **Fix Entity Resolution** (Complex, time-consuming)
- Implement proper NER (Named Entity Recognition)
- Build company name database with variants
- Validate matches against multiple criteria
- Manual review of top picks

### Option 2: **Manual Curation** (Slower but accurate)
- Review news manually
- Verify each company mention
- Build curated list of verified opportunities
- Quality over quantity

### Option 3: **Be Honest About Limitations**
- Present news articles raw
- Let user decide relevance
- Provide tools for verification
- Don't make false claims

---

## Immediate Action:

**I recommend we:**
1. Acknowledge the system has accuracy issues
2. Show you the raw news articles
3. Let you manually verify relevance
4. Build better entity resolution before making claims
5. Focus on process improvement, not quick results

**Would you like me to:**
- A) Show you the raw news articles for manual review?
- B) Build a better entity resolution system?
- C) Focus on specific sectors you're interested in?
- D) Something else?

---

**Bottom Line:** The current "recommendations" are unreliable because the ticker-to-news matching is broken. We need to fix this before making investment suggestions.

