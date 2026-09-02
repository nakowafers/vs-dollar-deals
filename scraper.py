import os
import re
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

FIRECRAWL_API_URL = "https://api.firecrawl.dev/v1/scrape"
TARGET_URL = "https://locations.vitaminshoppe.com/"
DEALS_JSON_PATH = Path(__file__).parent / "deals.json"

# JSON Schema for Firecrawl extraction
DEALS_SCHEMA = {
    "type": "object",
    "properties": {
        "has_active_deal": {
            "type": "boolean",
            "description": "True if a $1 or weekend drink promotion is active"
        },
        "deals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "brand": {
                        "type": "string",
                        "description": "Featured brand name (e.g. Jocko GO, C4, Ghost, Ryse)"
                    },
                    "product_name": {
                        "type": "string",
                        "description": "Full product or drink name"
                    },
                    "deal_price": {
                        "type": "string",
                        "description": "Promotional price (e.g. $1 or $2)"
                    },
                    "deal_dates": {
                        "type": "string",
                        "description": "Valid days/dates for promo (e.g. 8/27 – 8/30)"
                    },
                    "limit": {
                        "type": "string",
                        "description": "Quantity limit per customer (e.g. 6 item maximum)"
                    },
                    "details": {
                        "type": "string",
                        "description": "Any additional promo details"
                    },
                    "image_url": {
                        "type": "string",
                        "description": "URL to the product image from the Vitamin Shoppe website"
                    }
                },
                "required": ["brand", "deal_price"]
            }
        }
    },
    "required": ["has_active_deal", "deals"]
}

def direct_scrape_deals() -> dict:
    """Directly scrapes and parses the HTML from locations.vitaminshoppe.com (Fast, $0 Free, Deterministic)."""
    req = urllib.request.Request(
        TARGET_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
    )
    
    with urllib.request.urlopen(req, timeout=10) as response:
        html = response.read().decode("utf-8")

    # Match '$1 Drinks Weekend' section
    # Example: "8/27 – 8/30: Fuel up with Jocko Go Energy drink singles for $1. Plus, $2 Jocko Molk! 6 item maximum."
    promo_match = re.search(
        r"\$1\s*Drinks\s*Weekend.*?(\d{1,2}/\d{1,2}\s*[–-]\s*\d{1,2}/\d{1,2}):\s*([^<\n]+)",
        html,
        re.DOTALL | re.IGNORECASE
    )

    if not promo_match:
        return {
            "has_active_deal": False,
            "updated_at": datetime.now().isoformat(),
            "deals": []
        }

    deal_dates = promo_match.group(1).strip()
    promo_text = promo_match.group(2).strip()

    # Extract limit (e.g. "6 item maximum" or "limit 6")
    limit_match = re.search(r"(\d+\s*(?:item|can)?\s*max(?:imum)?|limit\s*\d+)", promo_text, re.IGNORECASE)
    limit = limit_match.group(1) if limit_match else "Limit 6 per customer"

    # Identify primary $1 brand & product
    # Example: "Fuel up with Jocko Go Energy drink singles for $1"
    primary_brand = "Featured Brand"
    primary_name = "Energy Drink Singles"
    
    brand_match = re.search(r"(?:with|on)\s+([A-Za-z0-9\s]+?)\s+(?:Energy|Drink|RTD)", promo_text, re.IGNORECASE)
    if brand_match:
        primary_brand = brand_match.group(1).strip()
        primary_name = f"{primary_brand} Energy Drink (12oz)"

    # Extract product image URL from promo section
    image_url = None
    # Look for img tags near the promo text
    img_match = re.search(
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]*(?:alt=["\'][^"\']*(?:' + re.escape(primary_brand) + r'|energy|drink)[^"\']*["\'])?[^>]*>',
        html,
        re.IGNORECASE
    )
    if img_match:
        img_src = img_match.group(1)
        # Handle relative URLs
        if img_src.startswith('/'):
            img_src = 'https://locations.vitaminshoppe.com' + img_src
        image_url = img_src

    deals = [
        {
            "brand": primary_brand,
            "product_name": primary_name,
            "deal_price": "$1.00",
            "deal_dates": f"Thursday – Sunday ({deal_dates})",
            "limit": limit,
            "details": promo_text,
            "image_url": image_url
        }
    ]

    # Check companion deal (e.g. "Plus, $2 Jocko Molk!")
    companion_match = re.search(r"(?:Plus,?\s*)?(\$\d+)\s+([A-Za-z0-9\s]+?)(?:!|\.|\,|$)", promo_text, re.IGNORECASE)
    if companion_match:
        price = companion_match.group(1).strip()
        comp_brand = companion_match.group(2).strip()
        if not price.endswith(".00") and price == "$2":
            price = "$2.00"
        deals.append({
            "brand": comp_brand,
            "product_name": f"{comp_brand} RTD",
            "deal_price": price,
            "deal_dates": f"Thursday – Sunday ({deal_dates})",
            "limit": limit,
            "details": "Companion deal",
            "image_url": None
        })

    return {
        "has_active_deal": True,
        "updated_at": datetime.now().isoformat(),
        "deals": deals
    }

def firecrawl_scrape_deals(api_key: str) -> dict:
    """Scrapes via Firecrawl v1 API with JSON schema extraction."""
    payload = {
        "url": TARGET_URL,
        "formats": ["json"],
        "jsonOptions": {
            "schema": DEALS_SCHEMA,
            "prompt": (
                "Extract the '$1 Drinks Weekend' promotion from this page, including the dates, "
                "the featured $1 energy drink brand name, the deal price, the limit, and any $2 companion deals."
            )
        },
        "location": {
            "country": "US",
            "languages": ["en-US"]
        }
    }

    req = urllib.request.Request(
        FIRECRAWL_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        data_block = res_data.get("data") or {}
        extracted = data_block.get("json") or data_block.get("extract") or data_block.get("llm_extraction") or {}
        extracted["updated_at"] = datetime.now().isoformat()
        return extracted

def scrape_weekly_deals() -> dict:
    api_key = os.getenv("FIRECRAWL_API_KEY")

    if api_key:
        print(f"Scraping {TARGET_URL} via Firecrawl API...")
        try:
            deals_data = firecrawl_scrape_deals(api_key)
            if deals_data and deals_data.get("deals"):
                with open(DEALS_JSON_PATH, "w") as f:
                    json.dump(deals_data, f, indent=2)
                print("Successfully updated deals.json via Firecrawl:")
                print(json.dumps(deals_data, indent=2))
                return deals_data
            else:
                print("Firecrawl returned empty deals array, falling back to direct parse...")
        except Exception as e:
            print(f"Firecrawl API error ({e}), falling back to direct parse...")

    # Direct parse (Default & High-reliability Fallback)
    print(f"Scraping {TARGET_URL} directly (Zero Anti-Bot / Fast)...")
    deals_data = direct_scrape_deals()
    
    with open(DEALS_JSON_PATH, "w") as f:
        json.dump(deals_data, f, indent=2)

    print("Successfully updated deals.json:")
    print(json.dumps(deals_data, indent=2))
    return deals_data

if __name__ == "__main__":
    scrape_weekly_deals()
