#!/usr/bin/env python3
"""
Debug script with detailed API response logging
"""

import os
import json
from claim_assist.config import Config
from claim_assist.models.item import ClaimItem
from claim_assist.utils import create_anthropic_client


def debug_api_response():
    """Test API call and see raw response"""

    config = Config.from_env()
    config.validate()
    client = create_anthropic_client(config)

    test_item = ClaimItem(
        description="Samsung 55-inch 4K TV",
        brand="Samsung",
        condition="good",
        age="3 years",
        features="Smart TV QLED",
        estimated_value=800
    )

    prompt = f"""You are an insurance claim adjuster researching replacement costs. Use web search to find real comparable prices.

ITEM DETAILS:
- Description: {test_item.description}
- Brand: {test_item.brand}
- Condition: {test_item.condition}

Return ONLY a valid JSON object:
{{
    "comparable_prices": [800, 850, 780, 820, 795],
    "sources": ["eBay", "Amazon", "Best Buy"],
    "recommended_value": 810,
    "confidence": "high",
    "reasoning": "Multiple recent sales found",
    "search_queries_used": ["Samsung 55 inch 4K TV used"]
}}"""

    print("="*60)
    print("SENDING REQUEST TO API")
    print("="*60)
    print(f"Model: claude-3-5-haiku-latest")
    print(f"Prompt length: {len(prompt)} chars")
    print("\n" + "-"*60)
    print("PROMPT:")
    print("-"*60)
    print(prompt)
    print("-"*60)

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5
            }]
        )

        print("\n" + "="*60)
        print("RAW API RESPONSE")
        print("="*60)
        print(f"ID: {response.id}")
        print(f"Model: {response.model}")
        print(f"Stop Reason: {response.stop_reason}")
        print(f"Usage: {response.usage}")
        print("\nContent blocks:")

        for i, block in enumerate(response.content):
            print(f"\n--- Block {i} (type: {block.type}) ---")
            if block.type == "text":
                print(f"Text: {block.text}")
            elif block.type == "tool_use":
                print(f"Tool: {block.name}")
                print(f"Input: {block.input}")

        # Try to extract and parse JSON
        print("\n" + "="*60)
        print("PARSING JSON")
        print("="*60)

        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content += block.text

        print(f"Extracted text: {text_content}")

        if text_content:
            try:
                parsed = json.loads(text_content)
                print("\nSuccessfully parsed JSON:")
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError as e:
                print(f"\nFailed to parse JSON: {e}")
                print(f"Raw text was: {repr(text_content)}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_api_response()
