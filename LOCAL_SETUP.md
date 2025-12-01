# Local Inference Setup Guide

This guide shows how to set up Claim Assist with local inference models instead of using Claude API.

## Quick Setup (Recommended: Ollama)

### 1. Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from https://ollama.ai/download
```

### 2. Start Ollama and Download a Model

```bash
# Start Ollama server
ollama serve

# In a new terminal, download a model
ollama pull llama3.1:8b

# Or use a smaller model for faster inference
ollama pull llama3.2:3b
```

### 3. Install Python Dependencies

```bash
# Minimal setup (recommended)
pip install -r requirements-minimal.txt

# Or full setup with all optional dependencies  
pip install -r requirements.txt
```

### 4. Test the Setup

```bash
python test_local_integration.py
```

### 5. Run Claim Processing

```bash
# Using Ollama (default)
python -m claim_assist.main example_claims.csv

# Or explicitly specify Ollama settings
python -m claim_assist.main example_claims.csv \
    --inference-backend ollama \
    --model-name llama3.1:8b \
    --inference-url http://localhost:11434
```

## Alternative Backends

### vLLM (OpenAI-Compatible API)

```bash
# Install vLLM
pip install vllm

# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
    --model microsoft/DialoGPT-medium \
    --port 8000

# Use with Claim Assist
python -m claim_assist.main example_claims.csv \
    --inference-backend openai_compatible \
    --model-name microsoft/DialoGPT-medium \
    --inference-url http://localhost:8000/v1
```

### Transformers (Direct Python)

```bash
# Install transformers
pip install torch transformers

# Use with Claim Assist
python -m claim_assist.main example_claims.csv \
    --inference-backend transformers \
    --model-name microsoft/DialoGPT-medium
```

## Configuration via Environment Variables

Instead of command-line arguments, you can set environment variables:

```bash
export INFERENCE_BACKEND=ollama
export MODEL_NAME=llama3.1:8b
export INFERENCE_BASE_URL=http://localhost:11434
export VALUE_THRESHOLD=100
export SCRAPING_DELAY=1.0
export MAX_RESULTS_PER_SOURCE=10

python -m claim_assist.main example_claims.csv
```

## Legacy Anthropic Support

For backward compatibility, you can still use Anthropic's API:

```bash
export ANTHROPIC_API_KEY=your_key_here

python -m claim_assist.main example_claims.csv \
    --inference-backend anthropic
```

## Troubleshooting

### "Inference client is not available"
- Make sure Ollama is running: `ollama serve`
- Check if model is downloaded: `ollama list`
- Test Ollama directly: `curl http://localhost:11434/api/tags`

### "No comparable prices found"
- Web scraping may be rate-limited
- Try increasing `--scraping-delay` 
- Some sites may block automated requests

### Poor LLM Results
- Try a larger model: `ollama pull llama3.1:70b` 
- Adjust temperature settings in the code
- Check if your model is appropriate for JSON parsing

### Memory Issues
- Use smaller models: `llama3.2:3b` instead of `llama3.1:8b`
- Close other applications
- For transformers backend, ensure you have enough RAM/VRAM

## Performance Optimization

### Model Selection
- **Fast + Small**: `llama3.2:3b` (2GB RAM)
- **Balanced**: `llama3.1:8b` (4.7GB RAM)  
- **Best Quality**: `llama3.1:70b` (40GB RAM, requires GPU)

### Scraping Settings
```bash
# Faster scraping (higher risk of being blocked)
export SCRAPING_DELAY=0.5
export MAX_RESULTS_PER_SOURCE=5

# Slower scraping (more reliable)
export SCRAPING_DELAY=2.0  
export MAX_RESULTS_PER_SOURCE=15
```

### Caching
```bash
# Enable caching (default)
export ENABLE_CACHE=true

# Disable for fresh results every time
export ENABLE_CACHE=false
```

## Cost Comparison

| Method | Cost per 100 items | Setup | Speed |
|--------|-------------------|--------|--------|
| Claude API | $0.50-2.00 | Easy | Fast |
| Local Ollama | $0.00 | Medium | Medium |
| Local Transformers | $0.00 | Hard | Slow |

## Next Steps

Once your local setup is working:

1. Process your own claim files
2. Adjust thresholds and settings for your use case  
3. Customize web scraping sources
4. Train or fine-tune models on your data