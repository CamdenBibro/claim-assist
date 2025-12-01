# Setup Methods Comparison

This document compares the different ways to run Claim Assist with local LLM inference.

## 🎯 Quick Decision Guide

**Just want to test it?** → Use [Google Colab (Free)](COLAB_QUICKSTART.md)

**Need it for production?** → Use [Cloud GPU Servers](CLOUD_DEPLOYMENT.md) (RunPod, AWS)

**Want to run locally?** → Use `llama-cpp-python` (easiest) or `llama.cpp server` (more control)

---

## Method Comparison

### Method 1: Google Colab ⭐ RECOMMENDED FOR BEGINNERS

**What it is:** Free cloud notebook with GPU access

**Pros:**
- ✅ Completely free (with limits)
- ✅ Zero local installation
- ✅ Works from any computer
- ✅ Pre-configured GPU environment
- ✅ 5-minute setup

**Cons:**
- ❌ Session limits (12 hours max)
- ❌ Disconnects after 90 min idle
- ❌ Not suitable for production
- ❌ GPU not always available

**Best for:** Testing, small batches, learning

**Setup time:** 5 minutes

**Cost:** FREE (or $10-50/mo for Pro)

**Guide:** [COLAB_QUICKSTART.md](COLAB_QUICKSTART.md)

---

### Method 2: llama-cpp-python (Python Library) ⭐ BEST FOR SIMPLICITY

**What it is:** Python library with GPU acceleration, runs in your Python environment

**Pros:**
- ✅ No separate server needed
- ✅ No C++ compilation required
- ✅ Simple Python installation: `pip install llama-cpp-python`
- ✅ Direct GPU acceleration (CUDA/ROCm)
- ✅ Works in Jupyter, Colab, or scripts
- ✅ Easy to integrate

**Cons:**
- ❌ Less control over server settings
- ❌ Loads model into Python process (more memory)
- ❌ Slightly slower than C++ server

**Best for:** Quick local setup, Python developers, notebooks

**Setup time:** 10 minutes

**Installation:**
```powershell
# NVIDIA GPU (CUDA)
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

# AMD GPU (ROCm) - requires building from source
CMAKE_ARGS="-DLLAMA_HIPBLAS=on" pip install llama-cpp-python

# CPU only
pip install llama-cpp-python
```

**Configuration:**
```powershell
$env:INFERENCE_BACKEND="llamacpp_python"
$env:MODEL_PATH="path/to/model.gguf"
$env:N_GPU_LAYERS="50"
python -m claim_assist.main claims.csv
```

**Guide:** See [README Quick Start](#option-2-local-inference-with-llama-cpp-python-simple-python-library)

---

### Method 3: llama.cpp Server (C++) ⭐ BEST FOR PERFORMANCE

**What it is:** Standalone C++ server with OpenAI-compatible API

**Pros:**
- ✅ Best performance (pure C++)
- ✅ More server configuration options
- ✅ Can serve multiple clients
- ✅ Lower memory usage
- ✅ Optimized GPU code paths
- ✅ Better for production

**Cons:**
- ❌ Requires C++ compilation (CMake, build tools)
- ❌ Separate server process to manage
- ❌ More complex setup
- ❌ Longer installation time

**Best for:** Production use, maximum performance, serving multiple apps

**Setup time:** 30-60 minutes (first time)

**Installation:**
```bash
# Clone and build
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build && cd build

# NVIDIA GPU
cmake .. -DLLAMA_CUDA=ON

# AMD GPU
cmake .. -DLLAMA_HIPBLAS=ON -DAMDGPU_TARGETS=gfx1030

cmake --build . --config Release
```

**Usage:**
```bash
# Start server
./build/bin/server -m model.gguf -ngl 50 --port 8080

# Configure app
export INFERENCE_BACKEND="llamacpp"
export INFERENCE_BASE_URL="http://localhost:8080/v1"
python -m claim_assist.main claims.csv
```

**Guides:**
- [LLAMACPP_AMD_SETUP.md](LLAMACPP_AMD_SETUP.md) - Detailed GPU setup
- [LOCAL_SETUP.md](LOCAL_SETUP.md) - Full local guide

---

### Method 4: Cloud GPU Servers ⭐ BEST FOR PRODUCTION

**What it is:** Rent GPU servers by the hour (RunPod, AWS, Vast.ai, etc.)

**Pros:**
- ✅ Powerful GPUs on-demand
- ✅ Pay only when processing
- ✅ No local hardware needed
- ✅ Scales to any workload
- ✅ Enterprise reliability (AWS/Azure)

**Cons:**
- ❌ Costs money ($0.20-3/hour)
- ❌ Requires cloud account setup
- ❌ Internet connection needed
- ❌ Data leaves your machine

**Best for:** Production workloads, large batches, no local GPU

**Setup time:** 15-30 minutes

**Cost:**
- Vast.ai: ~$0.20/hour (RTX 3090)
- RunPod: ~$0.34/hour (RTX 3090)
- AWS EC2: ~$0.53/hour (T4 GPU)

**Guide:** [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md)

---

## Feature Comparison Matrix

| Feature | Colab | llama-cpp-python | llama.cpp Server | Cloud GPU |
|---------|-------|------------------|------------------|-----------|
| **Setup Difficulty** | ⭐⭐⭐⭐⭐ Easiest | ⭐⭐⭐⭐ Easy | ⭐⭐⭐ Moderate | ⭐⭐⭐ Moderate |
| **Performance** | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Very Good | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐⭐ Excellent |
| **Cost** | FREE | $0 (hardware) | $0 (hardware) | $0.20-3/hr |
| **GPU Support** | ✅ CUDA only | ✅ CUDA + ROCm | ✅ CUDA + ROCm | ✅ CUDA + ROCm |
| **Production Ready** | ❌ No | ⚠️ Maybe | ✅ Yes | ✅ Yes |
| **Requires Internet** | ✅ Yes | ❌ No | ❌ No | ✅ Yes |
| **Multi-user** | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| **Memory Efficient** | ⚠️ OK | ⚠️ OK | ✅ Yes | ✅ Yes |
| **Easy Updates** | ✅ Yes | ✅ Yes | ⚠️ Rebuild | ✅ Yes |

---

## Performance Comparison

Processing **100 insurance claims** with Llama 3.1 8B (Q4_K_M):

| Method | GPU | Time | Tokens/sec | Cost |
|--------|-----|------|------------|------|
| **Colab (Free)** | T4 | 20-30 min | 30-40 | FREE |
| **llama-cpp-python (Local)** | RTX 3090 | 12-15 min | 60-70 | $0 |
| **llama.cpp Server (Local)** | RTX 3090 | 10-12 min | 80-100 | $0 |
| **RunPod** | RTX 3090 | 10-12 min | 80-100 | ~$0.06 |
| **AWS EC2** | T4 | 20-25 min | 35-45 | ~$0.20 |
| **CPU Only** | Any | 2-3 hours | 2-5 | $0 |

---

## Decision Tree

```
Do you have a GPU locally?
│
├─ NO → Use Google Colab (free) or Cloud GPU (paid)
│
└─ YES
   │
   ├─ Just testing? → Use llama-cpp-python (easiest)
   │
   ├─ Running occasionally? → Use llama-cpp-python (easy)
   │
   └─ Production / High volume?
      │
      ├─ Single user? → llama-cpp-python is fine
      │
      └─ Multiple users? → Build llama.cpp server
```

---

## Installation Commands Quick Reference

### Google Colab
```python
# See COLAB_QUICKSTART.md - just copy paste cells!
```

### llama-cpp-python (Local)
```powershell
# NVIDIA GPU
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

# AMD GPU (build from source)
$env:CMAKE_ARGS="-DLLAMA_HIPBLAS=on"
pip install llama-cpp-python --no-binary llama-cpp-python

# Configure
$env:INFERENCE_BACKEND="llamacpp_python"
$env:MODEL_PATH="path/to/model.gguf"
$env:N_GPU_LAYERS="50"
```

### llama.cpp Server (Local)
```powershell
# Clone
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build (NVIDIA)
mkdir build; cd build
cmake .. -DLLAMA_CUDA=ON
cmake --build . --config Release

# Build (AMD)
mkdir build; cd build
cmake .. -DLLAMA_HIPBLAS=ON -DAMDGPU_TARGETS=gfx1030
cmake --build . --config Release

# Run server
.\build\bin\server.exe -m model.gguf -ngl 50 --port 8080

# Configure app
$env:INFERENCE_BACKEND="llamacpp"
$env:INFERENCE_BASE_URL="http://localhost:8080/v1"
```

### Cloud GPU (RunPod)
```bash
# See CLOUD_DEPLOYMENT.md for full guide
# Quick: Use the automated setup script
bash cloud_setup.sh
```

---

## Recommended Path for New Users

1. **Start with Google Colab** ([COLAB_QUICKSTART.md](COLAB_QUICKSTART.md))
   - Test with small batch (10-20 claims)
   - Verify output quality
   - No setup required

2. **If you liked it and have a GPU:**
   - Install `llama-cpp-python` locally
   - Much faster than Colab
   - Process larger batches

3. **If running in production:**
   - Build `llama.cpp` C++ server for best performance
   - Or use cloud GPU servers (RunPod/AWS)
   - Set up proper monitoring

---

## Troubleshooting by Method

### Colab Issues
- "GPU not available" → Try again later or upgrade to Colab Pro
- "Session disconnected" → Re-run all cells
- "Out of memory" → Reduce `N_GPU_LAYERS`

### llama-cpp-python Issues
- "Import llama_cpp failed" → Reinstall with correct CUDA/ROCm version
- "Model not loading" → Check `MODEL_PATH` is correct
- "Slow inference" → Increase `N_GPU_LAYERS`, check GPU detected

### llama.cpp Server Issues
- "Build failed" → Install CMake, CUDA/ROCm, C++ compiler
- "Server won't start" → Check port 8080 not in use
- "GPU not detected" → Verify CUDA/ROCm installation

### Cloud GPU Issues
- "Connection refused" → Check server started, firewall rules
- "High costs" → Stop instances when not in use!
- "Slow upload" → Use SCP instead of web interface

---

## Summary

| Use Case | Best Method |
|----------|-------------|
| **Testing** | Google Colab |
| **Quick local run** | llama-cpp-python |
| **Production single-user** | llama-cpp-python or llama.cpp |
| **Production multi-user** | llama.cpp server |
| **No local GPU** | Google Colab or Cloud GPU |
| **Large batches (>1000)** | Cloud GPU or local llama.cpp |
| **Cost-sensitive** | Google Colab (free) or local setup |
| **Maximum performance** | llama.cpp server with high-end GPU |

---

**Next Steps:**
1. Choose your method based on use case
2. Follow the corresponding guide
3. Start with example_claims.csv to test
4. Scale up to your real data

**Need help deciding?** Open an issue with your:
- Use case (testing / production)
- Hardware (GPU / no GPU)
- Batch size (claims per run)
- Budget constraints
