import argparse
import sys

import httpx

# ---------------------------------------------------------------------------
# Sample product catalogue
# ---------------------------------------------------------------------------

PRODUCTS: list[dict] = [
    {
        "text": "Wireless Noise-Cancelling Headphones. Premium over-ear headphones with active noise cancellation, 30-hour battery life, and foldable design. Compatible with Bluetooth 5.0 devices.",
        "metadata": {
            "name": "Wireless Noise-Cancelling Headphones",
            "category": "Electronics",
            "price": 149.99,
            "brand": "SoundPro",
            "in_stock": True,
            "rating": 4.7,
        },
    },
    {
        "text": "Ergonomic Office Chair. Adjustable lumbar support, breathable mesh back, 360-degree swivel, and padded armrests. Supports up to 150 kg.",
        "metadata": {
            "name": "Ergonomic Office Chair",
            "category": "Furniture",
            "price": 299.00,
            "brand": "ComfortDesk",
            "in_stock": True,
            "rating": 4.5,
        },
    },
    {
        "text": "Stainless Steel Water Bottle 1L. Double-wall vacuum insulation keeps drinks cold for 24 hours or hot for 12 hours. BPA-free, leak-proof lid.",
        "metadata": {
            "name": "Stainless Steel Water Bottle 1L",
            "category": "Sports & Outdoors",
            "price": 34.95,
            "brand": "HydroFlow",
            "in_stock": True,
            "rating": 4.8,
        },
    },
    {
        "text": "Running Shoes Men's. Lightweight mesh upper with cushioned midsole and anti-slip rubber outsole. Available in sizes 40-47.",
        "metadata": {
            "name": "Running Shoes Men's",
            "category": "Footwear",
            "price": 89.99,
            "brand": "SwiftStep",
            "in_stock": True,
            "rating": 4.4,
        },
    },
    {
        "text": "Mechanical Keyboard TKL. Tenkeyless layout with Cherry MX Red switches, per-key RGB backlight, and USB-C detachable cable. Anti-ghosting N-key rollover.",
        "metadata": {
            "name": "Mechanical Keyboard TKL",
            "category": "Electronics",
            "price": 119.00,
            "brand": "KeyForge",
            "in_stock": True,
            "rating": 4.6,
        },
    },
    {
        "text": "Yoga Mat Non-Slip 6mm. Eco-friendly TPE material, extra-wide 183x61 cm, moisture-resistant surface with alignment lines.",
        "metadata": {
            "name": "Yoga Mat Non-Slip 6mm",
            "category": "Sports & Outdoors",
            "price": 29.95,
            "brand": "ZenFlow",
            "in_stock": True,
            "rating": 4.3,
        },
    },
    {
        "text": "Smart Watch Fitness Tracker. Heart rate monitor, sleep tracking, GPS, 50m water resistance, 7-day battery, compatible with iOS and Android.",
        "metadata": {
            "name": "Smart Watch Fitness Tracker",
            "category": "Electronics",
            "price": 199.00,
            "brand": "PulseTrack",
            "in_stock": False,
            "rating": 4.5,
        },
    },
    {
        "text": "Coffee Grinder Electric Burr. 18 adjustable grind settings from espresso to French press. Stainless steel conical burr, 200g bean hopper, quiet motor.",
        "metadata": {
            "name": "Coffee Grinder Electric Burr",
            "category": "Kitchen",
            "price": 79.99,
            "brand": "BrewMaster",
            "in_stock": True,
            "rating": 4.7,
        },
    },
    {
        "text": "LED Desk Lamp USB-C. Adjustable colour temperature (2700–6500 K), 5 brightness levels, built-in USB-A charging port, touch controls, and memory function.",
        "metadata": {
            "name": "LED Desk Lamp USB-C",
            "category": "Home & Office",
            "price": 44.99,
            "brand": "LumaLight",
            "in_stock": True,
            "rating": 4.4,
        },
    },
    {
        "text": "Backpack Laptop 15.6-inch. Water-resistant 30L daypack with padded laptop compartment, USB charging port, anti-theft pocket, and ergonomic shoulder straps.",
        "metadata": {
            "name": "Backpack Laptop 15.6-inch",
            "category": "Bags & Accessories",
            "price": 59.99,
            "brand": "TrekGear",
            "in_stock": True,
            "rating": 4.6,
        },
    },
    {
        "text": "Cast Iron Skillet 26cm. Pre-seasoned with flaxseed oil, suitable for all hob types including induction. Oven-safe up to 260°C, includes silicone handle cover.",
        "metadata": {
            "name": "Cast Iron Skillet 26cm",
            "category": "Kitchen",
            "price": 49.95,
            "brand": "IronChef",
            "in_stock": True,
            "rating": 4.9,
        },
    },
    {
        "text": "Wireless Charging Pad 15W. Qi-certified fast charger compatible with iPhone, Samsung Galaxy, and all Qi-enabled devices. LED indicator, anti-slip base.",
        "metadata": {
            "name": "Wireless Charging Pad 15W",
            "category": "Electronics",
            "price": 24.99,
            "brand": "ChargeFast",
            "in_stock": True,
            "rating": 4.2,
        },
    },
    {
        "text": "Bamboo Cutting Board Set of 3. Eco-friendly bamboo, juice groove, easy-grip handles. Dishwasher-safe. Sizes: small, medium, large.",
        "metadata": {
            "name": "Bamboo Cutting Board Set of 3",
            "category": "Kitchen",
            "price": 27.50,
            "brand": "GreenChop",
            "in_stock": True,
            "rating": 4.5,
        },
    },
    {
        "text": "Resistance Bands Set 5-piece. Latex loop bands with resistance levels from 10 to 50 lbs. Includes carry bag and exercise guide.",
        "metadata": {
            "name": "Resistance Bands Set 5-piece",
            "category": "Sports & Outdoors",
            "price": 19.99,
            "brand": "FlexBand",
            "in_stock": True,
            "rating": 4.3,
        },
    },
    {
        "text": "Portable Bluetooth Speaker Waterproof. 360° surround sound, IPX7 waterproof, 20-hour playtime, built-in mic, TWS stereo pairing.",
        "metadata": {
            "name": "Portable Bluetooth Speaker Waterproof",
            "category": "Electronics",
            "price": 69.99,
            "brand": "BoomWave",
            "in_stock": True,
            "rating": 4.6,
        },
    },
    {
        "text": "Linen Duvet Cover King Size. 100% washed linen, breathable and hypoallergenic. Button closure, includes two pillowcases. Machine washable.",
        "metadata": {
            "name": "Linen Duvet Cover King Size",
            "category": "Bedding",
            "price": 89.00,
            "brand": "SlumberCraft",
            "in_stock": True,
            "rating": 4.7,
        },
    },
    {
        "text": "Standing Desk Converter. Height-adjustable sit-stand workstation, dual monitor support, holds up to 15 kg, smooth gas-spring lift mechanism.",
        "metadata": {
            "name": "Standing Desk Converter",
            "category": "Furniture",
            "price": 179.00,
            "brand": "UpDesk",
            "in_stock": False,
            "rating": 4.4,
        },
    },
    {
        "text": "Travel Neck Pillow Memory Foam. Ergonomic U-shape, washable velvet cover, snap closure, compact roll-up design for carry-on bags.",
        "metadata": {
            "name": "Travel Neck Pillow Memory Foam",
            "category": "Travel",
            "price": 22.00,
            "brand": "JetRest",
            "in_stock": True,
            "rating": 4.2,
        },
    },
    {
        "text": "Stainless Steel Cookware Set 10-piece. Tri-ply construction, oven-safe to 230°C, induction compatible, dishwasher-safe, riveted handles.",
        "metadata": {
            "name": "Stainless Steel Cookware Set 10-piece",
            "category": "Kitchen",
            "price": 229.99,
            "brand": "ChefClad",
            "in_stock": True,
            "rating": 4.8,
        },
    },
    {
        "text": "Men's Merino Wool Crew Neck Sweater. 100% extra-fine merino wool, temperature-regulating, itch-free, available in 8 colours and sizes S–XXL.",
        "metadata": {
            "name": "Men's Merino Wool Crew Neck Sweater",
            "category": "Clothing",
            "price": 79.00,
            "brand": "WoolWorks",
            "in_stock": True,
            "rating": 4.6,
        },
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the database with sample e-commerce products.")
    parser.add_argument("--collection", default="ecommerce_products", help="Collection name (default: ecommerce_products)")
    parser.add_argument("--model", default="BAAI/bge-m3", help="Embedding model the collection should use (default: BAAI/bge-m3)")
    parser.add_argument("--url", default="http://localhost:7530", help="Base URL of the running Cognitor instance (default: http://localhost:7530)")
    parser.add_argument("--api-key", default=None, help="X-API-Key header value (required when MULTI_TENANT is enabled)")
    parser.add_argument("--force", action="store_true", help="Delete and recreate the collection if it already exists")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    headers = {"X-API-Key": args.api_key} if args.api_key else {}

    with httpx.Client(base_url=base_url, headers=headers, timeout=120.0) as client:
        if args.force:
            resp = client.delete(f"/collections/{args.collection}")
            if resp.status_code not in (204, 404):
                print(f"Failed to delete collection: {resp.status_code} {resp.text}")
                sys.exit(1)
            if resp.status_code == 204:
                print(f"--force: deleted existing collection '{args.collection}'")

        print(f"Creating collection '{args.collection}' …")
        resp = client.post("/collections", json={"name": args.collection, "emb_model": args.model})
        if resp.status_code == 409:
            print(
                f"Collection '{args.collection}' already exists. "
                "Use --force to drop and recreate it."
            )
            sys.exit(1)
        if resp.status_code != 201:
            print(f"Failed to create collection: {resp.status_code} {resp.text}")
            sys.exit(1)

        texts = [p["text"] for p in PRODUCTS]
        metadatas = [p["metadata"] for p in PRODUCTS]

        print(f"Adding {len(PRODUCTS)} products (server will embed using '{args.model}') …")
        resp = client.post(
            f"/collections/{args.collection}/documents",
            json={"texts": texts, "metadatas": metadatas},
        )
        if resp.status_code != 201:
            print(f"Failed to add documents: {resp.status_code} {resp.text}")
            sys.exit(1)

        ids = resp.json()["ids"]
        print(f"Done. Added {len(ids)} documents to '{args.collection}'.")


if __name__ == "__main__":
    main()
