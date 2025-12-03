# ClaimAssist: LLM-Powered Insurance Claim Pricing

##  Problem Statement & Overview

Home property damage reimbursement through insurance claims is tedious, expensive, and requires extensive research to adjust the price of lost items.

- **Getting a list of lost items adjusted in the first place can cost thousands**
- Adjusters/Insurance companies tend to low-ball valuation of lost items
- Although the homeowner can readjust claims for better valuations, it can take hundreds of hours for the homeowner to conduct this research manually

#### Question: "Why can't ChatGPT adjust claims?" 

Maybe it can. The purpose of this project was to explore the potential of using orchestrated LLMs to tackle claims lists. 

 **ClaimAssist** is a prototype tool that uses a **multi-agent LLM workflow** to:

- Ingest a CSV of claim items
- Automatically search online marketplaces for comparable prices
- Compute recommended replacement values with confidence scores
- Flag uncertain or risky items for human review
- Output clean CSVs suitable for adjuster workflows

 *The goal is **not** to fully automate claims, but to **augment human adjusters** with structured, explainable pricing suggestions.*

#### Takeoff Concerns and Questions:
 
*Is web-searching tool functionality more useful than feeding manually scraped data into LLMs?* 

*How expensive is this going to be?*

---

## Methodology Overview

1. **Multi-Agent LLM Workflow**
   The system is decomposed into specialized “agents”:
	 - **Router**: decides between heuristic pricing vs. LLM research
	 - **Classifier**: categorizes item complexity using Haiku 4.5
	 - **Researcher**: calls Sonnet 4.5 with a web-search tool to query eBay & Facebook Marketplace
	 - **Validator**: applies insurance-specific business rules to decide final recommendation and human review flags

2. **Tool Use / Function Calling**
   Claude models are given access to a **web search tool** restricted to:
	 - eBay
	 - Facebook Marketplace
   The model decides search queries, calls the tool, and returns structured JSON with comparable items and prices.  

3. **Prompt Engineering & JSON-Constrained Outputs**
   Prompts strongly constrain Haiku to:
	 - Query only **eBay** and **Facebook Marketplace**
	 - Return a **single JSON object** with fields like `price_sources`, `recommended_value`, `confidence`, `reasoning`, etc.
   A custom JSON extractor handles minor formatting violations.

4. **Cost-Aware Design & Routing**
  -  **Heuristic pricing** is used for **low-value items** (under $100) to avoid unnecessary API calls.  
   - **LLM-based research** is reserved for items where a human would reasonably want external comparables.  

5. **Reliability & Evaluation Patterns**
  -  The validator computes statistics (median, 75th percentile, price range, comparable count).  
   - Outlier detection and confidence scoring are used to **route items to human review** when the model is uncertain.

7. **Cost and Runtime Comparison between LLM models and tool use**
	- Comparisons between several LLMs 
	- Comparisons between architecture choices

---
### Visual Pipeline Aid
<img width="1381" height="661" alt="claimAssist-pipeline drawio" src="https://github.com/user-attachments/assets/9328ca4a-4f64-401d-80b5-5e4b3b61ad17" />


## Implementation

#### High-Level Architecture

The system follows this end-to-end pipeline:

```text
CSV Input → Value Router → Complexity Classifier → LLM Research → Validation → CSV Outputs
```

### Step-by-Step Flow

#### 1. Input: CSV File

You provide a CSV with claim items:

```csv
description,brand,condition,age,estimated_value
"Samsung 55-inch 4K TV",Samsung,good,3 years,800
```

Each row becomes a `ClaimItem` object.

---

#### 2. Value-Based Routing 

Simply filters out low valued items for proof-of-concept.

```python
# claim_assist/processors/claim_processor.py
if item.estimated_value < threshold:  # Default: $100
    return simple_pricing(item)  # Fast heuristic (no LLM)
else:
    return full_llm_research(item)  # Haiku + web search
```

- **Low-value items (\< $100)**
  - Use a simple **depreciation heuristic** based on age and condition
  - **No LLM / web search call** → $0 cost
  - Example: IKEA bookshelf → $42.50

- **High-value items (≥ $100)**
  - Use **Haiku** with web search on eBay + Facebook Marketplace
  - Proceed through classification, research, validation

---

#### 3. Complexity Classification (Haiku 3.5)

For web-research, Sonnet 4.5 is larger and more expensive than Haiku 4.5, and results in better web-research results. This complexity classification determines when to use Sonnet 4.5 or  Haiku 4.5. 

```python
# claim_assist/pricing/classifier.py
ItemClassifier.classify(item)
```

**What it does:**

- Calls **Claude 3.5 Haiku** with a short prompt describing:
  - Item description, brand, condition, age  
- Returns a **complexity label**:

```json
{
  "complexity": "simple",
  "reasoning": "Standard consumer electronics, readily available"
}
```

---

#### 4. Research with Web Search (eBay + Facebook Only)

```python
# claim_assist/pricing/researcher.py
PriceResearcher.research(item)
```

**Prompt construction:**

``` python
search_prompt = f"""You are an insurance claim adjuster evaluating replacement costs. Use web search to find VALID comparable prices.

        ITEM TO PRICE:
        - Description: {item.description}
        - Brand: {item.brand or 'unbranded'}
        - Condition: {item.condition or 'used'}
        - Age/Year: {item.age or 'unknown'}
        - Estimated Value: ${item.estimated_value or 'unknown'}

        SEARCH STRATEGY:
        1. Search ONLY eBay and Facebook Marketplace for items matching this description
        2. For EACH listing found, evaluate if it's a valid comparable
        3. REJECT listings that are:
        - Refurbished, renewed, or certified pre-owned
        - From auctions (only final sale/Buy It Now prices)
        - Significantly different condition than the original item
        - Different model/generation/variant
        - Bundle deals or parts-only listings
        - More than 5 years different in age (if age is known)
        - Priced as extreme outliers (>3x or <0.3x median)
        4. ACCEPT only listings that match condition, model, and age reasonably

        IMPORTANT: Include ONLY valid comparable prices. If fewer than 3 valid comparables found, note this in reasoning.

        Return ONLY this exact JSON format with NO additional text:
        {{
        "price_sources":[
        {{"source":"eBay - [exact item title]","price":number,"condition":"used/new","notes":"brief validation note"}},
        ...
        ],
        "comparable_count":number_of_valid_items_found,
        "total_listings_evaluated":total_number_checked,
        "recommended_value":calculated_value,
        "confidence":"low|medium|high",
        "reasoning":"Explain: How many comparables found? Why were some rejected? How did you calculate recommended_value? Any data quality concerns?",
        "search_queries_used":["query 1","query 2",...]
        }}

        CONFIDENCE SCORING:
        - high: 5+ valid comparables, tight price clustering, good condition match
        - medium: 3-4 comparables OR some condition variance OR moderate price spread
        - low: <3 comparables OR high variance OR poor condition match OR search failed

        Rules:
        - NO markdown formatting
        - NO explanatory text outside JSON
        - Use double quotes for strings
        - Numbers must not be quoted (use raw numbers like 650, not "650")
        - Include condition and notes for each price source
        - recommended_value should be median of valid comparables (or mean if <5 items)
        - If no valid comparables, use estimated_value with "low" confidence"""

model = self.complex_model if complexity == Complexity.COMPLEX.value else self.simple_model

```

- Includes:
  - Description, brand, condition, age, and estimated value  
  - Explicit instructions:
	- Search **only eBay and Facebook Marketplace**  
	- Prefer **used** or **pre-owned** listings  
	- Return a JSON with:
	  - `price_sources`
	  - `recommended_value`
	  - `percentile_75`
	  - `price_range`
	  - `confidence`
	  - `reasoning`
	  - `comparable_count`

**API call:**

```python
client.messages.create(
    model="claude-3-5-haiku-latest",
    messages=[{"role": "user", "content": prompt}],
    tools=[{
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 5
    }]
)
```

**What Haiku does:**

- Uses the `web_search` tool to query:
  - `site:ebay.com` and `site:facebook.com/marketplace`  
- Extracts prices from relevant listings  
- Produces structured data like:

```json
{
  "price_sources": [
    {"source": "eBay", "title": "...", "price": 650},
    {"source": "eBay", "title": "...", "price": 720}
  ],
  "recommended_value": 690,
  "percentile_75": 720,
  "price_range": "$650.00 - $720.00",
  "comparable_count": 2,
  "confidence": "medium",
  "reasoning": "Limited used listings for this TV model; prices cluster in the mid-600s to low-700s."
}
```

---

#### 5. JSON Extraction

```python
# claim_assist/pricing/researcher.py
_extract_json_from_text(response_text)
```

Claude models sometimes surrounds the JSON with explanatory text. The extractor:

1. Locates the first `{`
2. Tracks nested braces and quoted strings
3. Extracts a **single complete JSON object**
4. Handles escaped quotes and special characters


---

#### 6. Validation (Insurance Standards Logic)

```python
# claim_assist/pricing/validator.py
PriceValidator.validate(item, pricing_data)
```

**a) Compute summary stats**

- Median price
- 75th percentile (`percentile_75`)
- Min–max range → `price_range`

**b) Confidence adjustment**

If Claude struggles finding search matches, the number of comparable items is low. 

```python
if comparable_count < 3:
    confidence = "low"
elif comparable_count >= 5 and research_confidence == "high":
    confidence = "high"
else:
    confidence = "medium"
```

**c) Outlier detection**

```python
if abs(recommended_value - median) > median * 0.5:
    flag_for_human_review = True
```

**d) Human review criteria**

Items are flagged for human verification if:

- `comparable_count < 3`, or
- Recommended value is \>50% away from the median, or
- Research confidence is `"low"`, or
- Research fails (e.g., rate-limit or network error)

---

#### 7. CSV Output

```python
# claim_assist/processors/claim_processor.py
results.to_csv("claim_evaluation_results.csv")
```

The system generates **two CSV files**:

1. **Full Results** – all items with valuations and sources
2. **Items for Review** – only items flagged as `needs_human_review = TRUE`

These can be directly consumed by adjusters or visualized in a BI tool.

---

###  File Structure

```text
claim_assist/
├── models/
│   └── item.py           # Data models (ClaimItem, PricingResult)
├── pricing/
│   ├── classifier.py     # Complexity classification via Haiku
│   ├── researcher.py     # Haiku + Sonnet + web search 
│   └── validator.py      # Insurance standards & human-review logic
├── processors/
│   └── claim_processor.py  # Pipeline orchestration
├── utils/
│   ├── cache.py          # Result caching (keyed by description/brand/condition)
│   └── api_clients.py    # Anthropic client setup
├── config.py             # Thresholds, model names, etc.
└── main.py               # CLI entry point
```



---

###  Model Version / Architecture

- **Base Model:** `claude-3-5-haiku-latest & claude-3-5-sonnet-latest`
- **Roles in system:**
  - **Router:** Business logic (Python) – no LLM  
  - **Classifier, Researcher:** Haiku / Sonnet with web search tool  
  - **Validator:** Pure Python rules  


---


##  Running ClaimAssist

Assuming Python + dependencies are installed and environment variables are set:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set Anthropic API key
export ANTHROPIC_API_KEY="your_key_here"

# 3. Run on an example file
python -m claim_assist.main   --input data/example_claims.csv   --output_dir outputs/
```

You should see:

- `outputs/claim_evaluation_results.csv`
- `outputs/claim_items_for_review.csv`

### Example input: 

|   |   |   |   |   |   |
|---|---|---|---|---|---|
|**description**|**brand**|**condition**|**age**|**features**|**estimated_value**|
|**Samsung 55-inch 4K TV**|Samsung|good|3 years|Smart TV QLED|800|
|**Vintage leather armchair**|Unknown|fair|20 years|Genuine leather|300|
|**IKEA bookshelf**|IKEA|excellent|1 year|Billy series|50|
|**Apple MacBook Pro 14-inch**|Apple|excellent|1 year|M1 Pro 16GB RAM|2000|
|**Antique oak dining table**|Unknown|good|50 years|Solid oak handcrafted|800|
|**Sony PlayStation 5**|Sony|good|2 years|Digital Edition|400|
|**Designer leather sofa**|West Elm|good|5 years|Italian leather 3-seater|1500|
|**Dyson vacuum cleaner**|Dyson|excellent|6 months|V15 Detect|600|
|**Kitchen mixer**|KitchenAid|good|4 years|Stand mixer Artisan|300|

### Example output: 

|                               |                       |                   |                     |                |                        |
| ----------------------------- | --------------------- | ----------------- | ------------------- | -------------- | ---------------------- |
| **item**                      | **recommended_value** | **percentile_75** | **price_range**     | **confidence** | **needs_human_review** |
| **Samsung 55-inch 4K TV**     | 300.0                 | 300.0             | $300.00 - $300.00   | low            | TRUE                   |
| **Vintage leather armchair**  | 250.0                 | 275.0             | $225.00 - $275.00   | medium         | FALSE                  |
| **IKEA bookshelf**            | 42.5                  |                   |                     | medium         | FALSE                  |
| **Apple MacBook Pro 14-inch** | 1841.0                | 1875.0            | $1799.00 - $1875.00 | medium         | FALSE                  |
| **Antique oak dining table**  | 533.0                 | 650.0             | $450.00 - $650.00   | medium         | FALSE                  |
| **Sony PlayStation 5**        | 377.0                 | 395.0             | $360.00 - $395.00   | medium         | FALSE                  |
| **Designer leather sofa**     | 755.4                 | 1039.2            | $477.00 - $1039.20  | medium         | FALSE                  |
| **Dyson vacuum cleaner**      | 373.0                 | 450.0             | $310.00 - $450.00   | medium         | FALSE                  |
| **Kitchen mixer**             | 90.7                  | 90.7              | $90.70 - $90.70     | low            | TRUE                   |
| **Area rug**                  | 175.0                 | 190.0             | $160.00 - $190.00   | medium         | FALSE                  |

|                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |                      |                                                                                                                                                                                                                              |                                                                                                                                                                                                                                                                              |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **reasoning**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | **comparable_count** | **price_sources**                                                                                                                                                                                                            | **search_queries**                                                                                                                                                                                                                                                           |
| Limited valid comparables found. Most listings were for refurbished, open-box, or new TVs which were rejected. Only one local marketplace listing met criteria. Low sample size reduces confidence in pricing. <cite index='7-3,7-4'>4K TVs and smart capabilities can impact resale value</cite>. <cite index='7-5,7-6'>Initial cost and local market demand influence pricing</cite>.                                                                                                                                    | 1                    | OfferUp - Samsung 55 inch 4K TV smart: $300.00                                                                                                                                                                               | Samsung 55-inch 4K TV used 3 years old marketplace                                                                                                                                                                                                                           |
| Found 3 valid comparables out of 12 total listings. Rejected many listings due to condition mismatch, auction status, or refurbished status. Price range is tight ($225-$275), suggesting consistent valuation for vintage leather armchairs in fair condition. Recommended value set at median price of $250.                                                                                                                                                                                                             | 3                    | eBay - Vintage Leather Armchair (Used): $250.00; eBay - Leather Vintage Armchair: $275.00; eBay - Used Leather Armchair: $225.00                                                                                             | vintage leather armchair used site:[ebay.com](http://ebay.com), vintage leather armchair used condition "buy it now" site:[ebay.com](http://ebay.com) -refurbished, vintage leather armchair used 20 years old "buy it now" price condition                                  |
| Simple depreciation heuristic for low-value item                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | 0                    |                                                                                                                                                                                                                              |                                                                                                                                                                                                                                                                              |
| Found 3 valid comparable listings on eBay for 14-inch MacBook Pro from 2022 with matching specs (M2 Pro, 16GB RAM, 512GB SSD) in excellent condition. Prices clustered tightly between $1799-$1875. Recommended value calculated as median of valid comparables. Rejected listings included refurbished items, different generations, and listings with incomplete specifications.                                                                                                                                         | 3                    | eBay - Apple MacBook Pro 14" 2022 M2 Pro 16GB 512GB Space Gray: $1850.00; eBay - Apple MacBook Pro 14" 2022 M2 Pro 16GB 512GB Space Gray: $1799.00; eBay - Apple MacBook Pro 14" 2022 M2 Pro 16GB 512GB Space Gray: $1875.00 | Apple MacBook Pro 14-inch 2022 used excellent condition eBay, Apple MacBook Pro 14-inch 2022 used excellent condition Facebook Marketplace prices                                                                                                                            |
| Three valid comparables found with prices ranging from $450 to $650. <cite index='7-20:23'>Current market shows challenges selling dining room furniture due to changing home trends, which impacts pricing</cite>. <cite index='10-1,10-2'>Prices have declined from around $1000 a decade ago to $450-$650 currently</cite>. Median price calculated at $533 with moderate price spread. <cite index='14-2:4'>Oak tables remain a durable investment with minimal upkeep, maintaining some value</cite>.                 | 3                    | eBay - Vintage Oak Dining Table: $650.00; eBay - Antique Oak Dining Table: $450.00; Expert Appraisal Source: $500.00                                                                                                         | antique oak dining table 50 years old "Buy It Now" eBay Marketplace, vintage oak dining table 50 years old "Buy It Now" Facebook Marketplace, "oak dining table" vintage used condition eBay "Buy It Now" price, vintage oak dining table 50 years old actual selling prices |
| Found 3 valid comparable listings for PlayStation 5 Disc Edition in good condition. Prices ranged from $360 to $395, with an average of $377. Rejected multiple listings due to incomplete sets, damaged controllers, or bundle deals. Confidence is medium due to reasonable price clustering and condition match.                                                                                                                                                                                                        | 3                    | eBay - Sony PlayStation 5 Disc Edition 825GB Console Good Condition: $375.00; eBay - Sony PlayStation 5 Disc Edition 825GB White Console: $395.00; eBay - Sony PlayStation 5 Disc Edition Console: $360.00                   | PlayStation 5 used good condition, PS5 used eBay marketplace                                                                                                                                                                                                                 |
| Used West Elm leather sofas show significant price variation. Sofas typically drop about 20% in the first year and then around 7% each year. Premium brands like West Elm get a 10% premium, with leather in good condition adding another 10%. Prices ranged from $477 to $1,039.20, with an average of $755.40. Confidence is medium due to limited comparable listings and price variance.                                                                                                                              | 3                    | eBay - West Elm Leather Sofa: $1039.20; eBay - West Elm Leather Sofa: $750.00; Reperch - West Elm Leather Sofa: $477.00                                                                                                      | West Elm leather sofa used, West Elm sofa resale value                                                                                                                                                                                                                       |
| Found 3 comparable Dyson vacuum listings on local marketplaces. Prices range from $310 to $450, with a median of $360. Slight variance due to different models (V10, V11, V15) and condition. Recommended value calculated as the median price. Confidence is medium due to limited sample size and model variations.                                                                                                                                                                                                      | 3                    | eBay - Dyson V11 Torque Drive Stick Vacuum Cleaner: $360.00; eBay - Dyson V15 Detect Cordless Vacuum: $450.00; eBay - Dyson V10 Cyclone Total Clean+ Vacuum: $310.00                                                         | Dyson vacuum cleaner used excellent condition eBay, Dyson vacuum cleaner used excellent condition Facebook Marketplace                                                                                                                                                       |
| Only 1 valid comparable found on eBay. Multiple listings were rejected due to being refurbished, being part of bundle deals, or having significant condition issues. The single valid listing was a used mixer in similar condition to the original item, priced at $90.70. Low confidence due to limited comparables and small sample size.                                                                                                                                                                               | 1                    | eBay - KitchenAid Classic Series 4-1/2-Quart Stand Mixer Used: $90.70                                                                                                                                                        | KitchenAid mixer used good condition 4 years old selling price eBay                                                                                                                                                                                                          |
| Three valid comparables found after evaluating multiple listings. Pricing is consistent with the estimated original value of $200. Since the rug is used, it will not sell for full price, but this allows recouping some of the original investment. Rug value is complex and can vary based on multiple subjective factors. Rejected listings included auction items, refurbished rugs, and those with significant damage. Age does impact value, with condition being crucial - better condition maintains higher value | 3                    | eBay - Used Area Rug 10 Years Old: $175.00; eBay - Vintage Area Rug Pre-owned: $190.00; Facebook Marketplace - Used Area Rug: $160.00                                                                                        | area rug 10 years old used condition eBay marketplace, used area rug 10 years old fair condition eBay marketplace, 10-year-old area rug fair condition used price on Facebook Marketplace                                                                                    |


---

## Assessment & Evaluation

### Tested both Sonnet and Haiku for complex research

For the same 10 item list:

|            |              |          |
| ---------- | ------------ | -------- |
| **Model**  | **Run Time** | **Cost** |
| **Haiku**  | 4:10         | $0.28    |
| **Sonnet** | 6:49         | $0.63    |
|            |              |          |

Takeaways:
- Sonnet
	-  Surprisingly stubborn,  often deviates outside of the restricted websites listed in the prompt
	-  Significantly more expensive and slow
	
- Haiku (Top pick)
	- Far more efficient and cost effective than Sonnet / although still slow
	- More consistent web searches, and better at following prompt rules

## Alternative Approach

What if we manually web-scraped, and fed the data directly into a locally hosted series of models, requiring zero API cost?




---

## Critical Analysis & Impact

### Should people use this tool?  - Maybe? If the cost was lower...

- It is a difficult task for current web-based tools to perform **efficient** web searches.
- The models need a lot of time to reason and search the web, and this can cost a lot.  

To have confidence in the models, we would need to increase parameters to the API calls.
	- Allow more web searches
		- ```max_search(5) # set higher```
		- Set prompt that requires more comparable results, pushing the models to perform more extensive research.
	  
**However, the cost and runtime would skyrocket**

###  What It Reveals / Suggests

If deployed carefully with human oversight, this system could help you chug through extensive claims lists and help you find decent valuations that don't undercut actual value. **This would bring real value**

- **LLMs are strong at “last-mile” reasoning** when given tool access and structured prompts, but:
  - They struggle most on **edge cases** (e.g., unbranded vintage furniture)  
  - They can be brittle under rate limits and JSON formatting constraints  
- The “right” architecture balances:
  - **Heuristics + rules** (for low-value or simple items)  
  - **LLM reasoning + web search** (for complex, subjective items)  
  - **Human review** (for high-risk or low-confidence outputs)  

### Difficult to validate

**Insurance companies invest millions in creating datasets that serve this purpose**. This tool would be useful to help individuals dispute low claim valuations, but it's a long ways away from replacing claims adjusters.

---


###  Ethical & Bias Considerations

1. **Data Source Bias**
   2. Prices come only from **eBay** and **Facebook Marketplace**, which may not represent:
	 - All geographic regions
	 - All demographic groups
	 - Specific niche or luxury markets
   3. This can bias valuations lower or higher for certain items.

4. **LLM Hallucination & Misinterpretation**
   5. Claude might:
	 - Misread item descriptions
	 - Pick comparable items that aren’t truly similar
   6. Mitigations:
	 - Require multiple comparables when possible
	 - Flag low-comparable-count items for human review
	 - Use conservative confidence scoring and clear reasoning text.

7. **High-Risk Items**
   8. Complex, unbranded, or highly valuable items (e.g., **vintage leather armchairs**, **antique tables**) can be mispriced.  
   9. Design choice: such items are **often flagged** for human intervention, explicitly recommends **never fully trusting LLM output alone** for these cases.

10. **Transparency & Auditability**
   11. Each recommendation includes:
	 - Textual reasoning
	 - Comparable count
	 - Price sources (with marketplace + price)

This helps human reviewers audit and override the model when needed.

---

### Data Card (Marketplace Data)

- **Data Sources:**
  - **eBay** and **Facebook Marketplace** search results, via web search tool  
- **Data Type:**
  - Listing titles, prices, and sometimes description snippets  
- **Preprocessing:**
  - Done implicitly by Haiku in its tool-calling workflow  
  - The system aggregates prices and computes median, 75th percentile, etc.  
- **Known Issues & Limitations:**
  - Prices may be:
	- “As-is” or broken items mixed with good condition items
	- Regional (e.g., local pickup vs. shipping)
- **Privacy:**
  - Uses public marketplace data only; no private user data or PHI is ingested.

---


### Next Steps

Areas for improvement / next steps:

1. **Stronger Handling for Difficult Items**
   2. Vintage, unbranded, or luxury furniture should **always be flagged** for human review, even if Haiku seems confident.

3. **Depreciation Data Mapper**
   4. Integrate a more principled **depreciation module**:
	 - Use API calls (or tables) to retrieve original retail price
	 - Apply category-specific depreciation curves for items like sofas, appliances, etc.

5. *****Vision Model Integration**
   6. Add a vision model to handle **item photos**:
	 - Identify furniture type, style, material, and brand cues
	 - Assist especially with **unbranded furniture** and **visually distinctive items**.

7. **Human-in-the-Loop Feedback**
   8. Let adjusters:
	 - Approve/override model recommendations
	 - Provide feedback on whether comparable items were relevant
   9. Use this feedback to improve prompts and rules over time.

---




## Installation and Basic Guide

```bash
pip install -r requirements.txt
```

## Configuration

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Optional configuration via environment variables:

```bash
export VALUE_THRESHOLD=100      # Minimum value for deep research (default: 100)
export ENABLE_CACHE=true        # Enable result caching (default: true)
```

## Usage

### Command Line

```bash
python -m claim_assist.main input_claims.csv
```

With options:

```bash
python -m claim_assist.main input_claims.csv \
    --output results.csv \
    --review needs_review.csv \
    --threshold 150 \
    --api-key "your-key"
```

### Input CSV Format

Required column:
- `description`: Item description

Optional columns:
- `brand`: Brand name
- `condition`: new|excellent|good|fair|poor
- `age`: Item age
- `features`: Special features or materials
- `estimated_value`: Estimated replacement value

Example:

```csv
description,brand,condition,age,features,estimated_value
"Samsung 55-inch 4K TV",Samsung,good,3 years,Smart TV QLED,800
"Vintage leather armchair",Unknown,fair,20 years,Genuine leather,300
"IKEA bookshelf",IKEA,excellent,1 year,Billy series,50
```

### Output

The tool generates two CSV files:

1. **Complete Results** (`claim_evaluation_results.csv`): All items with pricing details
2. **Human Review** (`items_for_human_review.csv`): Items flagged for manual review

Output columns:
- `item`: Item description
- `recommended_value`: Recommended replacement value
- `percentile_75`: 75th percentile of comparable prices
- `price_range`: Range of comparable prices found
- `confidence`: high|medium|low
- `needs_human_review`: Boolean flag
- `reasoning`: Explanation of valuation
- `comparable_count`: Number of comparables found
- `price_sources`: Detailed price-to-source mapping (e.g., "eBay: $550.00; Amazon: $600.00; Best Buy: $650.00")
- `search_queries`: Search queries used to find comparables



### Process a claim file

```bash
python -m claim_assist.main fire_damage_claim.csv
```

### Custom threshold and output files

```bash
python -m claim_assist.main water_damage_claim.csv \
    --threshold 200 \
    --output water_damage_results.csv \
    --review water_damage_review.csv
```

### Disable caching

```bash
python -m claim_assist.main claim.csv --no-cache
```

## Development

### Run tests

```bash
pytest tests/
```

### Code formatting

```bash
black claim_assist/
```

### Linting

```bash
flake8 claim_assist/
```

###  Intended Uses & License

**Intended use:**

- Educational and prototyping tool demonstrating:
  - LLM tool use for marketplace search  
  - Cost-aware routing in an insurance-like workflow  
- Decision **support** for human adjusters, **not** a fully autonomous system.  

**Not intended for:**

- Production deployment on live insurance claims without additional validation
- Fully automated claim approvals or denials
- Any use where a human is not in the loop for high-value or ambiguous items

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
