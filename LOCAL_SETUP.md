

# Local Inference Setup Guide

This guide shows how to set up Claim Assist with local inference models instead of using Claude API.

## 🚀 llama.cpp Setup (RECOMMENDED - Optimized for All GPUs) ⚡

**Best for:** NVIDIA GPUs (RTX series), AMD Radeon GPUs (RX 6000/7000 series), and CPU inference

llama.cpp provides superior GPU support through CUDA (NVIDIA) and ROCm (AMD) with excellent performance.

#### 1. Install GPU Runtime (Choose Based on Your GPU)

**For NVIDIA GPUs:**
```powershell
# Download and install CUDA Toolkit from NVIDIA
# https://developer.nvidia.com/cuda-downloads

# Verify installation
nvcc --version
nvidia-smi
```

**For AMD GPUs:**
```powershell
# Download ROCm installer from AMD
# https://www.amd.com/en/graphics/servers-solutions-rocm

# Verify installation
rocminfo
```

#### 2. Build llama.cpp with GPU Support

**For NVIDIA GPUs (CUDA):**
```powershell
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build && cd build
cmake .. -G "Visual Studio 17 2022" -A x64 -DLLAMA_CUDA=ON
cmake --build . --config Release
```

**For AMD GPUs (ROCm):**

**For AMD GPUs (ROCm):**
```powershell
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build && cd build

# Identify your GPU architecture first
rocminfo | findstr "Name:"
# RX 6000 series = gfx1030, RX 7000 series = gfx1100

cmake .. -G "Visual Studio 17 2022" -A x64 `
  -DLLAMA_HIPBLAS=ON `
  -DCMAKE_C_COMPILER=clang `
  -DCMAKE_CXX_COMPILER=clang++ `
  -DAMDGPU_TARGETS=gfx1030

cmake --build . --config Release
```

**See [LLAMACPP_AMD_SETUP.md](LLAMACPP_AMD_SETUP.md) for detailed instructions for both NVIDIA and AMD GPUs.**

#### 3. Download a Model (GGUF Format)

```powershell
# Create a models directory
mkdir models
cd models

# Download Llama 3.1 8B (quantized for better performance)
# Q4_K_M = 4-bit quantization, good balance of speed/quality
curl -L -o llama-3.1-8b-instruct-q4_k_m.gguf "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

# Or for faster processing (smaller model):
curl -L -o llama-3.2-3b-instruct-q4_k_m.gguf "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
```

#### 4. Start llama.cpp Server with AMD GPU

```powershell
# Navigate to build directory
cd ..\build\bin

# Start server with GPU acceleration
# Adjust -ngl (GPU layers) based on your VRAM: 32 for 8GB, 40 for 12GB, 50+ for 16GB+
.\server.exe -m ..\..\models\llama-3.1-8b-instruct-q4_k_m.gguf `
  -ngl 40 `
  --port 8080 `
  --host 0.0.0.0 `
  -c 4096 `
  --n-gpu-layers 40

# The server will start on http://localhost:8080
```

#### 5. Configure Claim Assist to Use llama.cpp

```powershell
# Set environment variables
$env:INFERENCE_BACKEND="llamacpp"
$env:MODEL_NAME="llama-3.1-8b-instruct"
$env:INFERENCE_BASE_URL="http://localhost:8080/v1"

# Run claim processing
python -m claim_assist.main example_claims.csv
```

**Performance Tips for AMD GPUs:**
- **More GPU layers** (`-ngl`): Faster but needs more VRAM
- **Quantization levels**: Q4_K_M (fast) → Q5_K_M (balanced) → Q6_K (quality)
- **Context size** (`-c`): 2048 (fast) → 4096 (balanced) → 8192 (slow)
- Monitor GPU usage with: `rocm-smi`

---

## Common Setup Steps

### Install Python Dependencies

```bash
# Minimal setup (recommended)
pip install -r requirements-minimal.txt

# Or full setup with all optional dependencies  
pip install -r requirements.txt
```

### Test the Setup

```bash
python test_local_integration.py
```

### Run Claim Processing

```bash
# Using llama.cpp (recommended for AMD)
python -m claim_assist.main example_claims.csv

# Or explicitly specify backend
python -m claim_assist.main example_claims.csv `
    --inference-backend llamacpp `
    --model-name llama-3.1-8b-instruct `
    --inference-url http://localhost:8080/v1
```

---

## 📊 Backend Comparison

| Backend | NVIDIA GPU | AMD GPU | CPU | Setup | Performance |
|---------|------------|---------|-----|--------|-------------|
| **llama.cpp** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Medium | Excellent |
| **vLLM** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ | Hard | Excellent |
| **Transformers** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | Easy | Fair |

**Key Takeaways:**
- **NVIDIA GPU users**: llama.cpp or vLLM are excellent choices
- **AMD GPU users**: llama.cpp is the best choice (requires ROCm setup)
- **No GPU**: llama.cpp with CPU is efficient
- **Maximum control**: llama.cpp offers the most tuning options

---

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

```powershell
# For llama.cpp
$env:INFERENCE_BACKEND="llamacpp"
$env:MODEL_NAME="llama-3.1-8b-instruct"
$env:INFERENCE_BASE_URL="http://localhost:8080/v1"

# Common settings
$env:VALUE_THRESHOLD="100"
$env:SCRAPING_DELAY="1.0"
$env:MAX_RESULTS_PER_SOURCE="10"

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

### llama.cpp Issues (GPU-specific)

**NVIDIA: "CUDA not found" or GPU not detected**
- Verify CUDA installation: `nvcc --version` and `nvidia-smi`
- Check CUDA Toolkit is installed: Download from nvidia.com
- Ensure CUDA bin directory is in PATH
- Update NVIDIA drivers to latest version
- Rebuild with: `cmake .. -DLLAMA_CUDA=ON`

**AMD: "ROCm not found" or GPU not detected**
- Verify ROCm installation: `rocminfo`
- Check GPU is supported: RX 6000/7000 series work best
- Try rebuilding with correct `AMDGPU_TARGETS` for your GPU:
  - RX 6600-6950 XT: `gfx1030`
  - RX 7600-7900 XTX: `gfx1100`
  - Verify with: `rocminfo | grep "Name:"`

**"Out of memory" errors**
- Reduce GPU layers: Try `-ngl 20` or `-ngl 10`
- Use smaller quantization: Download Q3_K_M or Q2_K models
- Reduce context size: `-c 2048` instead of 4096
- Check VRAM usage: `rocm-smi`

**Server won't start or crashes**
- Check port isn't in use: `netstat -ano | findstr :8080`
- Try CPU-only mode first: Remove `-ngl` parameter
- Update GPU drivers and runtime (CUDA for NVIDIA, ROCm for AMD)
- Check model file isn't corrupted: Re-download if needed

**GPU not being used (high CPU usage instead)**
- Check server startup logs for GPU detection messages
- NVIDIA: Should see "CUDA" and "offloading X layers to GPU"
- AMD: Should see "HIP" and "offloading X layers to GPU"  
- Verify GPU monitoring: `nvidia-smi` or `rocm-smi`

### "No comparable prices found"
- Web scraping may be rate-limited
- Try increasing `--scraping-delay` 
- Some sites may block automated requests

### Poor LLM Results
- Try a larger model or lower quantization (Q5_K_M, Q6_K)
- Adjust temperature settings in the code
- Check if your model is appropriate for JSON parsing

### Memory Issues
- Use smaller models: `llama3.2:3b` instead of `llama3.1:8b`
- Close other applications
- For transformers backend, ensure you have enough RAM/VRAM

## Performance Optimization

### Model Selection

**llama.cpp (GGUF models):**
- **Fast + Small (3-4GB VRAM)**: Llama 3.2 3B Q4_K_M
- **Balanced (5-6GB VRAM)**: Llama 3.1 8B Q4_K_M
- **Best Quality (8-10GB VRAM)**: Llama 3.1 8B Q6_K
- **Maximum Quality (12GB+ VRAM)**: Llama 3.1 8B Q8_0

### AMD GPU Optimization (llama.cpp)

```powershell
# Check your GPU VRAM
rocm-smi

# Adjust layers based on VRAM:
# 8GB VRAM: -ngl 32
# 12GB VRAM: -ngl 40
# 16GB+ VRAM: -ngl 50 or higher

# For RX 6800 XT (16GB) - Maximum performance:
.\server.exe -m model.gguf -ngl 50 -c 4096 --n-gpu-layers 50

# For RX 6600 XT (8GB) - Balanced:
.\server.exe -m model.gguf -ngl 28 -c 2048 --n-gpu-layers 28

# Monitor performance:
rocm-smi -d 0 --showuse
```

### NVIDIA GPU Optimization (llama.cpp)

```powershell
# Check your GPU VRAM
nvidia-smi

# Adjust layers based on VRAM:
# 8GB VRAM (RTX 3060): -ngl 35
# 10GB VRAM (RTX 3080): -ngl 40
# 12GB VRAM (RTX 3060 Ti/4070): -ngl 45
# 16GB+ VRAM (RTX 4080/4090): -ngl 55

# For RTX 4090 (24GB) - Maximum performance:
.\server.exe -m model.gguf -ngl 60 -c 8192

# For RTX 3080 (10GB) - Balanced:
.\server.exe -m model.gguf -ngl 40 -c 4096

# Monitor performance:
nvidia-smi -l 1  # Updates every second
```

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

| Method | Cost per 100 items | Setup | Speed | NVIDIA GPU | AMD GPU |
|--------|-------------------|--------|--------|------------|---------|
| Claude API | $0.50-2.00 | Easy | Fast | N/A | N/A |
| llama.cpp | $0.00 | Medium | Very Fast | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Transformers | $0.00 | Hard | Slow | ⭐⭐⭐ | ⭐⭐ |

## Quick Reference Commands

```powershell
# Start llama.cpp server (GPU accelerated)
cd llama.cpp\build\bin\Release
.\server.exe -m ..\..\models\llama-3.1-8b-q4.gguf -ngl 40 --port 8080

# Check GPU status
nvidia-smi      # For NVIDIA GPUs
rocm-smi        # For AMD GPUs

# Run claim processing with llama.cpp
$env:INFERENCE_BACKEND="llamacpp"
python -m claim_assist.main example_claims.csv
```

## Next Steps

Once your local setup is working:

1. Process your own claim files
2. Adjust thresholds and settings for your use case  
3. Customize web scraping sources
4. Train or fine-tune models on your data