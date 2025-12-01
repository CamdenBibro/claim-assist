"""
MCP-based web scraping service for insurance claim pricing
Scrapes eBay and Facebook Marketplace for comparable prices
"""

import json
import re
import time
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup
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


class MCPWebScraper:
    """Web scraper using MCP (Model Context Protocol) approach"""
    
    def __init__(self, delay_between_requests: float = 1.0, max_results_per_source: int = 10):
        self.delay = delay_between_requests
        self.max_results = max_results_per_source
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def search_all_sources(self, query: str) -> List[PriceResult]:
        """
        Search all configured sources for pricing data
        
        Args:
            query: Search query for the item
            
        Returns:
            List of PriceResult objects from all sources
        """
        all_results = []
        
        # Search eBay
        try:
            ebay_results = self._search_ebay(query)
            all_results.extend(ebay_results)
            time.sleep(self.delay)
        except Exception as e:
            logger.warning(f"eBay search failed for '{query}': {e}")
        
        # Search Facebook Marketplace (DISABLED - Facebook blocks automated scraping)
        # Facebook returns 400 errors and doesn't allow bots
        # Uncomment and use alternative methods (Selenium, API) if needed
        # try:
        #     facebook_results = self._search_facebook_marketplace(query)
        #     all_results.extend(facebook_results)
        #     time.sleep(self.delay)
        # except Exception as e:
        #     logger.warning(f"Facebook Marketplace search failed for '{query}': {e}")
        
        return all_results
    
    def _search_ebay(self, query: str) -> List[PriceResult]:
        """Search eBay for completed/sold listings"""
        try:
            # eBay search parameters for sold listings
            params = {
                '_nkw': query,
                '_sacat': '0',  # All categories
                'LH_Sold': '1',  # Sold listings only
                'LH_Complete': '1',  # Completed listings
                '_sop': '13',  # Sort by time (newest first)
                '_ipg': str(min(self.max_results, 50)),  # Items per page
            }
            
            url = f"https://www.ebay.com/sch/i.html?{urlencode(params)}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Parse eBay search results - eBay now uses s-card structure
            # Find the results list and get all card items
            results_list = soup.find('ul', class_='srp-results')
            if not results_list:
                logger.warning("No results list found in eBay HTML")
                return results
            
            items = results_list.find_all('li', class_='s-card')
            logger.debug(f"Found {len(items)} eBay card items")
            
            for item in items[:self.max_results]:
                try:
                    price_info = self._extract_ebay_price(item)
                    if price_info:
                        results.append(price_info)
                except Exception as e:
                    logger.debug(f"Failed to parse eBay item: {e}")
                    continue
            
            logger.info(f"Found {len(results)} eBay results for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"eBay search error: {e}")
            return []
    
    def _extract_ebay_price(self, item_element) -> Optional[PriceResult]:
        """Extract price information from eBay item element (s-card structure)"""
        try:
            # Find title - now in div.s-card__title
            title_elem = item_element.find('div', class_='s-card__title')
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)
            
            # Skip if title is empty or a placeholder
            if not title or len(title) < 5:
                return None
            
            # Find price - now in span.s-card__price
            price_elem = item_element.find('span', class_='s-card__price')
            if not price_elem:
                return None
            
            price_text = price_elem.get_text(strip=True)
            price = self._parse_price(price_text)
            if not price:
                return None
            
            # Find URL - first a.s-card__link
            link_elem = item_element.find('a', class_='s-card__link')
            url = link_elem.get('href', '') if link_elem else ''
            
            # Find condition - look for span with condition text
            condition = None
            condition_keywords = ['New', 'Used', 'Refurbished', 'Open Box', 'For Parts']
            for span in item_element.find_all('span', class_='su-styled-text'):
                text = span.get_text(strip=True)
                if any(keyword in text for keyword in condition_keywords):
                    condition = text
                    break
            
            # Find shipping - look for "Free" or shipping cost
            shipping = None
            shipping_text = ''
            for span in item_element.find_all('span', class_='su-styled-text'):
                text = span.get_text(strip=True)
                if 'shipping' in text.lower() or 'delivery' in text.lower():
                    shipping_text = text
                    if 'free' in text.lower():
                        shipping = 0.0
                    else:
                        shipping = self._parse_price(text)
                    break
            
            return PriceResult(
                source="eBay",
                title=title,
                price=price,
                url=url,
                condition=condition,
                shipping=shipping
            )
            
        except Exception as e:
            logger.debug(f"Failed to extract eBay price: {e}")
            return None
    
    def _search_facebook_marketplace(self, query: str) -> List[PriceResult]:
        """Search Facebook Marketplace (simplified approach)"""
        try:
            # Facebook Marketplace is harder to scrape due to authentication
            # This is a simplified implementation that would need to be enhanced
            # For production, you might want to use Facebook's API or a specialized service
            
            # Basic approach using public search (limited functionality)
            encoded_query = quote_plus(query)
            url = f"https://www.facebook.com/marketplace/search/?query={encoded_query}"
            
            # Note: This will likely be blocked or require authentication
            # In practice, you'd need to use selenium or a specialized service
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Facebook's dynamic content makes this challenging
                # This is a placeholder implementation
                return self._parse_facebook_results(soup, query)
            else:
                logger.warning(f"Facebook Marketplace returned status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Facebook Marketplace search error: {e}")
            return []
    
    def _parse_facebook_results(self, soup: BeautifulSoup, query: str) -> List[PriceResult]:
        """Parse Facebook Marketplace results (placeholder)"""
        # This is a simplified placeholder
        # Real implementation would need to handle Facebook's dynamic content
        results = []
        
        # Facebook uses dynamic loading, so static scraping is limited
        # You might need to use Selenium or Facebook Graph API
        
        logger.info(f"Facebook Marketplace parsing not fully implemented for '{query}'")
        return results
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and extract numbers
        price_text = re.sub(r'[^\d.,]', '', price_text)
        price_text = price_text.replace(',', '')
        
        try:
            return float(price_text)
        except (ValueError, TypeError):
            return None


class AlternativeSourceScraper:
    """Alternative scraper for when Facebook is not accessible"""
    
    def __init__(self, delay_between_requests: float = 1.0):
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def search_craigslist(self, query: str, location: str = "sfbay") -> List[PriceResult]:
        """Search Craigslist for items (as alternative to Facebook Marketplace)"""
        try:
            # Craigslist search URL
            encoded_query = quote_plus(query)
            url = f"https://{location}.craigslist.org/search/sss?query={encoded_query}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Parse Craigslist results
            items = soup.find_all('li', class_='result-row')
            
            for item in items[:10]:  # Limit results
                try:
                    price_info = self._extract_craigslist_price(item)
                    if price_info:
                        results.append(price_info)
                except Exception as e:
                    logger.debug(f"Failed to parse Craigslist item: {e}")
                    continue
            
            logger.info(f"Found {len(results)} Craigslist results for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Craigslist search error: {e}")
            return []
    
    def _extract_craigslist_price(self, item_element) -> Optional[PriceResult]:
        """Extract price from Craigslist item"""
        try:
            # Find price
            price_elem = item_element.find('span', class_='result-price')
            if not price_elem:
                return None
            
            price_text = price_elem.get_text(strip=True)
            price = self._parse_price(price_text)
            if not price:
                return None
            
            # Find title
            title_elem = item_element.find('a', class_='result-title')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown item"
            
            # Find URL
            url = title_elem.get('href', '') if title_elem else ''
            
            # Find location
            location_elem = item_element.find('span', class_='result-hood')
            location = location_elem.get_text(strip=True) if location_elem else None
            
            return PriceResult(
                source="Craigslist",
                title=title,
                price=price,
                url=url,
                location=location
            )
            
        except Exception as e:
            logger.debug(f"Failed to extract Craigslist price: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and extract numbers
        price_text = re.sub(r'[^\d.]', '', price_text)
        
        try:
            return float(price_text)
        except (ValueError, TypeError):
            return None


class WebScrapingService:
    """Main web scraping service that coordinates different scrapers"""
    
    def __init__(self, use_alternative_sources: bool = True, use_selenium: bool = False):
        """
        Initialize web scraping service
        
        Args:
            use_alternative_sources: Enable Craigslist as alternative
            use_selenium: Enable Selenium for Facebook/Mercari (slower but bypasses blocks)
        """
        self.main_scraper = MCPWebScraper()
        self.alt_scraper = AlternativeSourceScraper() if use_alternative_sources else None
        self.use_selenium = use_selenium
        self.selenium_scraper = None
    
    def search_comparable_prices(self, query: str, max_results: int = 20) -> List[PriceResult]:
        """
        Search for comparable prices across all available sources
        
        Args:
            query: Search query for the item
            max_results: Maximum total results to return
            
        Returns:
            List of PriceResult objects sorted by relevance
        """
        all_results = []
        
        # Search main sources (eBay - always works)
        main_results = self.main_scraper.search_all_sources(query)
        all_results.extend(main_results)
        
        # Use Selenium for Facebook Marketplace and Mercari if enabled
        if self.use_selenium:
            try:
                from .selenium_scraper import get_selenium_scraper
                
                with get_selenium_scraper(headless=True, max_results=10) as selenium_scraper:
                    selenium_results = selenium_scraper.search_all_sources(query)
                    all_results.extend(selenium_results)
                    logger.info(f"Selenium found {len(selenium_results)} additional results")
            
            except ImportError:
                logger.warning(
                    "Selenium scraper not available. Install with: "
                    "pip install selenium undetected-chromedriver"
                )
            except Exception as e:
                logger.warning(f"Selenium scraping failed: {e}")
        
        # Search alternative sources if enabled and we need more results
        if self.alt_scraper and len(all_results) < max_results:
            alt_results = self.alt_scraper.search_craigslist(query)
            all_results.extend(alt_results)
        
        # Remove duplicates and sort by price
        unique_results = self._deduplicate_results(all_results)
        sorted_results = sorted(unique_results, key=lambda x: x.price)
        
        return sorted_results[:max_results]
    
    def _deduplicate_results(self, results: List[PriceResult]) -> List[PriceResult]:
        """Remove duplicate results based on title similarity and price"""
        if not results:
            return results
        
        unique_results = []
        seen_items = set()
        
        for result in results:
            # Create a simple key for deduplication
            key = (result.source, result.title.lower()[:50], round(result.price, 2))
            
            if key not in seen_items:
                seen_items.add(key)
                unique_results.append(result)
        
        return unique_results
    
    def format_results_for_llm(self, results: List[PriceResult]) -> Dict:
        """Format scraping results for LLM processing"""
        if not results:
            return {
                "price_sources": [],
                "comparable_prices": [],
                "sources": [],
                "price_source_details": []
            }
        
        price_sources = []
        comparable_prices = []
        sources = []
        price_source_details = []
        
        for result in results:
            price_sources.append({
                "source": result.source,
                "price": result.price
            })
            comparable_prices.append(result.price)
            sources.append(result.source)
            price_source_details.append(f"{result.source}: ${result.price:.2f}")
        
        return {
            "price_sources": price_sources,
            "comparable_prices": comparable_prices,
            "sources": sources,
            "price_source_details": price_source_details,
            "search_metadata": {
                "total_results": len(results),
                "price_range": f"${min(comparable_prices):.2f} - ${max(comparable_prices):.2f}" if comparable_prices else "No prices found"
            }
        }


def generate_search_queries(item_description: str, brand: str = None, model: str = None) -> List[str]:
    """Generate multiple search queries for better price coverage"""
    queries = []
    
    # Basic query
    queries.append(item_description)
    
    # Brand + description
    if brand:
        queries.append(f"{brand} {item_description}")
    
    # Model specific
    if model:
        queries.append(f"{brand} {model}" if brand else model)
    
    # Add "used" to queries to find secondhand prices
    base_query = f"{brand} {item_description}" if brand else item_description
    queries.append(f"used {base_query}")
    
    # Remove duplicates and return
    return list(dict.fromkeys(queries))  # Preserves order while removing duplicates