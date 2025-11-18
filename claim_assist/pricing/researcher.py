import json
from typing import Dict, List
import anthropic
from ..models.item import ClaimItem, Complexity


class PriceResearcher:
    """Researches comparable prices using LLM with web search capabilities"""

    def __init__(
        self,
        client: anthropic.Anthropic,
        simple_model: str = "claude-3-5-haiku-latest",
        complex_model: str =  "claude-sonnet-4-5-20250929" #"claude-3-5-haiku-latest"
    ):
        self.client = client
        self.simple_model = simple_model
        self.complex_model = complex_model

    def research(self, item: ClaimItem, complexity: str) -> Dict:
        """
        Research comparable prices for an item

        Args:
            item: ClaimItem to research
            complexity: Complexity level (simple|moderate|complex)

        Returns:
            Dict with comparable_prices, sources, recommended_value, confidence, reasoning, search_queries_used
        """
        item_dict = item.to_dict()

        search_prompt = f"""You are an insurance claim adjuster. Use web search to find replacement costs.

ITEM: {item_dict['description']}
BRAND: {item_dict.get('brand', 'unbranded')}
CONDITION: {item_dict.get('condition', 'used')}
AGE: {item_dict.get('age', 'unknown')}

Search ONLY eBay, Facebook Marketplace. Find 5-10 comparable prices. Do not include refurbished or auction prices. For ebay, only used items final sale or buy it now prices.

CRITICAL: Return ONLY this exact JSON format with NO additional text before or after:
{{
"price_sources":[{{"source":"source name","price":actual_price_number}},...],
"recommended_value":calculated_median_or_average,
"confidence":"low|medium|high",
"reasoning":"Brief explanation of how you arrived at this price",
"search_queries_used":["actual search query you used"]
}}

Rules:
- NO markdown formatting
- NO explanatory text outside the JSON
- Use double quotes for strings
- Numbers must not be quoted (use raw numbers like 650, not "650")
- Include ALL prices you found in price_sources array
- recommended_value should be the median or average of the prices found
- Array items separated by commas only"""

        # Use Sonnet for complex items, Haiku for simple/moderate
        model = self.complex_model if complexity == Complexity.COMPLEX.value else self.simple_model

        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=2000,
                messages=[{"role": "user", "content": search_prompt}],
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5
                }]
            )

            # Extract text content from the response
            text_content = ""
            for block in message.content:
                if block.type == "text":
                    text_content += block.text

            # Debug: print first 500 chars if extraction fails
            if not text_content.strip():
                raise ValueError("No text content in API response")

            # Extract JSON from text (Claude may wrap it in explanation)
            result = self._extract_json_from_text(text_content)

            # Validate and clean result
            result = self._validate_research_result(result)

            return result

        except (json.JSONDecodeError, anthropic.APIError) as e:
            # Return fallback result with estimated value if available
            return self._fallback_result(item, str(e))

    def _extract_json_from_text(self, text: str) -> Dict:
        """
        Extract JSON object from text that may contain explanations

        Args:
            text: Text that may contain JSON and other content

        Returns:
            Parsed JSON dictionary
        """
        # Try direct JSON parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Find the first { and matching } using bracket counting
        start_idx = text.find('{')
        if start_idx == -1:
            raise json.JSONDecodeError("No JSON object found in response", text, 0)

        bracket_count = 0
        in_string = False
        escape_next = False

        for i in range(start_idx, len(text)):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == '{':
                    bracket_count += 1
                elif char == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        # Found the matching closing bracket
                        json_str = text[start_idx:i+1]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError as e:
                            raise json.JSONDecodeError(f"Invalid JSON extracted: {e}", json_str, 0)

        # If we get here, no matching bracket was found
        raise json.JSONDecodeError("Could not find matching closing bracket for JSON", text, start_idx)

    def _validate_research_result(self, result: Dict) -> Dict:
        """Validate and clean research results"""

        # Handle new price_sources format or legacy format
        if 'price_sources' in result:
            # New format: list of {source, price} objects
            price_sources = result.get('price_sources', [])
            result['comparable_prices'] = [
                float(item['price']) for item in price_sources
                if isinstance(item, dict) and 'price' in item and item['price'] > 0
            ]
            result['sources'] = [
                item['source'] for item in price_sources
                if isinstance(item, dict) and 'source' in item
            ]
            # Store the structured data for detailed output
            result['price_source_details'] = [
                f"{item['source']}: ${float(item['price']):.2f}"
                for item in price_sources
                if isinstance(item, dict) and 'source' in item and 'price' in item
            ]
        else:
            # Legacy format: separate lists
            result.setdefault('comparable_prices', [])
            result.setdefault('sources', [])
            result['comparable_prices'] = [
                float(p) for p in result['comparable_prices']
                if isinstance(p, (int, float)) and p > 0
            ]
            result['price_source_details'] = []

        result.setdefault('recommended_value', 0)
        result.setdefault('confidence', 'low')
        result.setdefault('reasoning', 'No reasoning provided')
        result.setdefault('search_queries_used', [])

        return result

    def _fallback_result(self, item: ClaimItem, error: str) -> Dict:
        """Create fallback result when research fails"""
        estimated = item.estimated_value or 50.0

        return {
            'comparable_prices': [estimated],
            'sources': ['Estimated value (research failed)'],
            'recommended_value': estimated,
            'confidence': 'low',
            'reasoning': f'Research failed: {error}. Using estimated value.',
            'search_queries_used': []
        }
