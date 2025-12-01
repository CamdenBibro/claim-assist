# Claim Assist

LLM-powered insurance claim adjuster that automates item valuation using web search and comparable pricing analysis.

**Two Simple Modes:**
1. **Local Inference** (Free, GPU-accelerated) - llama-cpp-python
2. **Cloud API** (Fast, paid) - Anthropic Claude

## Features

- **Flexible Inference**: Run locally with llama-cpp-python or use Anthropic's cloud API
- **GPU Optimized**: Native CUDA/ROCm support for superior local performance
- **MCP Web Scraping**: Direct web scraping of eBay marketplace instead of relying on API web search
- **Intelligent Routing**: Classifies items by complexity (simple/moderate/complex) to optimize costs
- **Insurance Industry Standards**: Applies 75th percentile pricing and outlier detection  
- **Cost Optimization**: Uses simple heuristics for low-value items, deep research for high-value items
- **Caching**: Reduces duplicate processing
- **Human Review Flagging**: Automatically flags items needing adjuster review

## Quick Start

### Option 1: Google Colab (EASIEST - No Setup!)

Process claims in the cloud with free GPU access:

1. Open [Google Colab](https://colab.research.google.com/)
2. Enable GPU (Runtime → Change runtime type → T4 GPU)
3. Follow the [COLAB_QUICKSTART.md](COLAB_QUICKSTART.md) guide

**Literally copy-paste and run!** No installation needed.

---

### Option 2: Local Inference with llama-cpp-python (Recommended for Local Use)

```powershell
# Install with CUDA support (NVIDIA GPUs)
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

# Download model
pip install huggingface-hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('bartowski/Meta-Llama-3.1-8B-Instruct-GGUF', 'Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf', local_dir='models')"

# Install claim-assist
pip install -r requirements-minimal.txt

# Configure and run
$env:INFERENCE_BACKEND="llamacpp_python"
$env:MODEL_PATH="models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
$env:N_GPU_LAYERS="50"  # Use -1 for all layers
python -m claim_assist.main example_claims.csv
```

---

### Option 3: Anthropic Cloud API

```bash
# Install dependencies
pip install -r requirements.txt

# Set configuration
export INFERENCE_BACKEND="anthropic"
export ANTHROPIC_API_KEY="your-api-key-here"

# Run processing  
python -m claim_assist.main example_claims.csv
```

**Setup Guides:**
- 🎯 [COLAB_QUICKSTART.md](COLAB_QUICKSTART.md) - **Start here! Free cloud GPUs, zero setup!**
- ☁️ [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md) - **More cloud options (RunPod, AWS, etc.)**
- 📖 [LOCAL_SETUP.md](LOCAL_SETUP.md) - Detailed guide for local inference

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
