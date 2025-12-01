"""
Selenium-based web scraper for Facebook Marketplace and Mercari
Handles JavaScript-heavy sites that block simple HTTP requests
"""

import time
import re
from typing import List, Optional
from dataclasses import dataclass
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)


@dataclass
class PriceResult:
    """A single price result from web scraping"""
    source: str
    title: str
    price: float
    url: str
    condition: Optional[str] = None
    shipping: Optional[float] = None
    location: Optional[str] = None


class SeleniumScraper:
    """
    Browser automation scraper for sites that block bots
    Requires: pip install selenium undetected-chromedriver
    """
    
    def __init__(self, headless: bool = True, delay: float = 2.0, max_results: int = 10):
        """
        Initialize Selenium scraper
        
        Args:
            headless: Run browser in headless mode (no GUI)
            delay: Delay between actions (seconds)
            max_results: Maximum results per source
        """
        self.headless = headless
        self.delay = delay
        self.max_results = max_results
        self.driver = None
    
    def __enter__(self):
        """Context manager entry - initialize browser"""
        self._init_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup browser"""
        self.close()
    
    def _init_driver(self):
        """Initialize Selenium WebDriver with undetected-chromedriver"""
        try:
            import undetected_chromedriver as uc
            
            options = uc.ChromeOptions()
            
            if self.headless:
                options.add_argument('--headless=new')
            
            # Anti-detection options
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # Random user agent
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            self.driver = uc.Chrome(options=options)
            logger.info("Selenium WebDriver initialized successfully")
            
        except ImportError:
            raise ImportError(
                "Selenium scraper requires additional packages. Install with:\n"
                "pip install selenium undetected-chromedriver"
            )
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def close(self):
        """Close browser and cleanup"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")
    
    def search_all_sources(self, query: str) -> List[PriceResult]:
        """
        Search all sources with Selenium
        
        Args:
            query: Search query
            
        Returns:
            Combined results from all sources
        """
        results = []
        
        # Search Facebook Marketplace
        try:
            fb_results = self.search_facebook_marketplace(query)
            results.extend(fb_results)
            logger.info(f"Found {len(fb_results)} results from Facebook Marketplace")
            time.sleep(self.delay)
        except Exception as e:
            logger.warning(f"Facebook Marketplace search failed: {e}")
        
        # Search Mercari
        try:
            mercari_results = self.search_mercari(query)
            results.extend(mercari_results)
            logger.info(f"Found {len(mercari_results)} results from Mercari")
            time.sleep(self.delay)
        except Exception as e:
            logger.warning(f"Mercari search failed: {e}")
        
        return results
    
    def search_facebook_marketplace(self, query: str) -> List[PriceResult]:
        """
        Search Facebook Marketplace using Selenium
        
        Args:
            query: Search query
            
        Returns:
            List of price results
        """
        if not self.driver:
            self._init_driver()
        
        results = []
        encoded_query = quote_plus(query)
        url = f"https://www.facebook.com/marketplace/search/?query={encoded_query}"
        
        try:
            logger.info(f"Searching Facebook Marketplace: {query}")
            self.driver.get(url)
            time.sleep(3)  # Wait for dynamic content to load
            
            # Scroll to load more items
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Find listing elements (Facebook's structure changes frequently)
            # This is a best-effort approach that may need updates
            listings = self.driver.find_elements("css selector", "div[data-testid='marketplace-listing']")
            
            if not listings:
                # Try alternative selectors
                listings = self.driver.find_elements("css selector", "a[href*='/marketplace/item/']")
            
            logger.info(f"Found {len(listings)} Facebook listings")
            
            for listing in listings[:self.max_results]:
                try:
                    result = self._parse_facebook_listing(listing)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.debug(f"Failed to parse Facebook listing: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Facebook Marketplace scraping error: {e}")
        
        return results
    
    def _parse_facebook_listing(self, element) -> Optional[PriceResult]:
        """Parse a Facebook Marketplace listing element"""
        try:
            # Extract title
            title_elem = element.find_element("css selector", "span")
            title = title_elem.text if title_elem else "Unknown"
            
            # Extract price
            price_text = element.text
            price_match = re.search(r'\$[\d,]+', price_text)
            if not price_match:
                return None
            
            price_str = price_match.group(0).replace('$', '').replace(',', '')
            price = float(price_str)
            
            # Extract URL
            url = element.get_attribute('href')
            if not url:
                url = "https://www.facebook.com/marketplace"
            
            # Extract location (if available)
            location = None
            location_match = re.search(r'([A-Z][a-z]+,\s*[A-Z]{2})', price_text)
            if location_match:
                location = location_match.group(1)
            
            return PriceResult(
                source="Facebook Marketplace",
                title=title,
                price=price,
                url=url,
                location=location
            )
        
        except Exception as e:
            logger.debug(f"Error parsing Facebook listing: {e}")
            return None
    
    def search_mercari(self, query: str) -> List[PriceResult]:
        """
        Search Mercari using Selenium
        
        Args:
            query: Search query
            
        Returns:
            List of price results
        """
        if not self.driver:
            self._init_driver()
        
        results = []
        encoded_query = quote_plus(query)
        url = f"https://www.mercari.com/search/?keyword={encoded_query}"
        
        try:
            logger.info(f"Searching Mercari: {query}")
            self.driver.get(url)
            time.sleep(3)  # Wait for page load
            
            # Scroll to load more items
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Find listing elements
            listings = self.driver.find_elements("css selector", "div[data-testid='SearchResults'] li")
            
            if not listings:
                # Try alternative selector
                listings = self.driver.find_elements("css selector", "a[href*='/item/']")
            
            logger.info(f"Found {len(listings)} Mercari listings")
            
            for listing in listings[:self.max_results]:
                try:
                    result = self._parse_mercari_listing(listing)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.debug(f"Failed to parse Mercari listing: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Mercari scraping error: {e}")
        
        return results
    
    def _parse_mercari_listing(self, element) -> Optional[PriceResult]:
        """Parse a Mercari listing element"""
        try:
            # Extract price
            price_elem = element.find_element("css selector", "span[data-testid='ItemPrice']")
            price_text = price_elem.text if price_elem else element.text
            
            price_match = re.search(r'\$[\d,]+', price_text)
            if not price_match:
                return None
            
            price_str = price_match.group(0).replace('$', '').replace(',', '')
            price = float(price_str)
            
            # Extract title
            title_elem = element.find_element("css selector", "span[data-testid='ItemName']")
            title = title_elem.text if title_elem else "Unknown"
            
            # Extract URL
            link_elem = element.find_element("css selector", "a")
            url = link_elem.get_attribute('href') if link_elem else "https://www.mercari.com"
            
            # Extract condition (if available)
            condition = None
            condition_elem = element.find_elements("css selector", "span[data-testid='ItemCondition']")
            if condition_elem:
                condition = condition_elem[0].text
            
            return PriceResult(
                source="Mercari",
                title=title,
                price=price,
                url=url,
                condition=condition
            )
        
        except Exception as e:
            logger.debug(f"Error parsing Mercari listing: {e}")
            return None


def get_selenium_scraper(headless: bool = True, delay: float = 2.0, max_results: int = 10) -> SeleniumScraper:
    """
    Factory function to create Selenium scraper
    
    Usage:
        with get_selenium_scraper() as scraper:
            results = scraper.search_all_sources("iPhone 13")
    
    Args:
        headless: Run browser in headless mode
        delay: Delay between actions
        max_results: Max results per source
        
    Returns:
        SeleniumScraper instance
    """
    return SeleniumScraper(headless=headless, delay=delay, max_results=max_results)
