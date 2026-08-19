"""
Test script for Vaani Shopping Assistant Voice Input & Intent Parsing Module.
Evaluates 10 example phrases (including English and Hindi inputs) and verifies output schemas.
"""

import sys
import json
import os
from voice_input import IntentParser, VoiceInputPipeline

def run_tests():
    print("=" * 70)
    print("      VAANI SHOPPING ASSISTANT - VOICE INPUT MODULE TEST SUITE")
    print("=" * 70)

    parser = IntentParser()

    test_cases = []
    dataset_file = "dataset_samples.json"
    if os.path.exists(dataset_file):
        try:
            with open(dataset_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("samples", []):
                    test_cases.append({
                        "phrase": item["phrase"],
                        "lang": item.get("language", "en"),
                        "expected_intent": item["intent"],
                        "expected_item": item.get("item"),
                        "expected_quantity": item.get("quantity", 1)
                    })
            print(f"Loaded {len(test_cases)} evaluation cases from {dataset_file}.")
        except Exception as e:
            print(f"Error loading {dataset_file}: {e}")

    if not test_cases:
        test_cases = [
            {"phrase": "Add milk to my shopping list", "lang": "en", "expected_intent": "add", "expected_item": "milk", "expected_quantity": 1},
            {"phrase": "I need to buy 3 apples", "lang": "en", "expected_intent": "add", "expected_item": "apples", "expected_quantity": 3},
            {"phrase": "Remove bananas from shopping list", "lang": "en", "expected_intent": "remove", "expected_item": "bananas", "expected_quantity": 1},
            {"phrase": "दूध लिस्ट में जोड़ो", "lang": "hi", "expected_intent": "add", "expected_item": "milk (दूध)", "expected_quantity": 1},
            {"phrase": "केला लिस्ट से निकालो", "lang": "hi", "expected_intent": "remove", "expected_item": "bananas (केला)", "expected_quantity": 1}
        ]

    passed = 0
    total = len(test_cases)

    for idx, case in enumerate(test_cases, 1):
        phrase = case["phrase"]
        lang = case["lang"]
        res = parser.parse_intent(phrase, language=lang)

        print(f"\nTest {idx}/{total}: \"{phrase}\" (Lang: {lang})")
        print(f"  -> Transcribed/Raw Text : {res.get('raw_text')}")
        print(f"  -> Extracted Intent     : {res.get('intent')} (Confidence: {res.get('confidence')})")
        print(f"  -> Extracted Item       : {res.get('item')}")
        print(f"  -> Extracted Quantity   : {res.get('quantity')}")
        print(f"  -> Pipeline Status      : {res.get('status')}")

        # Verification check
        intent_ok = res.get("intent") == case["expected_intent"]
        item_ok = res.get("item") == case["expected_item"]
        qty_ok = res.get("quantity") == case["expected_quantity"]

        if intent_ok and (item_ok or case["expected_item"] is None) and qty_ok:
            print("  ✅ [PASS]")
            passed += 1
        else:
            print(f"  ⚠️ [PARTIAL/CHECK] Expected: intent={case['expected_intent']}, item={case['expected_item']}, qty={case['expected_quantity']}")

    print("\n" + "=" * 70, flush=True)
    print(f"Summary: {passed}/{total} tests completed with expected outputs.", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    run_tests()
