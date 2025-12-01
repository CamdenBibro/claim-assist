#!/usr/bin/env python3
"""
Inspect the new eBay s-card structure
"""

from bs4 import BeautifulSoup

print("Loading ebay_response.html...\n")
with open('ebay_response.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all cards
cards = soup.select('ul.srp-results li.s-card')
print(f"✅ Found {len(cards)} s-card elements\n")

if cards:
    print("=" * 80)
    print("FIRST CARD STRUCTURE")
    print("=" * 80)
    
    first_card = cards[0]
    
    # Show full first card HTML (truncated)
    print("\nFull card HTML (first 1000 chars):")
    print("-" * 80)
    print(str(first_card)[:1000])
    print("...\n")
    
    # Try to find title
    print("\n" + "=" * 80)
    print("TITLE SEARCH")
    print("=" * 80)
    
    title_searches = [
        ('span.s-card__title', first_card.find('span', class_='s-card__title')),
        ('div.s-card__title', first_card.find('div', class_='s-card__title')),
        ('h3', first_card.find('h3')),
        ('a[data-testid]', first_card.find('a', attrs={'data-testid': True})),
        ('a', first_card.find('a')),
    ]
    
    for selector, elem in title_searches:
        if elem:
            text = elem.get_text(strip=True)
            print(f"✅ {selector}: {text[:80]}")
            if selector == 'a':
                # Show all text content
                print(f"   Full text: {text}")
        else:
            print(f"❌ {selector}: Not found")
    
    # Try to find price
    print("\n" + "=" * 80)
    print("PRICE SEARCH")
    print("=" * 80)
    
    price_searches = [
        ('span.s-card__price', first_card.find('span', class_='s-card__price')),
        ('div.s-card__price', first_card.find('div', class_='s-card__price')),
        ('span containing $', first_card.find_all('span', string=lambda s: s and '$' in s)),
        ('div containing $', first_card.find_all('div', string=lambda s: s and '$' in s)),
    ]
    
    for selector, elem in price_searches:
        if isinstance(elem, list):
            if elem:
                print(f"✅ {selector}: Found {len(elem)} elements")
                for i, e in enumerate(elem[:3]):
                    print(f"   [{i}] {e.get_text(strip=True)}")
            else:
                print(f"❌ {selector}: Not found")
        else:
            if elem:
                print(f"✅ {selector}: {elem.get_text(strip=True)}")
            else:
                print(f"❌ {selector}: Not found")
    
    # Try to find link
    print("\n" + "=" * 80)
    print("LINK SEARCH")
    print("=" * 80)
    
    link = first_card.find('a')
    if link:
        href = link.get('href', '')
        print(f"✅ First <a> tag href: {href[:120]}...")
        print(f"   data-testid: {link.get('data-testid', 'N/A')}")
        print(f"   class: {link.get('class', 'N/A')}")
    
    # Show all span elements (price is likely in one)
    print("\n" + "=" * 80)
    print("ALL SPAN ELEMENTS (first 10)")
    print("=" * 80)
    
    spans = first_card.find_all('span')
    for i, span in enumerate(spans[:10]):
        text = span.get_text(strip=True)
        classes = span.get('class', [])
        if text:
            print(f"{i}. [{', '.join(classes) if classes else 'no-class'}] {text[:60]}")
    
    # Show all divs with text containing price indicators
    print("\n" + "=" * 80)
    print("ELEMENTS WITH '$' IN TEXT")
    print("=" * 80)
    
    all_elements = first_card.find_all(string=lambda s: s and '$' in s)
    for i, elem in enumerate(all_elements[:10]):
        parent = elem.parent
        print(f"{i}. <{parent.name} class='{parent.get('class', [])}'>")
        print(f"   Text: {elem.strip()}")

print("\n" + "=" * 80)
print("ANALYZING MULTIPLE CARDS")
print("=" * 80)

# Check if pattern is consistent across cards
for i, card in enumerate(cards[:5], 1):
    print(f"\nCard {i}:")
    link = card.find('a')
    if link:
        # Get title from link text
        title = link.get_text(strip=True)
        href = link.get('href', '')
        print(f"   Title: {title[:60]}")
        print(f"   URL: {href[:80]}...")
    
    # Find price
    price_elements = card.find_all(string=lambda s: s and '$' in s)
    if price_elements:
        print(f"   Prices found: {[p.strip() for p in price_elements[:3]]}")

print("\n✅ Analysis complete!")
