import pandas as pd
from typing import List
from ..models.item import ClaimItem, PricingResult, Condition
from ..pricing import ItemClassifier, PriceResearcher, PriceValidator
from ..utils import ItemCache, create_anthropic_client
from ..config import Config


class ClaimProcessor:
    """Processes insurance claims with LLM-powered pricing research"""

    def __init__(self, config: Config):
        """
        Initialize claim processor

        Args:
            config: Application configuration
        """
        self.config = config
        self.client = create_anthropic_client(config)

        # Initialize pricing components
        self.classifier = ItemClassifier(self.client, config.routing_model)
        self.researcher = PriceResearcher(
            self.client,
            config.simple_research_model,
            config.complex_research_model
        )
        self.validator = PriceValidator(config)

        # Initialize cache
        self.cache = ItemCache(config.cache_ttl) if config.enable_cache else None
        self.results: List[PricingResult] = []

    def process_spreadsheet(self, csv_path: str) -> pd.DataFrame:
        """
        Process entire claim spreadsheet

        Args:
            csv_path: Path to CSV file with claim items

        Returns:
            DataFrame with pricing results

        Expected CSV columns:
            - description (required)
            - brand (optional)
            - condition (optional)
            - age (optional)
            - features (optional)
            - estimated_value (optional)
        """
        df = pd.read_csv(csv_path)

        # Validate required columns
        if 'description' not in df.columns:
            raise ValueError("CSV must contain 'description' column")

        results = []
        total_items = len(df)

        print(f"Processing {total_items} items...")

        for idx, row in df.iterrows():
            item = self._row_to_claim_item(row)
            result = self.process_item(item)
            results.append(result)

            # Progress tracking
            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1}/{total_items} items")

        print(f"Completed processing all {total_items} items")

        self.results = results
        # Convert to dict for DataFrame
        results_dict = [r.to_dict() for r in results]
        return pd.DataFrame(results_dict)

    def process_item(self, item: ClaimItem) -> PricingResult:
        """
        Process single claim item

        Args:
            item: ClaimItem to process

        Returns:
            PricingResult with valuation
        """
        # Check cache first
        if self.cache:
            cached_result = self.cache.get(item)
            if cached_result:
                return cached_result

        # Decide pricing strategy based on estimated value
        estimated_value = item.estimated_value or 1000

        if estimated_value < self.config.value_threshold:
            # Use simple heuristic for low-value items
            result = self._simple_pricing(item)
        else:
            # Full LLM research for high-value items
            classification = self.classifier.classify(item)
            pricing_data = self.researcher.research(item, classification['complexity'])
            result = self.validator.validate(item, pricing_data)

        # Cache result
        if self.cache:
            self.cache.set(item, result)

        return result

    def _simple_pricing(self, item: ClaimItem) -> PricingResult:
        """
        Fast heuristic pricing for low-value items

        Args:
            item: ClaimItem to price

        Returns:
            PricingResult with simple depreciation calculation
        """
        base_value = item.estimated_value or 50.0

        # Condition-based depreciation multipliers
        condition_multiplier = {
            Condition.NEW.value: 1.0,
            Condition.EXCELLENT.value: 0.85,
            Condition.GOOD.value: 0.65,
            Condition.FAIR.value: 0.45,
            Condition.POOR.value: 0.25
        }

        multiplier = condition_multiplier.get(
            (item.condition or 'good').lower(),
            0.65  # Default to 'good'
        )

        recommended_value = base_value * multiplier

        return PricingResult(
            item=item.description,
            recommended_value=recommended_value,
            confidence="medium",
            needs_human_review=False,
            reasoning="Simple depreciation heuristic for low-value item",
            comparable_count=0
        )

    def _row_to_claim_item(self, row: pd.Series) -> ClaimItem:
        """Convert DataFrame row to ClaimItem"""
        return ClaimItem(
            description=row.get('description', ''),
            brand=row.get('brand') if pd.notna(row.get('brand')) else None,
            condition=row.get('condition') if pd.notna(row.get('condition')) else None,
            age=row.get('age') if pd.notna(row.get('age')) else None,
            features=row.get('features') if pd.notna(row.get('features')) else None,
            estimated_value=float(row.get('estimated_value', 0)) if pd.notna(row.get('estimated_value')) else None
        )

    def get_summary(self) -> dict:
        """
        Get summary statistics for processed claims

        Returns:
            Dict with summary statistics
        """
        if not self.results:
            return {
                "total_items": 0,
                "auto_approved": 0,
                "needs_review": 0,
                "total_value": 0.0,
                "auto_approved_value": 0.0,
                "review_value": 0.0
            }

        auto_approved = [r for r in self.results if not r.needs_human_review]
        needs_review = [r for r in self.results if r.needs_human_review]

        return {
            "total_items": len(self.results),
            "auto_approved": len(auto_approved),
            "needs_review": len(needs_review),
            "total_value": sum(r.recommended_value for r in self.results),
            "auto_approved_value": sum(r.recommended_value for r in auto_approved),
            "review_value": sum(r.recommended_value for r in needs_review)
        }

    def export_results(self, output_path: str, review_path: str) -> None:
        """
        Export results to CSV files

        Args:
            output_path: Path for complete results
            review_path: Path for items needing review
        """
        if not self.results:
            print("No results to export")
            return

        # Export all results
        df = pd.DataFrame([r.to_dict() for r in self.results])
        df.to_csv(output_path, index=False)
        print(f"Exported all results to {output_path}")

        # Export items needing review
        review_items = [r.to_dict() for r in self.results if r.needs_human_review]
        if review_items:
            review_df = pd.DataFrame(review_items)
            review_df.to_csv(review_path, index=False)
            print(f"Exported {len(review_items)} items for review to {review_path}")
