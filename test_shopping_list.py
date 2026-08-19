"""
Test suite for Shopping List Management module in Vaani Shopping Assistant.
Evaluates Item Addition, Quantity Incrementing, Fuzzy Removal, and Auto-Categorization.
"""

import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from shopping_list import ShoppingListManager, auto_categorize, parse_quantity

def run_shopping_list_tests():
    print("=" * 70)
    print("   VAANI SHOPPING ASSISTANT - SHOPPING LIST MANAGER TEST SUITE")
    print("=" * 70)

    manager = ShoppingListManager()

    # -----------------------------------------------------------------
    # Test 1: Auto-Categorization & Quantity Parsing
    # -----------------------------------------------------------------
    print("\n--- Test 1: Auto-Categorization & Quantity Parsing ---")
    assert auto_categorize("whole milk") == "dairy"
    assert auto_categorize("fresh apples") == "produce"
    assert auto_categorize("sourdough bread") == "bakery"
    assert auto_categorize("cold coffee") == "beverages"
    assert auto_categorize("potato chips") == "snacks"
    assert auto_categorize("dish soap") == "household"
    assert auto_categorize("random widget") == "other"

    assert parse_quantity("2") == 2
    assert parse_quantity("two") == 2
    assert parse_quantity("a couple of") == 2
    assert parse_quantity("a dozen") == 12
    assert parse_quantity("invalid") == 1
    print("  [PASS] Auto-categorization and quantity parsing tests passed.")

    # -----------------------------------------------------------------
    # Test 2: Adding Items & Incrementing Quantities
    # -----------------------------------------------------------------
    print("\n--- Test 2: Item Addition & Quantity Incrementing ---")
    res1 = manager.add_item("milk", 1)
    print(f"  Add 'milk': {res1['message']}")
    assert res1['item']['quantity'] == 1

    res2 = manager.add_item("Milk", "two") # Duplicate item with quantity phrase
    print(f"  Add 'Milk' x 2: {res2['message']}")
    assert res2['item']['quantity'] == 3, "Milk quantity should increment to 3."
    print("  [PASS] Quantity incrementing test passed.")

    # -----------------------------------------------------------------
    # Test 3: Fuzzy Item Removal
    # -----------------------------------------------------------------
    print("\n--- Test 3: Fuzzy Removal ---")
    manager.add_item("Organic Honeycrisp Apples", 5)
    print(f"  Current Items Count: {len(manager.get_all_items())}")

    remove_res = manager.remove_item("apples") # Should match "Organic Honeycrisp Apples"
    print(f"  Remove 'apples': {remove_res['message']}")
    assert remove_res['action'] == "removed"
    print("  [PASS] Fuzzy removal test passed.")

    # -----------------------------------------------------------------
    # Test 4: Quantity Modification
    # -----------------------------------------------------------------
    print("\n--- Test 4: Quantity Modification ---")
    mod_res = manager.modify_item("milk", 5)
    print(f"  Modify 'milk' -> 5: {mod_res['message']}")
    assert mod_res['item']['quantity'] == 5
    print("  [PASS] Quantity modification test passed.")

    print("\n" + "=" * 70)
    print("  All Shopping List Manager tests completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    run_shopping_list_tests()
