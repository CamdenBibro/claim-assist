#!/usr/bin/env python3
"""
Inspect eBay HTML to understand current structure
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode

# Setup
query = "Samsung 55 inch 4K TV"
params = {
    '_nkw': query,
    '_sacat': '0',
    'LH_Sold': '1',
    'LH_Complete': '1',
    '_sop': '13',
    '_ipg': '50',
}

url = f"https://www.ebay.com/sch/i.html?{urlencode(params)}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print(f"🔍 Fetching: {url}\n")

response = requests.get(url, headers=headers, timeout=10)
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.content):,} bytes\n")

# Save HTML for inspection
with open('ebay_response.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("✅ Saved HTML to ebay_response.html\n")

# Parse with BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

print("=" * 80)
print("SEARCHING FOR ITEM CONTAINERS")
print("=" * 80)

# Try different selectors
selectors_to_try = [
    ('div.s-item', soup.find_all('div', class_='s-item')),
    ('div.srp-results', soup.find_all('div', class_='srp-results')),
    ('li.s-item', soup.find_all('li', class_='s-item')),
    ('div[data-view]', soup.find_all('div', attrs={'data-view': True})),
    ('ul.srp-results li', soup.select('ul.srp-results li')),
]

for selector, elements in selectors_to_try:
    print(f"\n{selector}: Found {len(elements)} elements")
    if elements and len(elements) > 0:
        print(f"   First element classes: {elements[0].get('class', [])}")
        print(f"   First element snippet: {str(elements[0])[:200]}...")

# Look at the main results container
print("\n" + "=" * 80)
print("MAIN RESULTS CONTAINER")
print("=" * 80)

results_container = soup.find('div', class_='srp-river-results')
if results_container:
    print("✅ Found .srp-river-results container")
    items = results_container.find_all('li', class_='s-item')
    print(f"   Contains {len(items)} <li class='s-item'> elements")
else:
    print("❌ No .srp-river-results found")

# Alternative: ul.srp-results
results_ul = soup.find('ul', class_='srp-results')
if results_ul:
    print("✅ Found <ul class='srp-results'>")
    items = results_ul.find_all('li')
    print(f"   Contains {len(items)} <li> elements")
    if items:
        first_item = items[0] if len(items) > 0 else None
        if first_item:
            print(f"\n   First item classes: {first_item.get('class', [])}")
            
            # Look for title
            title_selectors = [
                ('h3.s-item__title', first_item.find('h3', class_='s-item__title')),
                ('div.s-item__title', first_item.find('div', class_='s-item__title')),
                ('span.s-item__title', first_item.find('span', class_='s-item__title')),
                ('a .s-item__title', first_item.select_one('a .s-item__title')),
            ]
            
            print("\n   Title element search:")
            for sel, elem in title_selectors:
                if elem:
                    print(f"      ✅ {sel}: {elem.get_text(strip=True)[:60]}")
                else:
                    print(f"      ❌ {sel}: Not found")
            
            # Look for price
            price_selectors = [
                ('span.s-item__price', first_item.find('span', class_='s-item__price')),
                ('span.s-item__price s-item__price--primary', first_item.find('span', class_='s-item__price--primary')),
                ('.s-item__price', first_item.select_one('.s-item__price')),
            ]
            
            print("\n   Price element search:")
            for sel, elem in price_selectors:
                if elem:
                    print(f"      ✅ {sel}: {elem.get_text(strip=True)}")
                else:
                    print(f"      ❌ {sel}: Not found")
            
            # Look for link
            link_selectors = [
                ('a.s-item__link', first_item.find('a', class_='s-item__link')),
                ('a', first_item.find('a')),
            ]
            
            print("\n   Link element search:")
            for sel, elem in link_selectors:
                if elem:
                    href = elem.get('href', '')
                    print(f"      ✅ {sel}: {href[:80]}...")
                else:
                    print(f"      ❌ {sel}: Not found")

else:
    print("❌ No <ul class='srp-results'> found")

print("\n" + "=" * 80)
print("✅ Inspection complete! Check ebay_response.html for full HTML")
print("=" * 80)
