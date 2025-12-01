# llama.cpp Setup for GPU Acceleration - Quick Start

This is a streamlined guide for setting up llama.cpp with GPU acceleration on Windows.

## Prerequisites

- **GPU Options**:
  - **NVIDIA GPU**: GTX 1000 series or newer (RTX 2000/3000/4000 series recommended)
  - **AMD GPU**: RX 6000 series or RX 7000 series (RDNA 2/3 architecture)
- **VRAM**: Minimum 8GB recommended, 12GB+ ideal
- **Windows 10/11**: 64-bit
- **CMake**: Download from https://cmake.org/download/
- **Git**: Download from https://git-scm.com/download/win

## Step 1: Install GPU Runtime

Choose based on your GPU:

### Option A: NVIDIA GPU (CUDA)

```powershell
# Download and install CUDA Toolkit from NVIDIA
# https://developer.nvidia.com/cuda-downloads
# Recommended: CUDA 12.x or 11.8

# After installation, verify:
nvcc --version

# Should show CUDA version, e.g.: "Cuda compilation tools, release 12.3"

# Also verify GPU is detected:
nvidia-smi

# Should show your GPU details (name, memory, driver version)
```

**If CUDA installation fails:**
- Ensure your NVIDIA drivers are up to date (Download from nvidia.com/drivers)
- CUDA Toolkit includes necessary drivers, but updating separately can help
- Restart after installation
- Supported GPUs: GTX 1000 series and newer

**CUDA Compute Capability:**
- GTX 1000 series: 6.1
- RTX 2000 series: 7.5
- RTX 3000 series: 8.6
- RTX 4000 series: 8.9

### Option B: AMD GPU (ROCm)

```powershell
# Download ROCm installer from AMD
# https://www.amd.com/en/graphics/servers-solutions-rocm

# After installation, verify:
rocminfo

# You should see your GPU listed
# Example output: "Name: gfx1030" (RX 6000 series) or "gfx1100" (RX 7000 series)
```

**If ROCm installation fails:**
- Ensure your AMD drivers are up to date
- AMD Radeon Software Adrenalin Edition must be installed first
- Some older GPUs may not support ROCm (check AMD's compatibility list)

## Step 2: Build llama.cpp with GPU Support

Choose based on your GPU:

### Option A: NVIDIA GPU (CUDA Build)

```powershell
# Clone the repository
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Create build directory
mkdir build
cd build

# Configure CMake with CUDA support
cmake .. -G "Visual Studio 17 2022" -A x64 `
  -DLLAMA_CUDA=ON

# Optional: Specify CUDA architectures for your GPU
# Uncomment and modify if you want to optimize for specific GPU:
# cmake .. -G "Visual Studio 17 2022" -A x64 `
#   -DLLAMA_CUDA=ON `
#   -DCMAKE_CUDA_ARCHITECTURES="86"  # For RTX 3000 series
# Common values: "75" (RTX 2000), "86" (RTX 3000), "89" (RTX 4000)

# Build (this will take 5-10 minutes)
cmake --build . --config Release

# Verify the server was built
ls bin\Release\server.exe
```

**NVIDIA Build Troubleshooting:**
- If CUDA not found: Ensure CUDA Toolkit is installed and in PATH
- If build fails: Update NVIDIA drivers to latest version
- If "unsupported compiler": Use Visual Studio 2019 or 2022
- Check CUDA is in PATH: `$env:PATH` should include CUDA bin directory

### Option B: AMD GPU (ROCm Build)

```powershell
# Clone the repository
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Create build directory
mkdir build
cd build

# Identify your GPU architecture
rocminfo | findstr "Name:"
# Look for gfx#### in the output

# Configure CMake with ROCm support
# Replace gfx1030 with your GPU architecture:
# - RX 6600/6700/6800/6900 series: gfx1030
# - RX 7600/7700/7800/7900 series: gfx1100

cmake .. -G "Visual Studio 17 2022" -A x64 `
  -DLLAMA_HIPBLAS=ON `
  -DCMAKE_C_COMPILER=clang `
  -DCMAKE_CXX_COMPILER=clang++ `
  -DAMDGPU_TARGETS=gfx1030

# Build (this will take 5-10 minutes)
cmake --build . --config Release

# Verify the server was built
ls bin\Release\server.exe
```

**AMD Build Troubleshooting:**
- If clang not found: Install LLVM from https://releases.llvm.org/
- If CMake fails: Try using Ninja instead: `cmake .. -G Ninja -DLLAMA_HIPBLAS=ON`
- If HIP not found: Ensure ROCm bin directory is in PATH

## Step 3: Download a GGUF Model

```powershell
# Create models directory
cd ..\..
mkdir models
cd models

# Download Llama 3.1 8B (4-bit quantized, ~4.5GB)
# This is a good balance of quality and speed
curl -L -o llama-3.1-8b-instruct-q4_k_m.gguf `
  "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

# Alternative: Smaller/faster model (2GB)
curl -L -o llama-3.2-3b-instruct-q4_k_m.gguf `
  "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
```

**Where to find more models:**
- https://huggingface.co/bartowski (curated GGUF quantizations)
- https://huggingface.co/TheBloke (large collection, mostly older)
- Search for "GGUF" on Hugging Face

**Quantization levels explained:**
- Q2_K: Smallest, fastest, lowest quality (2-3GB)
- Q4_K_M: **Recommended** - good balance (4-5GB)
- Q5_K_M: Higher quality, slower (5-6GB)
- Q6_K: Near-original quality (7-8GB)
- Q8_0: Highest quality, slowest (9-10GB)

## Step 4: Start the Server with GPU Acceleration

```powershell
# Navigate to the server binary
cd ..\build\bin\Release

# Start the server with GPU offloading
# Adjust -ngl (number of GPU layers) based on your VRAM:

# For 8GB VRAM (RX 6600 XT):
.\server.exe -m ..\..\..\models\llama-3.1-8b-instruct-q4_k_m.gguf `
  -ngl 32 `
  --port 8080 `
  --host 0.0.0.0 `
  -c 2048

# For 12GB VRAM (RX 6700 XT):
.\server.exe -m ..\..\..\models\llama-3.1-8b-instruct-q4_k_m.gguf `
  -ngl 40 `
  --port 8080 `
  --host 0.0.0.0 `
  -c 4096

# For 16GB+ VRAM (RX 6800 XT, 6900 XT, 7900 XT/XTX):
.\server.exe -m ..\..\..\models\llama-3.1-8b-instruct-q4_k_m.gguf `
  -ngl 50 `
  --port 8080 `
  --host 0.0.0.0 `
  -c 4096

# Server will start on http://localhost:8080
# You should see: "HTTP server listening on http://0.0.0.0:8080"
```

**Parameters explained:**
- `-m`: Path to model file
- `-ngl`: Number of layers to offload to GPU (higher = more GPU usage)
- `--port`: Port to run server on
- `-c`: Context size (higher = can process longer text, but slower)
- `--host`: Allow connections from any IP (use 127.0.0.1 for localhost only)

## Step 5: Test the Server

```powershell
# In a new PowerShell window, test the API:
Invoke-RestMethod -Uri "http://localhost:8080/v1/models" -Method Get | ConvertTo-Json
```

Expected output:
```json
{
  "object": "list",
  "data": [
    {
      "id": "llama-3.1-8b-instruct",
      ...
    }
  ]
}
```

## Step 6: Configure Claim Assist

```powershell
# Navigate to your claim-assist directory
cd C:\Users\Ke\Documents\GitHub\claim-assist

# Set environment variables for llama.cpp
$env:INFERENCE_BACKEND="llamacpp"
$env:MODEL_NAME="llama-3.1-8b-instruct"
$env:INFERENCE_BASE_URL="http://localhost:8080/v1"

# Run a test
python -m claim_assist.main example_claims.csv
```

## Performance Tuning

### Finding the Right -ngl Value

Start with a conservative value and increase:

```powershell
# Monitor GPU usage in another terminal
rocm-smi -d 0 --showuse

# Start low
.\server.exe -m model.gguf -ngl 20 --port 8080

# If VRAM usage is under 80%, increase -ngl by 5-10
# Stop increasing when you see "out of memory" or performance degrades
```

### Batch Size and Threads

For better throughput processing multiple claims:

```powershell
.\server.exe -m model.gguf `
  -ngl 40 `
  -c 4096 `
  -b 512 `            # Batch size (higher = faster for multiple requests)
  -t 8 `              # CPU threads for non-GPU work
  --parallel 4        # Process 4 requests simultaneously
```

### Temperature and Sampling

For claim processing, you want deterministic output:

```powershell
# These settings are controlled by the Python client
# But you can set server defaults:
.\server.exe -m model.gguf -ngl 40 `
  --temp 0.1 `        # Low temperature = more consistent
  --top-k 40 `        # Limit sampling to top 40 tokens
  --top-p 0.95        # Nucleus sampling threshold
```

## Monitoring and Debugging

### Check GPU Utilization

**For NVIDIA GPUs:**
```powershell
# Real-time GPU monitoring
nvidia-smi

# Or watch continuously (updates every 1 second):
nvidia-smi -l 1

# Watch for:
# - GPU usage should be 90-100% during inference
# - VRAM usage should be stable (not hitting limit)
# - Temperature should stay under 85°C
```

**For AMD GPUs:**
```powershell
# Real-time GPU monitoring
rocm-smi -d 0 --showuse --showmemuse

# Watch for:
# - GPU usage should be 90-100% during inference
# - VRAM usage should be stable (not hitting limit)
# - Temperature should stay under 80°C
```

### Common Issues

**Server starts but uses CPU instead of GPU:**

*For NVIDIA:*
```powershell
# Check the server output for:
"ggml_init_cublas: found X CUDA devices"  # Should see your GPU
"llm_load_tensors: offloading X layers to GPU"  # Should match -ngl value

# Verify CUDA build:
.\server.exe --version  # Should mention CUDA

# If not working, rebuild:
cmake .. -DLLAMA_CUDA=ON -DCMAKE_VERBOSE_MAKEFILE=ON
```

*For AMD:*
```powershell
# Check the server output for:
"ggml_init_hip: found X HIP devices"  # Should see your GPU
"llm_load_tensors: offloading X layers to GPU"  # Should match -ngl value

# If not, rebuild with verbose output:
cmake .. -DLLAMA_HIPBLAS=ON -DCMAKE_VERBOSE_MAKEFILE=ON
```

**"Out of memory" errors:**
- Reduce `-ngl` by 5-10
- Use a more quantized model (Q3_K_M or Q2_K)
- Reduce context size `-c 2048`
- Close other GPU-intensive applications

**Slow inference (< 10 tokens/second):**
- Increase `-ngl` to offload more to GPU
- Check GPU is actually being used: `nvidia-smi` (NVIDIA) or `rocm-smi` (AMD)
- Ensure no thermal throttling: check GPU temperature
- Try a smaller model or higher quantization

## Performance Expectations

### llama.cpp + GPU Performance

**NVIDIA GPUs:**
- RTX 4090 (24GB): ~80-100 tok/s with Llama 3.1 8B (Q4_K_M)
- RTX 4080 (16GB): ~65-80 tok/s with Llama 3.1 8B (Q4_K_M)
- RTX 4070 Ti (12GB): ~50-65 tok/s with Llama 3.1 8B (Q4_K_M)
- RTX 3090 (24GB): ~60-75 tok/s with Llama 3.1 8B (Q4_K_M)
- RTX 3080 (10GB): ~50-60 tok/s with Llama 3.1 8B (Q4_K_M)

**AMD GPUs:**
- RX 7900 XTX (24GB): ~50-60 tok/s with Llama 3.1 8B (Q4_K_M)
- RX 6800 XT (16GB): ~40-50 tok/s with Llama 3.1 8B (Q4_K_M)
- RX 6700 XT (12GB): ~35-45 tok/s with Llama 3.1 8B (Q4_K_M)

*Note: NVIDIA GPUs typically perform better due to more mature CUDA support.*

## Creating a Start Script

Save this as `start_llamacpp.ps1`:

```powershell
# start_llamacpp.ps1
$LLAMACPP_PATH = "C:\path\to\llama.cpp\build\bin\Release"
$MODEL_PATH = "C:\path\to\llama.cpp\models\llama-3.1-8b-instruct-q4_k_m.gguf"

cd $LLAMACPP_PATH

Write-Host "Starting llama.cpp server with AMD GPU acceleration..."
Write-Host "Model: $MODEL_PATH"
Write-Host "Server will be available at http://localhost:8080"

.\server.exe -m $MODEL_PATH `
  -ngl 40 `
  --port 8080 `
  --host 0.0.0.0 `
  -c 4096 `
  -b 512 `
  --parallel 2

# Run with: powershell -ExecutionPolicy Bypass -File start_llamacpp.ps1
```

## Next Steps

1. **Test with small claims file first**: Verify everything works
2. **Monitor GPU usage**: Adjust `-ngl` for optimal performance
3. **Try different models**: Q4_K_M is great, but Q5_K_M may be worth it
4. **Benchmark**: Test speeds on your hardware with different settings
5. **Automate**: Create startup scripts and Windows services if needed

## Additional Resources

- llama.cpp GitHub: https://github.com/ggerganov/llama.cpp
- GGUF Model Hub: https://huggingface.co/models?search=gguf
- **NVIDIA Users:**
  - CUDA Toolkit: https://developer.nvidia.com/cuda-downloads
  - CUDA Documentation: https://docs.nvidia.com/cuda/
- **AMD Users:**
  - ROCm Documentation: https://rocm.docs.amd.com/
  - AMD GPU Compatibility: https://github.com/ggerganov/llama.cpp#hip-amd-gpu

## Getting Help

If you encounter issues:
1. Check llama.cpp GitHub Issues: https://github.com/ggerganov/llama.cpp/issues
2. **Verify GPU installation:**
   - NVIDIA: `nvidia-smi` and `nvcc --version`
   - AMD: `rocminfo`
3. Check server logs for error messages
4. Try CPU-only mode first: Remove `-ngl` parameter
5. Test with a smaller model: llama-3.2-3b

## GPU Selection Summary

| Feature | NVIDIA (CUDA) | AMD (ROCm) |
|---------|---------------|------------|
| **Performance** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐ Very Good |
| **Setup Difficulty** | ⭐⭐⭐⭐⭐ Easy | ⭐⭐⭐ Moderate |
| **Compatibility** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Good |
| **Driver Support** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐ Good |
| **Documentation** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Good |

**Recommendation:**
- **Best performance**: NVIDIA RTX 4000 series
- **Best value**: NVIDIA RTX 3060/3070 (12GB VRAM)
- **AMD option**: RX 6800 XT or RX 7900 XTX (requires more setup but works well)
