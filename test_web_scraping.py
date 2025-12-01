#!/usr/bin/env python3
"""
Test web scraping to diagnose why no results are found
"""

from claim_assist.utils.web_scraping import MCPWebScraper, WebScrapingService

def test_ebay_scraper():
    """Test eBay scraping directly"""
    print("=" * 60)
    print("Testing eBay Scraper")
    print("=" * 60)
    
    scraper = MCPWebScraper(delay_between_requests=1.0, max_results_per_source=10)
    
    # Test queries
    test_queries = [
        "Samsung 55 inch 4K TV",
        "Apple MacBook Pro 14",
        "Sony PlayStation 5"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching eBay for: '{query}'")
        print("-" * 60)
        
        try:
            results = scraper._search_ebay(query)
            
            if results:
                print(f"✅ Found {len(results)} results:")
                for i, result in enumerate(results[:5], 1):
                    print(f"   {i}. {result.title[:60]}")
                    print(f"      Price: ${result.price:.2f}")
                    print(f"      Source: {result.source}")
                    print(f"      URL: {result.url[:80]}...")
                    print()
            else:
                print(f"❌ No results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)


def test_web_scraping_service():
    """Test the full WebScrapingService"""
    print("\n" + "=" * 60)
    print("Testing WebScrapingService")
    print("=" * 60)
    
    service = WebScrapingService(use_alternative_sources=False, use_selenium=False)
    
    query = "Samsung 55 inch 4K TV"
    print(f"\n🔍 Searching for: '{query}'")
    print("-" * 60)
    
    try:
        results = service.search_comparable_prices(query, max_results=20)
        
        if results:
            print(f"✅ Found {len(results)} total results:")
            
            # Group by source
            by_source = {}
            for result in results:
                if result.source not in by_source:
                    by_source[result.source] = []
                by_source[result.source].append(result)
            
            for source, items in by_source.items():
                print(f"\n   {source}: {len(items)} results")
                for item in items[:3]:
                    print(f"      - ${item.price:.2f}: {item.title[:50]}")
        else:
            print(f"❌ No results found")
            print("\nPossible issues:")
            print("   1. eBay HTML structure changed")
            print("   2. Network/firewall blocking requests")
            print("   3. Rate limiting")
            print("   4. BeautifulSoup parsing errors")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)


def test_requests():
    """Test if basic HTTP requests work"""
    print("\n" + "=" * 60)
    print("Testing Basic HTTP Requests")
    print("=" * 60)
    
    import requests
    
    test_urls = [
        ("Google", "https://www.google.com"),
        ("eBay Search", "https://www.ebay.com/sch/i.html?_nkw=samsung+tv"),
    ]
    
    for name, url in test_urls:
        print(f"\n🔍 Testing {name}: {url[:60]}...")
        try:
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            print(f"   Content length: {len(response.content)} bytes")
            
            if response.status_code == 200:
                print(f"   ✅ Success")
            else:
                print(f"   ⚠️ Non-200 status code")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n🧪 WEB SCRAPING DIAGNOSTIC TOOL\n")
    
    # Test basic connectivity
    test_requests()
    
    # Test eBay scraper
    test_ebay_scraper()
    
    # Test full service
    test_web_scraping_service()
    
    print("\n✅ Diagnostic complete!")
    print("\nIf all tests show 'No results found', the eBay scraper may need updating.")
    print("Check SELENIUM_SETUP.md for alternative scraping methods.\n")
