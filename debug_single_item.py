#!/usr/bin/env python3
"""
Debug script to test pricing on a single item
Run: python3 debug_single_item.py
""" 

import os
from claim_assist.config import Config
from claim_assist.models.item import ClaimItem
from claim_assist.processors import ClaimProcessor
from claim_assist.utils import create_anthropic_client
from claim_assist.pricing import ItemClassifier, PriceResearcher, PriceValidator


def debug_single_item():
    """Test pricing logic on a single item with detailed output"""

    # Setup configuration
    config = Config.from_env()
    config.validate()

    # Create test item
    test_item = ClaimItem(
        description="Samsung 55-inch 4K TV",
        brand="Samsung",
        condition="good",
        age="3 years",
        features="Smart TV QLED",
        estimated_value=800
    )

    print("="*60)
    print("DEBUGGING SINGLE ITEM")
    print("="*60)
    print(f"Item: {test_item.description}")
    print(f"Brand: {test_item.brand}")
    print(f"Condition: {test_item.condition}")
    print(f"Estimated Value: ${test_item.estimated_value}")
    print("="*60)

    # Initialize components
    client = create_anthropic_client(config)
    classifier = ItemClassifier(client, config.routing_model)
    researcher = PriceResearcher(client, config.simple_research_model, config.complex_research_model)
    validator = PriceValidator(config)

    # Step 1: Classify
    print("\nStep 1: Classifying item complexity...")
    classification = classifier.classify(test_item)
    print(f"Complexity: {classification['complexity']}")
    print(f"Reasoning: {classification['reasoning']}")

    # Step 2: Research prices
    print("\nStep 2: Researching comparable prices...")
    try:
        pricing_data = researcher.research(test_item, classification['complexity'])
        print(f"Found {len(pricing_data['comparable_prices'])} comparable prices")
        print(f"Prices: {pricing_data['comparable_prices']}")
        print(f"Sources: {pricing_data['sources']}")
        print(f"Recommended Value: ${pricing_data['recommended_value']}")
        print(f"Confidence: {pricing_data['confidence']}")
        print(f"Reasoning: {pricing_data['reasoning']}")
    except Exception as e:
        print(f"ERROR during research: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Validate
    print("\nStep 3: Validating pricing...")
    result = validator.validate(test_item, pricing_data)
    print(f"Final Recommended Value: ${result.recommended_value}")
    print(f"75th Percentile: ${result.percentile_75}")
    print(f"Price Range: {result.price_range}")
    print(f"Confidence: {result.confidence}")
    print(f"Needs Review: {result.needs_human_review}")
    print(f"Comparable Count: {result.comparable_count}")
    if result.price_source_details:
        print(f"\nDetailed Price Sources:")
        for detail in result.price_source_details:
            print(f"  - {detail}")

    print("\n" + "="*60)
    print("DEBUG COMPLETE")
    print("="*60)


if __name__ == "__main__":
    debug_single_item()
