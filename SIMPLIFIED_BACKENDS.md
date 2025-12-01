# Simplified to Two Backends

## ✅ Changes Made

Removed all legacy backend support to keep only the two essential modes:

### **Supported Backends:**
1. ✅ **llamacpp_python** - Local inference with Python library (Default)
2. ✅ **anthropic** - Cloud API

### **Removed Backends:**
- ❌ llamacpp (server mode) - Removed, use llamacpp_python instead
- ❌ openai_compatible - Removed
- ❌ transformers - Removed

---

## 📝 Files Updated

### 1. **claim_assist/config.py**
- Default backend: `llamacpp_python`
- Valid backends: Only `["llamacpp_python", "anthropic"]`
- Removed: `inference_base_url`, `inference_api_key` (only used by removed backends)
- Simplified validation logic

### 2. **claim_assist/main.py**
- CLI argument `--inference-backend` now only accepts: `llamacpp_python`, `anthropic`
- Removed `--inference-url` argument
- Simplified `--api-key` to only work with Anthropic
- Updated help text and error messages

### 3. **claim_assist/utils/api_clients.py**
- Simplified `create_inference_client()` function
- Only handles two cases: llamacpp_python or anthropic
- Removed unnecessary kwargs and conditionals

### 4. **check_setup.py**
- Renamed function from `check_local_llamacpp()` to reflect llamacpp_python focus
- Removed llamacpp server connectivity tests
- Updated recommendations to only show two modes

### 5. **debug_single_item.py**
- Updated docstring and help text
- Removed llamacpp server references

### 6. **README.md**
- Simplified to show only two options
- Removed "Option 3: llama.cpp Server" section
- Updated feature list
- Cleaner Quick Start section

---

## 🎯 Current Architecture

```
User Configuration
       ↓
   Config.from_env()
       ├─ INFERENCE_BACKEND = llamacpp_python (default)
       │  ├─ MODEL_PATH (required)
       │  ├─ N_GPU_LAYERS (optional, default: 50)
       │  └─ N_CTX (optional, default: 4096)
       │
       └─ INFERENCE_BACKEND = anthropic
          └─ ANTHROPIC_API_KEY (required)
       ↓
create_inference_client(config)
       ├─ llamacpp_python → LlamaCppPythonClient
       │   └─ Loads GGUF model from MODEL_PATH
       │   └─ Uses GPU with n_gpu_layers
       │
       └─ anthropic → AnthropicWrapper
           └─ Uses anthropic.Anthropic(api_key)
       ↓
ClaimProcessor
    ├─ ItemClassifier
    ├─ PriceResearcher
    │   └─ WebScrapingService
    └─ PriceValidator
```

---

## 🚀 Usage Examples

### Local Mode (llamacpp_python)
```powershell
# Windows PowerShell
$env:INFERENCE_BACKEND="llamacpp_python"
$env:MODEL_PATH="C:\models\llama-3.1-8b-instruct-q4.gguf"
$env:N_GPU_LAYERS="50"
python -m claim_assist.main example_claims.csv
```

```bash
# Linux/Mac
export INFERENCE_BACKEND="llamacpp_python"
export MODEL_PATH="/home/user/models/llama-3.1-8b-instruct-q4.gguf"
export N_GPU_LAYERS="50"
python -m claim_assist.main example_claims.csv
```

### Cloud Mode (anthropic)
```powershell
# Windows PowerShell
$env:INFERENCE_BACKEND="anthropic"
$env:ANTHROPIC_API_KEY="sk-ant-api03-..."
python -m claim_assist.main example_claims.csv
```

```bash
# Linux/Mac
export INFERENCE_BACKEND="anthropic"
export ANTHROPIC_API_KEY="sk-ant-api03-..."
python -m claim_assist.main example_claims.csv
```

---

## 🎓 Why Only Two Backends?

### **llamacpp_python** (Local)
- ✅ Simple to install (`pip install llama-cpp-python`)
- ✅ No server setup required
- ✅ GPU acceleration (CUDA/ROCm)
- ✅ Perfect for Colab, local development, single-user
- ✅ Free (just need model file)
- ✅ Offline capable

### **anthropic** (Cloud)
- ✅ No local setup needed
- ✅ Fastest inference (cloud infrastructure)
- ✅ Always up-to-date models
- ✅ No GPU required
- ✅ Perfect for production, multiple users
- ❌ Costs money (~$0.001-0.02 per item)
- ❌ Requires internet

### **Why Remove Others?**

**llamacpp (server mode):**
- Too complex (requires C++ build, server management)
- llamacpp_python does the same thing with less setup
- Server only useful for multi-user scenarios (not typical use case)

**openai_compatible:**
- Added complexity without clear benefit
- If users want OpenAI, they can modify the code
- Not insurance-focused

**transformers:**
- Slower than llamacpp_python
- More dependencies
- Less GPU optimization
- No clear advantage

---

## ✅ Benefits of Simplification

1. **Easier to understand** - Two clear choices
2. **Easier to maintain** - Less code, fewer edge cases
3. **Better documentation** - Can focus on what matters
4. **Faster onboarding** - New users aren't overwhelmed
5. **Clearer value proposition** - Free local vs Paid cloud

---

## 📋 Validation Checklist

- ✅ Config only allows llamacpp_python or anthropic
- ✅ Config validation checks backend-specific requirements
- ✅ CLI only shows two backend choices
- ✅ API client factory handles only two cases
- ✅ Documentation updated everywhere
- ✅ Error messages reference correct backends
- ✅ Debug scripts updated
- ✅ Check script updated
- ✅ README simplified

---

## 🧪 Testing

```powershell
# Test configuration checker
python check_setup.py

# Test with llamacpp_python (if you have a model)
$env:INFERENCE_BACKEND="llamacpp_python"
$env:MODEL_PATH="path/to/model.gguf"
python debug_single_item.py

# Test with Anthropic (if you have an API key)
$env:INFERENCE_BACKEND="anthropic"
$env:ANTHROPIC_API_KEY="your-key"
python debug_single_item.py
```

---

## 📚 Updated Documentation Files

Still relevant:
- ✅ COLAB_QUICKSTART.md - llamacpp_python setup
- ✅ CLOUD_DEPLOYMENT.md - Cloud options
- ✅ HIGH_LEVEL_ARCHITECTURE.md - System architecture
- ✅ README.md - Updated to show two options

Can be archived/removed:
- ⚠️ LLAMACPP_AMD_SETUP.md - Server mode instructions (no longer needed)
- ⚠️ SETUP_COMPARISON.md - Compared multiple backends (no longer relevant)
- ⚠️ LLAMACPP_PYTHON_GUIDE.md - Already covered in COLAB_QUICKSTART.md

---

## 🎉 Result

**Simpler, cleaner, easier to use!**

Users now have a clear choice:
- Want free local inference? → Use llamacpp_python
- Want fast cloud inference? → Use Anthropic

No confusion, no extra complexity, just what works.
