"""
Test suite for Smart Suggestions Engine in Vaani Shopping Assistant.
Evaluates Product Replenishment, Seasonal Recommendations, and Substitutes.
"""
import sys
import io

# Reconfigure stdout for Windows unicode console output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from smart_suggestions import SmartSuggestionsEngine

def run_suggestion_tests():
    print("=" * 70)
    print("    VAANI SHOPPING ASSISTANT - SMART SUGGESTIONS TEST SUITE")
    print("=" * 70)

    engine = SmartSuggestionsEngine()

    # -----------------------------------------------------------------
    # Test 1: Product Replenishment Recommendations
    # -----------------------------------------------------------------
    print("\n--- Test 1: Product Replenishment Predictions ---")
    mock_history = [
        {"item": "bread", "last_purchased_days_ago": 7, "cycle_days": 5},
        {"item": "milk", "last_purchased_days_ago": 4, "cycle_days": 3},
        {"item": "rice", "last_purchased_days_ago": 10, "cycle_days": 30}
    ]
    recs = engine.get_product_recommendations(mock_history)
    print(f"Input History: {mock_history}")
    print(f"Replenishment Alerts Generated: {len(recs)}")
    for r in recs:
        print(f"  -> Item: {r['item']} | Urgency: {r['urgency']} | Message: \"{r['recommendation']}\"")
    
    assert len(recs) == 2, "Expected 2 items needing replenishment (bread & milk)."
    print("  [PASS] Replenishment prediction test passed.")

    # -----------------------------------------------------------------
    # Test 2: Seasonal Produce Recommendations
    # -----------------------------------------------------------------
    print("\n--- Test 2: Seasonal Recommendations ---")
    summer_recs = engine.get_seasonal_recommendations(month=6) # June
    winter_recs = engine.get_seasonal_recommendations(month=1) # January

    print(f"June (Summer) Title: {summer_recs['title']}")
    print(f"June Seasonal Items: {summer_recs['items']}")
    print(f"January (Winter) Title: {winter_recs['title']}")
    print(f"January Seasonal Items: {winter_recs['items']}")

    assert summer_recs['season'] == 'summer', "June should map to Summer."
    assert winter_recs['season'] == 'winter', "January should map to Winter."
    print("  [PASS] Seasonal recommendations test passed.")

    # -----------------------------------------------------------------
    # Test 3: Product Substitutes & Alternatives
    # -----------------------------------------------------------------
    print("\n--- Test 3: Product Substitutes & Alternatives ---")
    test_items = ["milk", "white bread", "sugar", "butter"]

    for item in test_items:
        res = engine.get_substitutes(item)
        print(f"  -> Query Item: '{item}'")
        print(f"     Substitutes: {res['substitutes']}")
        print(f"     Reason     : {res['reason']}")
        assert len(res['substitutes']) > 0, f"Expected substitutes for {item}."

    print("  [PASS] Product substitutes test passed.")

    # -----------------------------------------------------------------
    # Test 4: Dietary Preference Filtered Substitutes
    # -----------------------------------------------------------------
    print("\n--- Test 4: Vegan Preference Substitute Filtering ---")
    vegan_res = engine.get_substitutes("milk", dietary_preference="vegan")
    print(f"  -> Query: 'milk' (Preference: vegan)")
    print(f"     Substitutes: {vegan_res['substitutes']}")
    assert "almond milk" in vegan_res['substitutes'], "Almond milk should be suggested for vegan milk request."
    print("  [PASS] Vegan preference filtering test passed.")

    print("\n" + "=" * 70)
    print("  All Smart Suggestions tests completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    run_suggestion_tests()
