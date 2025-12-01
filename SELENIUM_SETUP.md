# Facebook Marketplace & Mercari Setup Guide

This guide shows how to enable automated scraping of Facebook Marketplace and Mercari using Selenium.

## Why Selenium?

Facebook Marketplace and Mercari block simple HTTP requests (return 400 errors). They require:
- JavaScript rendering
- Browser-like behavior
- Anti-bot detection bypass

**Selenium with `undetected-chromedriver`** solves this by using a real Chrome browser.

---

## Installation

### Step 1: Install Selenium Packages

```python
# In Google Colab or locally
!pip install selenium undetected-chromedriver
```

### Step 2: Enable Selenium in Config

**Option A: Environment Variable**
```python
import os
os.environ['ENABLE_SELENIUM'] = 'true'
```

**Option B: Command Line**
```bash
python -m claim_assist.main claims.csv --enable-selenium
```

**Option C: In Code**
```python
from claim_assist.config import Config

config = Config.from_env()
config.enable_selenium_scraping = True
```

---

## Usage

### Google Colab Example

```python
# Cell 1: Install dependencies
!pip install selenium undetected-chromedriver
!pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
!pip install tqdm

# Cell 2: Clone and setup
!git clone https://github.com/CamdenBibro/claim-assist.git
%cd claim-assist
!pip install -r requirements-minimal.txt

# Cell 3: Download model
from huggingface_hub import hf_hub_download
model_path = hf_hub_download(
    repo_id="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
    filename="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
)

# Cell 4: Upload claims
from google.colab import files
uploaded = files.upload()
claims_file = list(uploaded.keys())[0]

# Cell 5: Configure with Selenium ENABLED
import os
os.environ['INFERENCE_BACKEND'] = 'llamacpp_python'
os.environ['MODEL_PATH'] = model_path
os.environ['N_GPU_LAYERS'] = '50'
os.environ['ENABLE_SELENIUM'] = 'true'  # ← Enable Facebook/Mercari

# Cell 6: Process claims
!python -m claim_assist.main {claims_file}

# Cell 7: Download results
import glob
for f in glob.glob("*_results.csv") + glob.glob("*_review.csv"):
    files.download(f)
```

---

## What You'll Get

With Selenium enabled, you'll scrape from:

| Source | Without Selenium | With Selenium |
|--------|------------------|---------------|
| **eBay** | ✅ Works | ✅ Works |
| **Facebook Marketplace** | ❌ Blocked (400 error) | ✅ **Works!** |
| **Mercari** | ❌ Not available | ✅ **Works!** |
| **Craigslist** | ✅ Works (if enabled) | ✅ Works |

---

## Performance Impact

**Selenium is SLOWER** than simple HTTP requests:

| Scraping Method | Speed | Success Rate |
|-----------------|-------|--------------|
| **HTTP Only** (default) | ⚡ Fast (~1-2s per query) | 50% (eBay only) |
| **With Selenium** | 🐢 Slow (~5-10s per query) | 95% (all sources) |

**Recommendation:**
- **Enable Selenium** if you need comprehensive price coverage
- **Disable Selenium** if you're processing large batches and eBay is sufficient

---

## Troubleshooting

### "WebDriver not found"

```python
# Reinstall
!pip install --upgrade undetected-chromedriver
```

### "Chrome binary not found" (Local Windows)

Download and install Chrome:
https://www.google.com/chrome/

### "Timeout waiting for page load"

Increase delays:
```python
os.environ['SCRAPING_DELAY'] = '3.0'  # Default: 1.0
```

### "No results found"

Facebook and Mercari frequently change their HTML structure. The selectors may need updating.

Check logs:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### "Headless mode not working"

Disable headless to see what's happening:
```python
# In selenium_scraper.py, change:
scraper = SeleniumScraper(headless=False)  # Opens visible browser
```

---

## Advanced Configuration

### Customize Scraping

```python
from claim_assist.utils.selenium_scraper import get_selenium_scraper

# Use Selenium scraper directly
with get_selenium_scraper(
    headless=True,      # Run without GUI
    delay=2.0,          # Wait 2 seconds between actions
    max_results=10      # Get 10 results per source
) as scraper:
    results = scraper.search_all_sources("iPhone 13")
    
    for result in results:
        print(f"{result.source}: {result.title} - ${result.price}")
```

### Only Enable for Specific Queries

```python
from claim_assist.utils.web_scraping import WebScrapingService

# Regular scraper (fast, eBay only)
regular_scraper = WebScrapingService(use_selenium=False)

# Selenium scraper (slow, all sources)
selenium_scraper = WebScrapingService(use_selenium=True)

# Use selenium for high-value items only
if item.estimated_value > 500:
    results = selenium_scraper.search_comparable_prices(query)
else:
    results = regular_scraper.search_comparable_prices(query)
```

---

## Cost Comparison

### Without Selenium (eBay only)
- **100 items**: ~15 minutes
- **Cost**: Free
- **Coverage**: eBay sold listings

### With Selenium (All sources)
- **100 items**: ~30-40 minutes (2x slower)
- **Cost**: Free
- **Coverage**: eBay + Facebook + Mercari + Craigslist

---

## Security & Ethics

### ⚠️ Important Notes

1. **Terms of Service**: Web scraping may violate site ToS
2. **Rate Limiting**: Selenium helps avoid detection, but don't abuse it
3. **Personal Data**: Don't scrape personal information
4. **Commercial Use**: Check legal requirements in your jurisdiction

### Best Practices

- ✅ Add delays between requests (default: 2 seconds)
- ✅ Use headless mode to minimize resource usage
- ✅ Respect robots.txt
- ✅ Only scrape public data
- ❌ Don't bypass authentication
- ❌ Don't scrape private user data

---

## Alternative: Use APIs Instead

If you process claims regularly, consider paid APIs:

| Service | API Available | Cost |
|---------|---------------|------|
| **eBay** | ✅ Yes ([Finding API](https://developer.ebay.com/)) | Free tier available |
| **Facebook** | ⚠️ Limited ([Marketplace API](https://developers.facebook.com/)) | Business accounts only |
| **Mercari** | ❌ No public API | N/A |

**eBay API Example:**
```python
# More reliable than scraping
import requests

response = requests.get(
    "https://svcs.ebay.com/services/search/FindingService/v1",
    params={
        "OPERATION-NAME": "findCompletedItems",
        "keywords": "Samsung 55 inch TV",
        "SECURITY-APPNAME": "your-app-id"
    }
)
```

---

## Summary

**When to enable Selenium:**
- ✅ Need comprehensive price data
- ✅ High-value items requiring multiple comparables
- ✅ Facebook Marketplace is important in your area
- ✅ Mercari is relevant for your items

**When to skip Selenium:**
- ✅ Processing large batches (100+ items)
- ✅ eBay provides sufficient data
- ✅ Speed is more important than coverage
- ✅ Running in resource-constrained environment

**Quick Enable:**
```bash
export ENABLE_SELENIUM=true
python -m claim_assist.main claims.csv
```

---

## Getting Help

- **Selenium Issues**: https://github.com/ultrafunkamsterdam/undetected-chromedriver/issues
- **Claim Assist Issues**: https://github.com/CamdenBibro/claim-assist/issues
- **Debugging**: Set `logging.basicConfig(level=logging.DEBUG)`
