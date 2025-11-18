import statistics
from typing import Dict, List
from ..models.item import ClaimItem, PricingResult, Confidence
from ..config import Config


class PriceValidator:
    """Validates pricing research and applies insurance industry standards"""

    def __init__(self, config: Config):
        self.config = config

    def validate(self, item: ClaimItem, pricing_data: Dict) -> PricingResult:
        """
        Validate pricing research and create final result

        Args:
            item: ClaimItem being priced
            pricing_data: Research data from PriceResearcher

        Returns:
            PricingResult with validated pricing and metadata
        """
        prices = pricing_data.get('comparable_prices', [])

        # Determine confidence based on number of comparables and research confidence
        confidence = self._determine_confidence(prices, pricing_data.get('confidence', 'low'))

        # Calculate statistical values
        percentile_75 = None
        median_price = None
        outlier = False

        if len(prices) >= 2:
            sorted_prices = sorted(prices)
            percentile_75 = sorted_prices[int(len(sorted_prices) * self.config.percentile_value)]
            median_price = statistics.median(prices)

            # Flag outliers - if recommended value deviates significantly from median
            recommended = pricing_data.get('recommended_value', 0)
            if median_price > 0:
                deviation = abs(recommended - median_price) / median_price
                outlier = deviation > self.config.outlier_threshold
        elif len(prices) == 1:
            percentile_75 = prices[0]
            outlier = True  # Single data point is always uncertain
        else:
            # No comparable prices found
            percentile_75 = pricing_data.get('recommended_value', 0)
            outlier = True

        # Determine if human review is needed
        needs_human_review = (
            outlier or
            confidence == Confidence.LOW.value or
            len(prices) < self.config.low_confidence_threshold
        )

        # Format price range
        price_range = "N/A"
        if prices:
            price_range = f"${min(prices):.2f} - ${max(prices):.2f}"

        return PricingResult(
            item=item.description,
            recommended_value=pricing_data.get('recommended_value', 0),
            percentile_75=percentile_75,
            price_range=price_range,
            confidence=confidence,
            needs_human_review=needs_human_review,
            reasoning=pricing_data.get('reasoning', 'No reasoning provided'),
            comparable_count=len(prices),
            sources=pricing_data.get('sources', []),
            search_queries_used=pricing_data.get('search_queries_used', []),
            price_source_details=pricing_data.get('price_source_details', [])
        )

    def _determine_confidence(self, prices: List[float], research_confidence: str) -> str:
        """
        Determine overall confidence level

        Args:
            prices: List of comparable prices found
            research_confidence: Confidence from research phase

        Returns:
            Confidence level (high|medium|low)
        """
        if len(prices) < self.config.low_confidence_threshold:
            return Confidence.LOW.value
        elif (research_confidence == Confidence.HIGH.value and
              len(prices) >= self.config.high_confidence_threshold):
            return Confidence.HIGH.value
        else:
            return Confidence.MEDIUM.value
