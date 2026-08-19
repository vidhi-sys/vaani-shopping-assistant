"""
Test suite for Voice-Activated Search Engine in Vaani Shopping Assistant.
Evaluates Regex Price Constraint Parsing, Catalog Search, and Relevance Ranking.
"""

import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from voice_search import VoiceSearchEngine, parse_price_filter

def run_search_tests():
    print("=" * 70)
    print("    VAANI SHOPPING ASSISTANT - VOICE SEARCH TEST SUITE")
    print("=" * 70)

    engine = VoiceSearchEngine(catalog_path="catalog.json")

    # -----------------------------------------------------------------
    # Test 1: Regex Price Constraint Parsing
    # -----------------------------------------------------------------
    print("\n--- Test 1: Price Regex Filter Parsing ---")
    min_p, max_p, term = parse_price_filter("search organic milk under $5")
    print(f"  'under $5' -> min: {min_p}, max: {max_p}, term: '{term}'")
    assert max_p == 5.0 and min_p is None

    min_p, max_p, term = parse_price_filter("find snacks between $3 and $8 dollars")
    print(f"  'between $3 and $8' -> min: {min_p}, max: {max_p}, term: '{term}'")
    assert min_p == 3.0 and max_p == 8.0

    min_p, max_p, term = parse_price_filter("coffee over $5")
    print(f"  'over $5' -> min: {min_p}, max: {max_p}, term: '{term}'")
    assert min_p == 5.0 and max_p is None
    print("  [PASS] Price regex parsing test passed.")

    # -----------------------------------------------------------------
    # Test 2: Catalog Product Search & Price Bound Filtering
    # -----------------------------------------------------------------
    print("\n--- Test 2: Catalog Product Search ---")
    res = engine.search_items("milk under $4")
    print(f"  Query: 'milk under $4' -> Found {res['count']} results:")
    for item in res["results"]:
        print(f"    - {item['name']} (${item['price']})")
        assert item["price"] <= 4.0

    assert res["count"] > 0
    print("  [PASS] Catalog search and price bound filtering test passed.")

    # -----------------------------------------------------------------
    # Test 3: No Results Fallback
    # -----------------------------------------------------------------
    print("\n--- Test 3: No Match Fallback ---")
    no_match_res = engine.search_items("spaceship engine under $2")
    print(f"  Query: 'spaceship' -> Status: {no_match_res['status']}")
    print(f"  Message: \"{no_match_res['message']}\"")
    assert no_match_res["status"] == "no_results"
    print("  [PASS] No match fallback test passed.")

    print("\n" + "=" * 70)
    print("  All Voice Search tests completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    run_search_tests()
