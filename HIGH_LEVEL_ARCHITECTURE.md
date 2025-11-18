# High-Level Architecture

The tool uses a **multi-agent LLM approach** to automatically price insurance claim items by searching the web for comparable prices.

```
CSV Input → Classify → Route → Research → Validate → CSV Output
```

---

## Step-by-Step Process

### 1. **Input: CSV File**

You provide a CSV with claim items:

```csv
description,brand,condition,age,estimated_value
"Samsung 55-inch 4K TV",Samsung,good,3 years,800
```

### 2. **Initial Routing Decision**

```python
# claim_assist/processors/claim_processor.py
if item.estimated_value < threshold:  # Default: $100
    return simple_pricing(item)  # Fast heuristic
else:
    return full_llm_research(item)  # Deep research
```

**Low-value items** (<$100):

- Uses depreciation formula based on condition
- No API calls = $0 cost
- Example: IKEA bookshelf → $42.50

**High-value items** (≥$100):

- Full LLM research with web search
- Proceeds to next steps

---

### 3. **Classification (Haiku)**

```python
# claim_assist/pricing/classifier.py
ItemClassifier.classify(item)
```

**What it does:**

- Uses Claude Haiku (fast, cheap model)
- Analyzes item description, brand, condition
- Returns: `simple`, `moderate`, or `complex`

**Example:**

```json
{
  "complexity": "simple",
  "reasoning": "Standard consumer electronics, readily available"
}
```

**Purpose:** Determines which model to use for research

- Simple/Moderate → Haiku (~$0.001/item)
- Complex (vintage, rare) → Sonnet (~$0.02/item)

---

### 4. **Research with Web Search**

```python
# claim_assist/pricing/researcher.py
PriceResearcher.research(item, complexity)
```

**What happens:**

#### a) **Prompt Construction**

The tool builds a prompt with:

- Item details (description, brand, condition, age)
- Instructions to search real marketplaces
- Strict JSON formatting requirements

#### b) **API Call with Web Search Tool**

```python
client.messages.create(
    model="claude-3-5-haiku-latest",  # or Sonnet for complex
    messages=[{"role": "user", "content": prompt}],
    tools=[{
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 5  # Up to 5 web searches
    }]
)
```

#### c) **Claude Searches Real Sites**

Claude automatically searches:

- eBay (sold listings)
- Amazon
- Facebook Marketplace
- Retail sites (Best Buy, Home Depot, etc.)
- Specialty sites (Etsy for vintage, etc.)

#### d) **Returns Structured Data**

```json
{
  "price_sources": [
    {"source": "eBay", "price": 650},
    {"source": "Amazon", "price": 720},
    {"source": "Best Buy", "price": 700}
  ],
  "recommended_value": 690,
  "confidence": "high",
  "reasoning": "3-year-old TV, accounting for depreciation",
  "search_queries_used": ["Samsung 55-inch 4K TV used"]
}
```

---

### 5. **JSON Extraction**

```python
# claim_assist/pricing/researcher.py
_extract_json_from_text(response_text)
```

**Challenge:** Claude sometimes adds explanation text around the JSON

 

**Solution:** Smart bracket-counting parser that:

1. Finds first `{`
2. Tracks nested braces and string quotes
3. Extracts complete JSON object
4. Handles escaped characters

---

### 6. **Validation (Insurance Standards)**

```python
# claim_assist/pricing/validator.py
PriceValidator.validate(item, pricing_data)
```

**What it does:**

#### a) **Calculate Statistics**

- 75th percentile (industry standard for "fair replacement")
- Median price
- Price range

#### b) **Confidence Assessment**

```python
if comparable_count < 3:
    confidence = "low"
elif comparable_count >= 5 and research_confidence == "high":
    confidence = "high"
else:
    confidence = "medium"
```

#### c) **Outlier Detection**

```python
if abs(recommended_value - median) > median * 0.5:
    flag_for_human_review = True
```

#### d) **Human Review Flagging**

Items flagged if:

- < 3 comparable prices found
- Recommended value deviates >50% from median
- Low confidence from research
- Research failed

---

### 7. **Output Generation**

```python
# claim_assist/processors/claim_processor.py
results.to_csv("claim_evaluation_results.csv")
```

**Two CSV files created:**

#### a) **Complete Results**

Every item with full details:

```csv
item,recommended_value,price_range,confidence,price_sources
Samsung TV,685,$450-$720,medium,"eBay: $650; Amazon: $720"
```

#### b) **Items for Review**

Only flagged items needing human verification

---

## Key Technologies

### **1. Claude Models**

|Model|Use Case|Cost|Speed|
|---|---|---|---|
|Haiku|Classification, Simple items|~$0.001|Fast|
|Sonnet|Complex/vintage items|~$0.02|Slower|

### **2. Web Search Integration**

```python
tools=[{
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5
}]
```

- Claude automatically searches web
- Real-time price data
- Multiple sources per item

### **3. Caching System**

```python
# claim_assist/utils/cache.py
cache_key = md5(f"{description}_{brand}_{condition}")
```

- Prevents duplicate API calls
- 24-hour TTL
- Saves cost on similar items

---

## Cost Optimization Strategies

### **1. Value-Based Routing**

```python
if estimated_value < $100:
    use_heuristic()  # $0
else:
    use_llm()  # $0.001-0.02
```

### **2. Model Selection**

- Haiku for routine items (90% of cases)
- Sonnet only for complex items (10%)

### **3. Caching**

- Similar items reuse cached results
- No repeat API calls

### **4. Batch Processing**

- Process entire CSV in one run
- Progress tracking every 10 items

**Example cost for 100-item claim:**

- 90 simple items × $0.001 = $0.09
- 10 complex items × $0.02 = $0.20
- **Total: ~$0.29**

---

## Error Handling

### **Graceful Degradation**

At every step, if something fails, the tool falls back:

1. **JSON parsing fails** → Use estimated value
2. **Web search fails** → Use estimated value
3. **API error** → Retry with fallback
4. **No comparables found** → Flag for review

### **Example Failure Path**

```
Research fails → Use estimated_value → Set confidence="low" 
→ Flag needs_human_review=True → Still completes processing
```

---

## File Structure

```
claim_assist/
├── models/
│   └── item.py           # Data models (ClaimItem, PricingResult)
├── pricing/
│   ├── classifier.py     # Routes by complexity
│   ├── researcher.py     # Web search + price research
│   └── validator.py      # Insurance standards validation
├── processors/
│   └── claim_processor.py  # Main orchestration logic
├── utils/
│   ├── cache.py          # Result caching
│   └── api_clients.py    # Anthropic client setup
├── config.py             # Configuration management
└── main.py               # CLI entry point
```

---

## Summary: The Complete Flow

```
1. Load CSV → Parse items
2. For each item:
   a. Check value threshold
   b. If low → simple depreciation
   c. If high → classify complexity
   d. Research with web search (Claude searches eBay, Amazon, etc.)
   e. Parse JSON response
   f. Validate with insurance standards
   g. Flag outliers for review
3. Export two CSVs:
   - All results with price sources
   - Items needing human review
4. Display summary
```

**Result:** Automated claim pricing with full transparency into where each price came from, which items need review, and detailed reasoning for all valuations.




Only using Haiku3.5 for all tasks
Only using ebay and facebook marketplace

|   |   |   |   |   |   |
|---|---|---|---|---|---|
|**item**|**recommended_value**|**percentile_75**|**price_range**|**confidence**|**needs_human_review**|
|**Samsung 55-inch 4K TV**|289.98|329.95|$250.00 - $329.95|low|TRUE|
|**Vintage leather armchair**|899.5|1895.0|$295.00 - $5495.00|medium|FALSE|
|**IKEA bookshelf**|42.5|||medium|FALSE|
|**Apple MacBook Pro 14-inch**|1490.0|1500.0|$1450.00 - $1525.00|medium|FALSE|
|**Antique oak dining table**|419.0|800.0|$25.00 - $3700.00|medium|FALSE|
|**Sony PlayStation 5**|235.0|255.0|$180.00 - $265.00|medium|FALSE|
|**Designer leather sofa**|2150.0|3199.0|$400.00 - $3199.00|medium|FALSE|
|**Dyson vacuum cleaner**|171.82|207.9|$100.00 - $299.00|medium|FALSE|
|**Kitchen mixer**|90.0|92.0|$85.00 - $95.00|medium|FALSE|
|**Area rug**|200.0|200.0|$200.00 - $200.00|low|TRUE|


|   |   |   |
|---|---|---|
|**reasoning**|**comparable_count**|**price_sources**|
|Limited sample of used Samsung 55-inch 4K TVs from eBay, with only 2 confirmed used pricing points|2|eBay - Samsung 55" 4K LED Smart TV: $329.95; eBay - Samsung 54.6" 4K Ultra HD Smart LED TV: $250.00|
|Calculated median price from 10 used leather armchairs of varying ages and conditions. Excluded extremely high and low outliers. Adjusted for 20-year-old chair in fair condition.|10|eBay Vintage Leather Armchair 1: $556.50; eBay Steelcase Leather Chair: $295.00; eBay Gunlocke Leather Chair: $400.00; eBay Stickley Leather Chair 1: $299.00; eBay Stickley Leather Chair 2: $695.00; eBay Leather Chair: $999.99; eBay CENTURY Leather Chair: $2100.00; eBay Pre-Owned Leather Chair 1: $1895.00; eBay Pre-Owned Leather Chair 2: $5495.00; Facebook Marketplace Leather Living Room Chair: $299.00|
|Simple depreciation heuristic for low-value item|0||
|Gathered 5 used eBay listings for 14-inch MacBook Pro in excellent condition, with prices clustered tightly around $1,450-$1,525. Median and average calculations support a recommended value of $1,490.|5|eBay Listing 1: $1499.00; eBay Listing 2: $1450.00; eBay Listing 3: $1475.00; eBay Listing 4: $1525.00; eBay Listing 5: $1500.00|
|Wide range of prices for 50-year-old oak dining tables, with most used prices falling between $150-$500. Median price calculated based on multiple sources.|9|eBay: $419.50; eBay: $500.00; eBay: $800.00; eBay: $1500.00; eBay: $3700.00; Facebook Marketplace: $25.00; Facebook Marketplace: $79.00; Facebook Marketplace: $150.00; Facebook Marketplace: $300.00|
|Prices based on current market values for 2-year-old PlayStation 5 in good condition. Multiple sources indicate used PS5s retain around 55% of original retail price. Median price reflects good condition and minimal depreciation.|8|eBay Disc Edition: $220.00; eBay Disc Edition: $235.00; eBay Disc Edition: $245.00; eBay Disc Edition: $255.00; eBay Disc Edition: $265.00; eBay Digital Edition: $180.00; eBay Digital Edition: $195.00; eBay Digital Edition: $210.00|
|Depreciation for leather furniture is typically 15-20% per year. Original price was around $3,199. After 5 years, estimated value ranges from $1,280 to $1,920, with actual marketplace listings showing values between $400-$2,600 depending on condition.|4|eBay West Elm Brooklyn Leather Sofa: $2600.00; eBay West Elm Hamilton Leather Sofa: $3199.00; Facebook Marketplace West Elm Brooklyn Sofa: $2400.00; eBay Used West Elm Leather Sofa: $400.00|
|Calculated from 6 different marketplace and eBay listings for similar Dyson V8 Absolute vacuums in used or open box condition. Prices range from $100 to $299, with a median of $171.82.|6|eBay V8 Absolute Used: $207.90; eBay V8 Absolute Open Box: $299.00; Facebook Marketplace V8 Absolute Palo Alto: $115.00; Facebook Marketplace V8 Absolute Sunnyvale: $100.00; Facebook Marketplace San Francisco V8 Cordless: $159.00; eBay V8 Absolute Pre-Owned: $149.99|
|Prices for 4-year-old KitchenAid mixers in good condition consistently range between $85-$95 on eBay, with most listings around $90|5|eBay: $90.70; eBay: $85.00; eBay: $95.00; eBay: $92.00; eBay: $88.00|
|Research failed: Error code: 429 - {'type': 'error', 'error': {'type': 'rate_limit_error', 'message': 'This request would exceed the rate limit for your organization (a708ccf8-9f4d-4798-9af5-d61f94848a74) of 50,000 input tokens per minute. For details, refer to: [https://docs.claude.com/en/api/rate-limits](https://docs.claude.com/en/api/rate-limits). You can see the response headers for current usage. Please reduce the prompt length or the maximum tokens requested, or try again later. You may also contact sales at [https://www.anthropic.com/contact-sales](https://www.anthropic.com/contact-sales) to discuss your options for a rate limit increase.'}, 'request_id': 'req_011CVFpmagy45KpMwJ5EJ8vZ'}. Using estimated value.|1||


# Areas for improvement

1.  I still don't trust LLMs to adjust difficult examples like the unbranded vintage leather chair. This item should always be flagged for human intervention.
2.  Consider using relied on depreciation data mapper. For items like the expensive couch, use API call to confirm retail value, then apply depreciation factor
3.  Consider using a vision model for image recognition for difficult items (unbranded furniture, etc.)
4.  Add human-in-the-loop feedback to the reasoning process. Have the LLM ask for additional information on certain items to help better evaluate. 



