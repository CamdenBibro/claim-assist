# Google Colab Quick Start

Run Claim Assist in Google Colab with free GPU access! **No local setup required.**

## 🚀 One-Click Setup

Copy and paste these cells into a new Google Colab notebook:

### Step 1: Enable GPU

1. Go to **Runtime** → **Change runtime type**
2. Select **T4 GPU** (free tier)
3. Click **Save**

### Step 2: Install Dependencies

```python
# Cell 1: Install llama-cpp-python with CUDA support
!pip install -q llama-cpp-python \
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

!pip install -q huggingface-hub

# Optional: Install Selenium for Facebook Marketplace & Mercari scraping
# Note: This adds ~2 minutes to setup and makes processing 2x slower
!pip install -q selenium undetected-chromedriver
!apt-get update
!apt-get install -y chromium-chromedriver chromium-browser
```

### Step 3: Download Model

```python
# Cell 2: Download Llama 3.1 8B model
from huggingface_hub import hf_hub_download

print("Downloading model (this takes ~5 minutes)...")
model_path = hf_hub_download(
    repo_id="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
    filename="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
)
print(f"Model downloaded to: {model_path}")
```

### Step 4: Setup Claim Assist

```python
# Cell 3: Clone repository and install dependencies
!git clone https://github.com/CamdenBibro/claim-assist.git
%cd claim-assist
!pip install -q -r requirements-minimal.txt
print("Setup complete!")
```

### Step 5: Upload Your Claims File

```python
# Cell 4: Upload claims CSV
from google.colab import files

print("Click 'Choose Files' to upload your claims CSV...")
uploaded = files.upload()
claims_file = list(uploaded.keys())[0]
print(f"Uploaded: {claims_file}")
```

### Step 6: Process Claims (with Optional Selenium for More Price Sources)

**Option A: Fast Processing (eBay only)**
```python
# Cell 5A: Configure and run processing (fast, eBay only)
import os

# Configure to use llama-cpp-python (no server needed!)
os.environ['INFERENCE_BACKEND'] = 'llamacpp_python'
os.environ['MODEL_PATH'] = model_path
os.environ['N_GPU_LAYERS'] = '50'  # Use GPU acceleration

# Process the claims
!python -m claim_assist.main {claims_file}

print("\n✅ Processing complete!")
```

**Option B: Comprehensive Processing (eBay + Facebook + Mercari) - SLOWER**
```python
# Cell 5B: Configure and run with Selenium (slow but more sources)
import os

# Configure to use llama-cpp-python + Selenium
os.environ['INFERENCE_BACKEND'] = 'llamacpp_python'
os.environ['MODEL_PATH'] = model_path
os.environ['N_GPU_LAYERS'] = '50'
os.environ['ENABLE_SELENIUM'] = 'true'  # ← Enable Facebook/Mercari scraping

# Process the claims
!python -m claim_assist.main {claims_file}

print("\n✅ Processing complete!")
```

### Step 7: Download Results

```python
# Cell 6: Download results
from google.colab import files
import glob

# Find all result files
result_files = glob.glob("*_results.csv") + glob.glob("*_review.csv")

print(f"Found {len(result_files)} result files:")
for f in result_files:
    print(f"  - {f}")
    files.download(f)

print("\n✅ Download complete! Check your Downloads folder.")
```

---

## 📝 Example Input Format

Create a CSV file with this format:

```csv
description,brand,condition,age,features,estimated_value
"Samsung 55-inch 4K TV",Samsung,good,3 years,Smart TV QLED,800
"Vintage leather armchair",Unknown,fair,20 years,Genuine leather,300
"IKEA bookshelf",IKEA,excellent,1 year,Billy series,50
```

Required column: `description`

Optional columns: `brand`, `condition`, `age`, `features`, `estimated_value`

---

## ⚙️ Advanced Configuration

### Adjust GPU Usage

```python
# Use fewer GPU layers if you run out of memory
os.environ['N_GPU_LAYERS'] = '30'  # Default: 50

# Increase context window for longer descriptions
os.environ['N_CTX'] = '8192'  # Default: 4096
```

### Disable Caching

```python
os.environ['ENABLE_CACHE'] = 'false'
```

### Change Value Threshold

```python
# Only use deep research for items over $200
os.environ['VALUE_THRESHOLD'] = '200'
```

---

## 🔍 Monitor Processing

```python
# Cell: Watch processing in real-time
!python -m claim_assist.main {claims_file} --verbose
```

---

## 📊 Expected Performance

| GPU | Processing Speed | Cost |
|-----|------------------|------|
| **T4 (Free)** | ~30-40 tok/s | FREE |
| **A100 (Pro+)** | ~80-100 tok/s | $50/month |

**Processing time estimate:**
- 10 claims: ~2-3 minutes
- 50 claims: ~10-15 minutes
- 100 claims: ~20-30 minutes

---

## 💡 Tips

1. **Free Tier Limits:**
   - 12 hours max session time
   - Disconnects after 90 minutes of inactivity
   - GPU not always available during peak hours

2. **Save Your Work:**
   - Download results frequently
   - Session resets if disconnected
   - Model stays cached between runs in same session

3. **Batch Processing:**
   - Process multiple CSV files in one session
   - Combine files to minimize setup time

4. **Upgrade Options:**
   - **Colab Pro ($10/mo)**: Better GPUs, longer sessions
   - **Colab Pro+ ($50/mo)**: A100 GPUs, priority access

---

## 🐛 Troubleshooting

### "CUDA out of memory"

```python
# Reduce GPU layers
os.environ['N_GPU_LAYERS'] = '30'
```

### "Model download is slow"

```python
# Check download progress
!ls -lh /root/.cache/huggingface/hub/
```

### "Session disconnected"

- Click **Runtime** → **Reconnect**
- Re-run all cells from the beginning
- Model will re-download (~5 minutes)

### "Claims not processing"

```python
# Check if model is loaded
!ls -lh {model_path}

# Verify configuration
!python -c "from claim_assist.config import Config; c = Config.from_env(); print(f'Backend: {c.inference_backend}'); print(f'Model: {c.model_path}')"
```

---

## 📖 Full Documentation

- **Cloud Options:** [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md)
- **Local Setup:** [LOCAL_SETUP.md](LOCAL_SETUP.md)
- **GPU Setup:** [LLAMACPP_AMD_SETUP.md](LLAMACPP_AMD_SETUP.md)

---

## 🆘 Getting Help

- **Issues:** https://github.com/CamdenBibro/claim-assist/issues
- **Colab Docs:** https://colab.research.google.com/
- **Model Info:** https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF

---

## 🎉 Complete Notebook

Want a ready-to-use notebook? [Open in Colab](https://colab.research.google.com/) and copy this full notebook:

### Fast Version (eBay Only - Recommended)

```python
# ======================================
# Claim Assist - Google Colab Notebook
# Fast Version (eBay only)
# ======================================

# 1. Install dependencies
!pip install -q llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
!pip install -q huggingface-hub

# 2. Download model
from huggingface_hub import hf_hub_download
model_path = hf_hub_download(
    repo_id="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
    filename="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
)

# 3. Setup Claim Assist
!git clone https://github.com/CamdenBibro/claim-assist.git
%cd claim-assist
!pip install -q -r requirements-minimal.txt

# 4. Upload claims CSV
from google.colab import files
uploaded = files.upload()
claims_file = list(uploaded.keys())[0]

# 5. Configure and process
import os
os.environ['INFERENCE_BACKEND'] = 'llamacpp_python'
os.environ['MODEL_PATH'] = model_path
os.environ['N_GPU_LAYERS'] = '50'

!python -m claim_assist.main {claims_file}

# 6. Download results
import glob
for f in glob.glob("*_results.csv") + glob.glob("*_review.csv"):
    files.download(f)
```

### Comprehensive Version (All Sources - Slower)

```python
# ======================================
# Claim Assist - Google Colab Notebook
# With Facebook Marketplace & Mercari
# ======================================

# 1. Install dependencies (including Selenium)
!pip install -q llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
!pip install -q huggingface-hub selenium undetected-chromedriver

# Install Chrome and chromedriver (Colab specific)
!apt-get update
!apt-get install -y chromium-chromedriver chromium-browser

# 2. Download model
from huggingface_hub import hf_hub_download
model_path = hf_hub_download(
    repo_id="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
    filename="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
)

# 3. Setup Claim Assist
!git clone https://github.com/CamdenBibro/claim-assist.git
%cd claim-assist
!pip install -q -r requirements-minimal.txt

# 4. Upload claims CSV
from google.colab import files
uploaded = files.upload()
claims_file = list(uploaded.keys())[0]

# 5. Configure with Selenium enabled
import os
os.environ['INFERENCE_BACKEND'] = 'llamacpp_python'
os.environ['MODEL_PATH'] = model_path
os.environ['N_GPU_LAYERS'] = '50'
os.environ['ENABLE_SELENIUM'] = 'true'  # Enable Facebook/Mercari

!python -m claim_assist.main {claims_file}

# 6. Download results
import glob
for f in glob.glob("*_results.csv") + glob.glob("*_review.csv"):
    files.download(f)
```

**That's it! 🎊 You're ready to process insurance claims in the cloud!**
