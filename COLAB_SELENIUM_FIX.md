# Quick Fix for Selenium in Google Colab

Run these commands in your Colab notebook to fix the "Binary Location Must be a String" error:

```python
# Cell 1: Install Chrome and chromedriver properly for Colab
# Use apt to install chromium (not snap, which doesn't work in Colab)
!apt-get update
!apt-get install -y chromium-chromedriver
!apt-get install -y chromium-browser

# Verify paths
!which chromedriver
!ls -la /usr/bin/chromedriver
!ls -la /usr/bin/chromium-browser

print("✅ Chrome and chromedriver installed!")
```

```python
# Cell 2: Verify installation
!chromedriver --version

print("✅ Versions confirmed!")
```

```python
# Cell 3: Install Selenium packages if not already installed
!pip install -q selenium undetected-chromedriver

print("✅ Selenium packages ready!")
```

```python
# Cell 3: Test Selenium
from claim_assist.utils.selenium_scraper import get_selenium_scraper

try:
    with get_selenium_scraper(headless=True) as scraper:
        print("✅ Selenium initialized successfully!")
        results = scraper.search_facebook_marketplace("iPhone 13")
        print(f"Found {len(results)} results from Facebook")
        for result in results[:3]:
            print(f"  - {result.title}: ${result.price}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
```

## Alternative: Disable Selenium

If Selenium continues to fail, you can disable it and still get good results from eBay:

```python
import os

# Disable Selenium (use eBay only - faster and reliable)
os.environ['ENABLE_SELENIUM'] = 'false'

# Or just don't set it at all (default is false)
# del os.environ['ENABLE_SELENIUM']

# Process claims
!python -m claim_assist.main your_claims.csv
```

## Why This Happens

Google Colab has Chrome installed at a non-standard location. The fix:

1. Install `chromium-browser` and `chromium-chromedriver`
2. Copy chromedriver to `/usr/bin/` 
3. Updated selenium_scraper.py detects Colab and uses the correct Chrome binary

## Quick Comparison

| Method | Speed | Sources | Setup |
|--------|-------|---------|-------|
| **eBay Only** (no Selenium) | ⚡ Fast | 1 source | ✅ Zero setup |
| **With Selenium** | 🐢 Slow | 4 sources | ⚠️ Needs Chrome setup |

**Recommendation for Colab:** Start without Selenium. Only enable it if you need Facebook/Mercari data and are willing to do the setup.
