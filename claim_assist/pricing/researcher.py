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
        search_prompt = f"""You are an insurance claim adjuster evaluating replacement costs. Use web search to find VALID comparable prices.

        ITEM TO PRICE:
        - Description: {item.description}
        - Brand: {item.brand or 'unbranded'}
        - Condition: {item.condition or 'used'}
        - Age/Year: {item.age or 'unknown'}
        - Estimated Value: ${item.estimated_value or 'unknown'}

        SEARCH STRATEGY:
        1. Search ONLY eBay and Facebook Marketplace for items matching this description
        2. For EACH listing found, evaluate if it's a valid comparable
        3. REJECT listings that are:
        - Refurbished, renewed, or certified pre-owned
        - From auctions (only final sale/Buy It Now prices)
        - Significantly different condition than the original item
        - Different model/generation/variant
        - Bundle deals or parts-only listings
        - More than 5 years different in age (if age is known)
        - Priced as extreme outliers (>3x or <0.3x median)
        4. ACCEPT only listings that match condition, model, and age reasonably

        IMPORTANT: Include ONLY valid comparable prices. If fewer than 3 valid comparables found, note this in reasoning.

        Return ONLY this exact JSON format with NO additional text:
        {{
        "price_sources":[
        {{"source":"eBay - [exact item title]","price":number,"condition":"used/new","notes":"brief validation note"}},
        ...
        ],
        "comparable_count":number_of_valid_items_found,
        "total_listings_evaluated":total_number_checked,
        "recommended_value":calculated_value,
        "confidence":"low|medium|high",
        "reasoning":"Explain: How many comparables found? Why were some rejected? How did you calculate recommended_value? Any data quality concerns?",
        "search_queries_used":["query 1","query 2",...]
        }}

        CONFIDENCE SCORING:
        - high: 5+ valid comparables, tight price clustering, good condition match
        - medium: 3-4 comparables OR some condition variance OR moderate price spread
        - low: <3 comparables OR high variance OR poor condition match OR search failed

        Rules:
        - NO markdown formatting
        - NO explanatory text outside JSON
        - Use double quotes for strings
        - Numbers must not be quoted (use raw numbers like 650, not "650")
        - Include condition and notes for each price source
        - recommended_value should be median of valid comparables (or mean if <5 items)
        - If no valid comparables, use estimated_value with "low" confidence"""

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
                if isinstance(item, dict) and 'price' in item and item['price'] is not None and item['price'] > 0
            ]
            result['sources'] = [
                item['source'] for item in price_sources
                if isinstance(item, dict) and 'source' in item
            ]
            # Store the structured data for detailed output
            result['price_source_details'] = [
                f"{item['source']}: ${float(item['price']):.2f}"
                for item in price_sources
                if isinstance(item, dict) and 'source' in item and 'price' in item and item['price'] is not None
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
