import json
from typing import Dict
import anthropic
from ..models.item import ClaimItem, Complexity


class ItemClassifier:
    """Classifies items by pricing complexity to route to appropriate pricing strategy"""

    def __init__(self, client: anthropic.Anthropic, model: str = "claude-3-5-haiku-latest"):
        self.client = client
        self.model = model

    def classify(self, item: ClaimItem) -> Dict[str, str]:
        """
        Classify item complexity for pricing strategy routing

        Args:
            item: ClaimItem to classify

        Returns:
            Dict with 'complexity' (simple|moderate|complex) and 'reasoning'
        """
        item_dict = item.to_dict()

        prompt = f"""Classify this damaged item's pricing complexity:

Item: {item_dict['description']}
Brand: {item_dict.get('brand', 'unknown')}
Condition: {item_dict.get('condition', 'unknown')}

Respond with JSON:
{{"complexity": "simple|moderate|complex", "reasoning": "brief explanation"}}

Simple: Clear brand/model, readily available new
Moderate: Generic item, available used market
Complex: Vintage, custom, or rare items needing deep research"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            result = json.loads(message.content[0].text)

            # Validate complexity value
            if result['complexity'] not in [c.value for c in Complexity]:
                result['complexity'] = Complexity.MODERATE.value

            return result

        except (json.JSONDecodeError, KeyError, anthropic.APIError) as e:
            # Fallback to moderate complexity if classification fails
            return {
                "complexity": Complexity.MODERATE.value,
                "reasoning": f"Classification error, defaulting to moderate: {str(e)}"
            }
