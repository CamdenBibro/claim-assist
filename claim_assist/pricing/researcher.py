import json
import statistics
from typing import Dict, List
from ..models.item import ClaimItem, Complexity
from ..utils.local_inference import LocalInferenceClient
from ..utils.web_scraping import WebScrapingService, generate_search_queries


class PriceResearcher:
    """Researches comparable prices using local LLM with MCP web scraping"""

    def __init__(
        self,
        inference_client: LocalInferenceClient,
        web_scraping_service: WebScrapingService,
        use_complex_model_for_complex_items: bool = True
    ):
        self.client = inference_client
        self.web_scraper = web_scraping_service
        self.use_complex_model = use_complex_model_for_complex_items

    def research(self, item: ClaimItem, complexity: str) -> Dict:
        """
        Research comparable prices for an item using web scraping + local LLM analysis

        Args:
            item: ClaimItem to research
            complexity: Complexity level (simple|moderate|complex)

        Returns:
            Dict with comparable_prices, sources, recommended_value, confidence, reasoning, search_queries_used
        """
        item_dict = item.to_dict()

        try:
            # Step 1: Generate search queries
            search_queries = generate_search_queries(
                item_description=item_dict['description'],
                brand=item_dict.get('brand'),
                model=None  # Could be extracted from description in the future
            )

            # Step 2: Scrape web for comparable prices
            all_price_results = []
            used_queries = []
            
            for query in search_queries[:3]:  # Limit to 3 queries to avoid rate limiting
                try:
                    results = self.web_scraper.search_comparable_prices(query, max_results=10)
                    if results:
                        all_price_results.extend(results)
                        used_queries.append(query)
                except Exception as e:
                    print(f"Failed to search for '{query}': {e}")
                    continue

            # Step 3: Analyze results with local LLM
            if all_price_results:
                analysis = self._analyze_prices_with_llm(item, all_price_results, complexity)
                analysis['search_queries_used'] = used_queries
                
                # Add structured price data
                formatted_results = self.web_scraper.format_results_for_llm(all_price_results)
                analysis.update(formatted_results)
                
                return analysis
            else:
                # No results found - fallback
                return self._fallback_result(item, "No comparable prices found in web search")

        except Exception as e:
            return self._fallback_result(item, f"Research failed: {str(e)}")

    def _analyze_prices_with_llm(self, item: ClaimItem, price_results: List, complexity: str) -> Dict:
        """Use local LLM to analyze scraped price results"""
        
        item_dict = item.to_dict()
        
        # Prepare price data for LLM
        price_list = [result.price for result in price_results]
        source_info = []
        for result in price_results:
            source_info.append(f"- {result.source}: ${result.price:.2f} - {result.title[:80]}")
        
        price_summary = "\n".join(source_info[:15])  # Limit to avoid token overflow
        
        prompt = f"""You are an insurance claim adjuster analyzing comparable prices for item valuation.

ITEM TO VALUE:
Description: {item_dict['description']}
Brand: {item_dict.get('brand', 'unknown')}
Condition: {item_dict.get('condition', 'unknown')}
Age: {item_dict.get('age', 'unknown')}
Estimated Value: ${item_dict.get('estimated_value', 'unknown')}

COMPARABLE PRICES FOUND:
{price_summary}

STATISTICAL DATA:
Total comparables: {len(price_list)}
Price range: ${min(price_list):.2f} - ${max(price_list):.2f}
Median price: ${statistics.median(price_list):.2f}
75th percentile: ${statistics.quantiles(price_list, n=4)[2]:.2f if len(price_list) >= 4 else statistics.median(price_list):.2f}

INSTRUCTIONS:
1. Calculate a fair replacement value using insurance industry standards (75th percentile preferred)
2. Account for the item's condition and age
3. Consider outliers and data quality
4. Assign confidence level based on number and quality of comparables

Respond with ONLY valid JSON in this exact format:
{{
    "recommended_value": calculated_replacement_value_number,
    "confidence": "low|medium|high",
    "reasoning": "Brief explanation of how you calculated the value and why"
}}

Confidence guidelines:
- High: 5+ comparables, tight price range, high-quality sources
- Medium: 3-4 comparables, reasonable price range  
- Low: <3 comparables, wide price range, or questionable data

Return only the JSON response, no other text."""

        try:
            response = self.client.generate(prompt, max_tokens=500, temperature=0.1)
            
            if not response.success:
                raise Exception(response.error)
            
            # Parse JSON response
            result = json.loads(response.content.strip())
            
            # Validate and set defaults
            result.setdefault('recommended_value', statistics.median(price_list))
            result.setdefault('confidence', 'medium')
            result.setdefault('reasoning', 'LLM analysis of comparable prices')
            
            # Ensure recommended_value is a number
            try:
                result['recommended_value'] = float(result['recommended_value'])
            except (ValueError, TypeError):
                result['recommended_value'] = statistics.median(price_list)
            
            return result

        except (json.JSONDecodeError, Exception) as e:
            # Fallback to statistical analysis if LLM fails
            return self._statistical_fallback_analysis(price_list, str(e))

    def _statistical_fallback_analysis(self, prices: List[float], error: str) -> Dict:
        """Fallback statistical analysis if LLM analysis fails"""
        if not prices:
            return {
                'recommended_value': 0,
                'confidence': 'low', 
                'reasoning': f'No prices available for analysis. Error: {error}'
            }
        
        # Use 75th percentile for insurance standard
        if len(prices) >= 4:
            recommended_value = statistics.quantiles(prices, n=4)[2]  # 75th percentile
            confidence = 'medium' if len(prices) >= 5 else 'low'
        else:
            recommended_value = statistics.median(prices)
            confidence = 'low'
        
        return {
            'recommended_value': recommended_value,
            'confidence': confidence,
            'reasoning': f'Statistical analysis used due to LLM error: {error}. Used {"75th percentile" if len(prices) >= 4 else "median"} of {len(prices)} comparables.'
        }

    def _fallback_result(self, item: ClaimItem, error: str) -> Dict:
        """Create fallback result when research fails"""
        estimated = item.estimated_value or 50.0

        return {
            'comparable_prices': [estimated],
            'sources': ['Estimated value (research failed)'],
            'price_sources': [{'source': 'Estimated', 'price': estimated}],
            'recommended_value': estimated,
            'confidence': 'low',
            'reasoning': f'{error}. Using estimated value.',
            'search_queries_used': [],
            'price_source_details': [f'Estimated: ${estimated:.2f}']
        }

