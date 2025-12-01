# Claim Assist

LLM-powered insurance claim adjuster that automates item valuation using web search and comparable pricing analysis.

**NEW**: Now supports local inference models (llama.cpp, vLLM, Transformers) as an alternative to cloud APIs! **llama.cpp optimized for both NVIDIA and AMD GPUs.**

## Features

- **Local & Cloud Inference**: Run with local models (llama.cpp, vLLM) or cloud APIs (Claude)
- **GPU Optimized**: Native llama.cpp support with CUDA (NVIDIA) and ROCm (AMD) for superior performance
- **MCP Web Scraping**: Direct web scraping of eBay and marketplace sites instead of relying on API web search
- **Intelligent Routing**: Classifies items by complexity (simple/moderate/complex) to optimize costs
- **Insurance Industry Standards**: Applies 75th percentile pricing and outlier detection  
- **Cost Optimization**: Uses simple heuristics for low-value items, deep research for high-value items
- **Caching**: Reduces processing by caching similar items
- **Human Review Flagging**: Automatically flags items needing adjuster review

## Quick Start

### Option 1: Local Inference with llama.cpp (Recommended - Optimized for All GPUs!)

```powershell
# See LLAMACPP_AMD_SETUP.md for detailed GPU setup (NVIDIA or AMD)
# Quick version:

# For NVIDIA GPUs:
# 1. Install CUDA Toolkit from nvidia.com
# 2. Build: cmake .. -DLLAMA_CUDA=ON

# For AMD GPUs:
# 1. Install ROCm from AMD
# 2. Build: cmake .. -DLLAMA_HIPBLAS=ON -DAMDGPU_TARGETS=gfx1030

# 3. Download a GGUF model and start server
.\server.exe -m model.gguf -ngl 40 --port 8080

# 4. Install dependencies and run
pip install -r requirements-minimal.txt
$env:INFERENCE_BACKEND="llamacpp"
python -m claim_assist.main example_claims.csv
```

### Option 2: Cloud API (Legacy)

```bash
# Install full dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Run processing  
python -m claim_assist.main example_claims.csv --inference-backend anthropic
```

**Setup Guides:**
- ☁️ [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md) - **Run this online with cloud GPUs!**
- 🚀 [LLAMACPP_AMD_SETUP.md](LLAMACPP_AMD_SETUP.md) - **GPU users (NVIDIA/AMD) start here!**
- 📖 [LOCAL_SETUP.md](LOCAL_SETUP.md) - Detailed guide for all local inference options

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

## Project Structure

```
claim_assist/
├── __init__.py
├── main.py                    # CLI entry point
├── config.py                  # Configuration management
├── models/
│   ├── __init__.py
│   └── item.py               # Data models (ClaimItem, PricingResult)
├── pricing/
│   ├── __init__.py
│   ├── classifier.py         # Item complexity classifier
│   ├── researcher.py         # Price research with web search
│   └── validator.py          # Price validation logic
├── processors/
│   ├── __init__.py
│   └── claim_processor.py    # Main claim processing workflow
└── utils/
    ├── __init__.py
    ├── cache.py              # Result caching
    └── api_clients.py        # API client setup
```

## How It Works

1. **Classification**: Each item is classified as simple, moderate, or complex
2. **Routing**:
   - Low-value items (<$100): Fast heuristic pricing
   - High-value items (≥$100): Full LLM research
3. **Research**: Claude searches trusted marketplaces for comparable items
4. **Validation**: Applies insurance standards (75th percentile, outlier detection)
5. **Review Flagging**: Items with low confidence or outliers flagged for human review

## Cost Optimization

- Uses Claude Haiku for routing and simple/moderate items
- Uses Claude Sonnet only for complex vintage/rare items
- Simple depreciation heuristic for items below value threshold
- Caching prevents duplicate API calls for similar items

## Examples

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

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
