import json
from typing import Dict
from ..models.item import ClaimItem, Complexity
from ..utils.local_inference import LocalInferenceClient


class ItemClassifier:
    """Classifies items by pricing complexity to route to appropriate pricing strategy"""

    def __init__(self, inference_client: LocalInferenceClient):
        self.client = inference_client

    def classify(self, item: ClaimItem) -> Dict[str, str]:
        """
        Classify item complexity for pricing strategy routing

        Args:
            item: ClaimItem to classify

        Returns:
            Dict with 'complexity' (simple|moderate|complex) and 'reasoning'
        """
        item_dict = item.to_dict()

        prompt = f"""Classify this damaged item's pricing complexity for insurance claim valuation.

Item: {item_dict['description']}
Brand: {item_dict.get('brand', 'unknown')}
Condition: {item_dict.get('condition', 'unknown')}
Age: {item_dict.get('age', 'unknown')}

Respond with ONLY valid JSON in this exact format:
{{"complexity": "simple|moderate|complex", "reasoning": "brief explanation"}}

Classification guidelines:
- Simple: Clear brand/model, readily available new, mass-produced consumer goods (electronics, appliances, furniture from major brands)
- Moderate: Generic items with available used market, common items without specific brand, standard household items
- Complex: Vintage items, custom-made items, rare collectibles, antiques, one-of-a-kind pieces requiring specialized knowledge

Examples:
- "Samsung 55-inch TV" = simple (clear brand, readily available)
- "Leather armchair" = moderate (generic furniture, used market exists) 
- "1950s vintage oak dining table" = complex (vintage, requires specialized knowledge)

Return only the JSON response, no other text."""

        try:
            response = self.client.generate(prompt, max_tokens=200, temperature=0.1)
            
            if not response.success:
                raise Exception(response.error)
            
            # Parse JSON response
            result = json.loads(response.content.strip())

            # Validate complexity value
            valid_complexities = [c.value for c in Complexity]
            if result.get('complexity') not in valid_complexities:
                result['complexity'] = Complexity.MODERATE.value

            return result

        except (json.JSONDecodeError, KeyError, Exception) as e:
            # Fallback to moderate complexity if classification fails
            return {
                "complexity": Complexity.MODERATE.value,
                "reasoning": f"Classification error, defaulting to moderate: {str(e)}"
            }
