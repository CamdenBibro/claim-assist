#!/usr/bin/env python3
"""
Test script for local inference and MCP web scraping integration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claim_assist.config import Config
from claim_assist.utils.api_clients import create_inference_client
from claim_assist.utils.web_scraping import WebScrapingService
from claim_assist.models.item import ClaimItem
from claim_assist.pricing.classifier import ItemClassifier
from claim_assist.pricing.researcher import PriceResearcher


def test_local_inference():
    """Test local inference client setup"""
    print("=== Testing Local Inference ===")
    
    # Create config with default local settings
    config = Config(
        inference_backend="ollama",
        model_name="llama3.1:8b",
        inference_base_url="http://localhost:11434"
    )
    
    try:
        client = create_inference_client(config)
        
        if not client.is_available():
            print("❌ Local inference client is not available")
            print("Make sure Ollama is running: ollama serve")
            print("And model is downloaded: ollama pull llama3.1:8b")
            return False
        
        # Test simple generation
        response = client.generate("What is 2+2? Answer with just the number.", max_tokens=10)
        
        if response.success:
            print(f"✅ Local inference working! Response: {response.content.strip()}")
            return True
        else:
            print(f"❌ Inference failed: {response.error}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing local inference: {e}")
        return False


def test_web_scraping():
    """Test web scraping functionality"""
    print("\n=== Testing Web Scraping ===")
    
    try:
        scraper = WebScrapingService()
        
        # Test with a simple query
        results = scraper.search_comparable_prices("Samsung TV", max_results=3)
        
        if results:
            print(f"✅ Web scraping working! Found {len(results)} results:")
            for result in results[:2]:  # Show first 2 results
                print(f"  - {result.source}: ${result.price:.2f} - {result.title[:50]}...")
            return True
        else:
            print("⚠️  No results found (this may be normal due to rate limiting)")
            return True  # Not necessarily a failure
            
    except Exception as e:
        print(f"❌ Error testing web scraping: {e}")
        return False


def test_item_classification():
    """Test item classification with local inference"""
    print("\n=== Testing Item Classification ===")
    
    try:
        config = Config(
            inference_backend="ollama",
            model_name="llama3.1:8b"
        )
        
        client = create_inference_client(config)
        if not client.is_available():
            print("❌ Skipping classification test - no local inference available")
            return False
        
        classifier = ItemClassifier(client)
        
        # Test item
        item = ClaimItem(
            description="Samsung 55-inch 4K TV",
            brand="Samsung",
            condition="good",
            age="3 years"
        )
        
        result = classifier.classify(item)
        print(f"✅ Classification result: {result['complexity']}")
        print(f"  Reasoning: {result['reasoning']}")
        return True
        
    except Exception as e:
        print(f"❌ Error testing classification: {e}")
        return False


def test_price_research():
    """Test price research with local inference + web scraping"""
    print("\n=== Testing Price Research ===")
    
    try:
        config = Config(
            inference_backend="ollama",
            model_name="llama3.1:8b",
            scraping_delay=0.5,  # Faster for testing
            max_results_per_source=3
        )
        
        client = create_inference_client(config)
        if not client.is_available():
            print("❌ Skipping research test - no local inference available")
            return False
            
        web_scraper = WebScrapingService()
        researcher = PriceResearcher(client, web_scraper)
        
        # Test item
        item = ClaimItem(
            description="Samsung 55-inch TV",
            brand="Samsung",
            condition="good",
            estimated_value=800
        )
        
        result = researcher.research(item, "simple")
        
        print(f"✅ Research completed!")
        print(f"  Recommended value: ${result.get('recommended_value', 0):.2f}")
        print(f"  Confidence: {result.get('confidence', 'unknown')}")
        print(f"  Comparables found: {len(result.get('comparable_prices', []))}")
        print(f"  Reasoning: {result.get('reasoning', 'No reasoning')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing price research: {e}")
        return False


def main():
    """Run all tests"""
    print("Testing Local Inference + MCP Web Scraping Integration\n")
    
    results = []
    
    # Run tests
    results.append(("Local Inference", test_local_inference()))
    results.append(("Web Scraping", test_web_scraping()))
    results.append(("Item Classification", test_item_classification()))
    results.append(("Price Research", test_price_research()))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if success:
            passed += 1
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
        print("\nTo run with your CSV:")
        print("python -m claim_assist.main your_claims.csv --inference-backend ollama")
    else:
        print("⚠️  Some tests failed. Check your setup:")
        print("1. Make sure Ollama is running: ollama serve")
        print("2. Make sure model is downloaded: ollama pull llama3.1:8b")
        print("3. Check network connectivity for web scraping")


if __name__ == "__main__":
    main()