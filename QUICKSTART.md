# Quick Start Guide

Get started with Claim Assist in 5 minutes.

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install -e .
```

## Step 2: Set API Key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Step 3: Try the Example

Run the example claims file:

```bash
python -m claim_assist.main example_claims.csv
```

This will:
1. Process 10 sample insurance claim items
2. Generate `claim_evaluation_results.csv` with all results
3. Generate `items_for_human_review.csv` with flagged items
4. Display a summary of the claim

## Understanding the Output

### Results File (`claim_evaluation_results.csv`)

Contains all items with:
- **recommended_value**: Final valuation
- **confidence**: high/medium/low
- **needs_human_review**: Boolean flag
- **reasoning**: Explanation of how value was determined
- **comparable_count**: Number of similar items found

### Review File (`items_for_human_review.csv`)

Contains only items that need manual review due to:
- Low confidence (< 3 comparables)
- Price outliers (> 50% deviation)
- Research failures

## Common Usage Patterns

### Process a Different File

```bash
python -m claim_assist.main your_claims.csv
```

### Higher Value Threshold

Only use deep research for items over $200:

```bash
python -m claim_assist.main claims.csv --threshold 200
```

### Custom Output Files

```bash
python -m claim_assist.main claims.csv \
    --output my_results.csv \
    --review my_review.csv
```

### Disable Caching

For fresh results every time:

```bash
python -m claim_assist.main claims.csv --no-cache
```

## Input CSV Format

Minimum required format:

```csv
description
"Samsung TV"
"Leather sofa"
"IKEA bookshelf"
```

Full format with all optional fields:

```csv
description,brand,condition,age,features,estimated_value
"Samsung 55-inch TV",Samsung,good,3 years,4K Smart TV,800
"Leather sofa",Unknown,fair,10 years,3-seater,600
```

## What Happens Behind the Scenes

1. **Low-value items** (< threshold): Fast depreciation calculation
2. **High-value items** (≥ threshold):
   - Classify complexity (simple/moderate/complex)
   - Search web for comparable prices
   - Apply insurance standards (75th percentile)
   - Flag outliers for review

## Cost Optimization

- Low-value items: ~$0 (heuristic only)
- Simple items: ~$0.001-0.002 per item (Haiku)
- Complex items: ~$0.015-0.03 per item (Sonnet)
- Cached items: $0 (instant)

**Typical cost for 100-item claim: $0.50-2.00**

## Troubleshooting

### "ANTHROPIC_API_KEY is required"

Set your API key:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or pass it directly:
```bash
python -m claim_assist.main claims.csv --api-key "sk-ant-..."
```

### "Input file not found"

Check the file path is correct:
```bash
ls -l your_claims.csv
```

### Low confidence results

Items with < 3 comparables will have low confidence. To improve:
- Add more details in description
- Include brand and condition
- Provide estimated_value as a baseline

## Next Steps

- Review [README.md](README.md) for full documentation
- Run tests: `pytest claim_assist/tests/`
- Customize thresholds in [config.py](claim_assist/config.py)
