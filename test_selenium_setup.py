#!/usr/bin/env python3
"""
Test script to verify Selenium setup in Google Colab
Run this to debug Chrome/Selenium issues
"""

import os
import sys

def test_chrome_installation():
    """Test if Chrome/Chromium is installed"""
    print("=" * 60)
    print("Testing Chrome Installation")
    print("=" * 60)
    
    chrome_paths = [
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
        '/usr/bin/google-chrome',
        '/snap/bin/chromium'
    ]
    
    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Found Chrome at: {path}")
            chrome_found = True
            
            # Try to get version
            try:
                import subprocess
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                print(f"   Version: {result.stdout.strip()}")
            except Exception as e:
                print(f"   ⚠️ Could not get version: {e}")
        else:
            print(f"❌ Not found: {path}")
    
    if not chrome_found:
        print("\n❌ Chrome not installed!")
        print("   Run: !apt-get install -y chromium-browser")
        return False
    
    print("\n✅ Chrome is installed")
    return True


def test_chromedriver_installation():
    """Test if chromedriver is installed"""
    print("\n" + "=" * 60)
    print("Testing Chromedriver Installation")
    print("=" * 60)
    
    chromedriver_paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver'
    ]
    
    driver_found = False
    for path in chromedriver_paths:
        if os.path.exists(path):
            print(f"✅ Found chromedriver at: {path}")
            driver_found = True
            
            # Try to get version
            try:
                import subprocess
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                print(f"   Version: {result.stdout.strip()}")
            except Exception as e:
                print(f"   ⚠️ Could not get version: {e}")
        else:
            print(f"❌ Not found: {path}")
    
    if not driver_found:
        print("\n❌ Chromedriver not installed!")
        print("   Run: !apt-get install -y chromium-chromedriver")
        return False
    
    print("\n✅ Chromedriver is installed")
    return True


def test_selenium_import():
    """Test if selenium is installed"""
    print("\n" + "=" * 60)
    print("Testing Selenium Import")
    print("=" * 60)
    
    try:
        import selenium
        print(f"✅ Selenium installed: {selenium.__version__}")
    except ImportError:
        print("❌ Selenium not installed!")
        print("   Run: !pip install selenium")
        return False
    
    try:
        import undetected_chromedriver
        print(f"✅ Undetected-chromedriver installed")
    except ImportError:
        print("❌ Undetected-chromedriver not installed!")
        print("   Run: !pip install undetected-chromedriver")
        return False
    
    return True


def test_selenium_initialization():
    """Test if Selenium can initialize a browser"""
    print("\n" + "=" * 60)
    print("Testing Selenium Initialization")
    print("=" * 60)
    
    try:
        import undetected_chromedriver as uc
        
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Try to find Chrome
        chrome_paths = [
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/usr/bin/google-chrome'
        ]
        
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                options.binary_location = chrome_path
                print(f"Using Chrome at: {chrome_path}")
                break
        
        print("Initializing WebDriver...")
        driver = uc.Chrome(options=options)
        
        print("✅ WebDriver initialized successfully!")
        
        # Test navigation
        print("Testing navigation...")
        driver.get("https://www.google.com")
        print(f"✅ Navigated to Google, title: {driver.title}")
        
        driver.quit()
        print("✅ WebDriver closed cleanly")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize WebDriver: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_claim_assist_scraper():
    """Test claim-assist selenium scraper"""
    print("\n" + "=" * 60)
    print("Testing Claim Assist Selenium Scraper")
    print("=" * 60)
    
    try:
        from claim_assist.utils.selenium_scraper import get_selenium_scraper
        
        print("Creating scraper...")
        with get_selenium_scraper(headless=True) as scraper:
            print("✅ Scraper created successfully!")
            
            print("Testing eBay search...")
            # Don't actually search to avoid rate limits
            print("✅ Scraper is ready to use!")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test scraper: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("🔍 SELENIUM SETUP DIAGNOSTIC")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(("Chrome Installation", test_chrome_installation()))
    results.append(("Chromedriver Installation", test_chromedriver_installation()))
    results.append(("Selenium Import", test_selenium_import()))
    results.append(("Selenium Initialization", test_selenium_initialization()))
    results.append(("Claim Assist Scraper", test_claim_assist_scraper()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("Selenium is ready to use for Facebook/Mercari scraping")
    else:
        print("❌ SOME TESTS FAILED")
        print("Follow the instructions above to fix the issues")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
