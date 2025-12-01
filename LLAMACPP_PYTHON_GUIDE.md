# What You Built: llama-cpp-python Integration

Great choice! You're using `llama-cpp-python` which is **the simplest way** to run local LLM inference with GPU acceleration.

## What You Did

You installed llama-cpp-python with CUDA 12.4 support:
```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
```

This is a **pre-built wheel** with CUDA support, meaning:
- ✅ No C++ compilation needed
- ✅ No CMake, Visual Studio, or build tools required
- ✅ Works immediately with NVIDIA GPUs
- ✅ Much simpler than building llama.cpp from source

## How to Use It

### Option 1: In Google Colab (What You're Doing)

Perfect for testing and small batches! See [COLAB_QUICKSTART.md](COLAB_QUICKSTART.md) for complete guide.

```python
# 1. Install (already done!)
!pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

# 2. Download model
from huggingface_hub import hf_hub_download
model_path = hf_hub_download(
    repo_id="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
    filename="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
)

# 3. Configure claim-assist to use it
import os
os.environ['INFERENCE_BACKEND'] = 'llamacpp_python'
os.environ['MODEL_PATH'] = model_path
os.environ['N_GPU_LAYERS'] = '50'  # Use GPU

# 4. Process claims!
!python -m claim_assist.main your_claims.csv
```

### Option 2: Local Windows Machine

If you want to run this on your local machine:

```powershell
# 1. Install llama-cpp-python
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

# 2. Download a model (one-time)
pip install huggingface-hub
python -c "from huggingface_hub import hf_hub_download; print(hf_hub_download('bartowski/Meta-Llama-3.1-8B-Instruct-GGUF', 'Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf'))"

# 3. Note the path where model was downloaded (it will print it)

# 4. Install claim-assist
git clone https://github.com/CamdenBibro/claim-assist.git
cd claim-assist
pip install -r requirements-minimal.txt

# 5. Configure environment
$env:INFERENCE_BACKEND="llamacpp_python"
$env:MODEL_PATH="C:\Users\YourName\.cache\huggingface\hub\...\model.gguf"  # Use actual path
$env:N_GPU_LAYERS="50"

# 6. Process claims
python -m claim_assist.main example_claims.csv
```

## What's Different from llama.cpp Server?

| Feature | llama-cpp-python (What You're Using) | llama.cpp C++ Server |
|---------|-------------------------------------|----------------------|
| **Installation** | `pip install` (1 command) | Build from source (30+ min) |
| **Setup** | Import in Python | Run separate server process |
| **GPU Support** | ✅ Automatic (CUDA/ROCm) | ✅ Requires build flags |
| **Use Case** | Scripts, notebooks, single user | Production, multiple users |
| **Performance** | ⭐⭐⭐⭐ Very Good | ⭐⭐⭐⭐⭐ Excellent |
| **Complexity** | ⭐⭐⭐⭐⭐ Simple | ⭐⭐⭐ Complex |

**Bottom line:** llama-cpp-python is perfect for your use case! You get 90% of the performance with 10% of the complexity.

## Configuration Options

All configured via environment variables:

```python
import os

# Required
os.environ['INFERENCE_BACKEND'] = 'llamacpp_python'
os.environ['MODEL_PATH'] = '/path/to/model.gguf'

# Optional (with defaults)
os.environ['N_GPU_LAYERS'] = '50'  # Number of layers on GPU (-1 = all)
os.environ['N_CTX'] = '4096'       # Context window size
```

Or via command line:
```bash
python -m claim_assist.main claims.csv \
  --inference-backend llamacpp_python \
  --model-path /path/to/model.gguf \
  --n-gpu-layers 50
```

## GPU Detection

llama-cpp-python automatically detects your GPU:

- **NVIDIA GPU**: Uses CUDA (you installed `cu124` wheel)
- **AMD GPU**: Requires building from source with ROCm
- **No GPU**: Falls back to CPU (slow but works)

Check if GPU is working:
```python
from llama_cpp import Llama

llm = Llama(
    model_path="path/to/model.gguf",
    n_gpu_layers=50,
    verbose=True  # Will show GPU info
)

# Look for output like:
# "CUDA: 1 device(s) detected"
# "offloading 50 layers to GPU"
```

## Troubleshooting

### "ImportError: DLL load failed" (Windows)

Install Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

### "CUDA out of memory"

Reduce GPU layers:
```python
os.environ['N_GPU_LAYERS'] = '30'  # Instead of 50
```

### "Model loading is slow"

First load takes time (loading weights). Subsequent inference is fast.

### "No GPU detected"

Check CUDA installation:
```python
import subprocess
subprocess.run(["nvidia-smi"])
```

## Advanced: Building from Source (AMD GPUs)

If you have an AMD GPU, the pre-built wheel won't work. Build from source:

```powershell
# Install ROCm from AMD
# Then build with HIP support:
$env:CMAKE_ARGS="-DLLAMA_HIPBLAS=on -DAMDGPU_TARGETS=gfx1030"
pip install llama-cpp-python --no-binary llama-cpp-python
```

Replace `gfx1030` with your GPU architecture. Find it with:
```bash
rocminfo | grep "Name:"
```

## Performance Expectations

With RTX 3090 and Llama 3.1 8B Q4_K_M:

- **Tokens/sec**: 60-80
- **100 claims**: ~15-20 minutes
- **Memory usage**: ~6-8 GB VRAM

With T4 GPU (Google Colab):

- **Tokens/sec**: 30-40
- **100 claims**: ~25-30 minutes
- **Memory usage**: ~5-7 GB VRAM

## Next Steps

1. **Test it:** Run with `example_claims.csv` first
2. **Tune GPU layers:** Adjust `N_GPU_LAYERS` for your GPU memory
3. **Try different models:** Experiment with Q5_K_M (better quality) or Q3_K_M (faster)
4. **Scale up:** Process your real claims data

## Comparison to Other Methods

✅ **Better than:**
- Cloud APIs (cost, privacy)
- CPU inference (speed)
- llama.cpp server (simplicity)

⚠️ **Not as good as:**
- llama.cpp server (absolute max performance)
- Cloud GPUs (no hardware investment)

🎯 **Perfect for:**
- Development and testing
- Personal/small team use
- Learning and experimentation
- Jupyter notebooks
- Single-user applications

## Resources

- **Quick Start:** [COLAB_QUICKSTART.md](COLAB_QUICKSTART.md)
- **Cloud Options:** [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md)
- **Method Comparison:** [SETUP_COMPARISON.md](SETUP_COMPARISON.md)
- **llama-cpp-python Docs:** https://github.com/abetlen/llama-cpp-python
- **Model Downloads:** https://huggingface.co/bartowski

## Summary

You chose the **easiest and most practical** method for local GPU inference:

```
pip install llama-cpp-python  # ← One command!
↓
Download model               # ← One Python call
↓
Set environment variables    # ← Three lines
↓
python -m claim_assist.main  # ← Process claims!
```

**No build tools. No servers. Just Python.** 🎉

Perfect for Google Colab, Jupyter notebooks, or local development!
