"""
Shopping List Management Module for Vaani Shopping Assistant.

Maintains a shopping list as a collection of structured objects:
{ "id": str, "item": str, "quantity": int, "category": str, "addedAt": str }

Features:
- Auto-categorization using static lookup dictionary.
- Quantity parsing for numeric digits and spoken numbers ("two", "a couple of", "a dozen").
- Quantity incrementing on duplicate additions.
- Fuzzy matching item removal.
"""

import uuid
import re
import datetime
from typing import Dict, Any, List, Optional

# Static Category Lookup Dictionary
CATEGORY_MAPPINGS: Dict[str, List[str]] = {
    "dairy": [
        "milk", "doodh", "दूध", "butter", "makkan", "मक्खन", "cheese", "paneer", "पनीर",
        "yogurt", "dahi", "curd", "cream", "ghee", "घी"
    ],
    "produce": [
        "apple", "apples", "seb", "सेब", "banana", "bananas", "kela", "केला",
        "potato", "potatoes", "aalu", "आलू", "tomato", "tomatoes", "tamatar", "टमाटर",
        "onion", "onions", "pyaz", "प्याज़", "spinach", "palak", "पालक", "orange",
        "oranges", "lemon", "lemons", "ginger", "adrak", "garlic", "lahsun"
    ],
    "bakery": [
        "bread", "buns", "bagel", "sourdough", "croissant", "cake", "muffin", "toast"
    ],
    "beverages": [
        "coffee", "tea", "chai", "चाय", "juice", "soda", "water", "lemonade",
        "energy drink", "coca cola", "pepsi"
    ],
    "snacks": [
        "potato chips", "chips", "biscuits", "cookies", "namkeen", "popcorn", "chocolate", "nuts",
        "almonds", "cashews"
    ],
    "household": [
        "soap", "shampoo", "detergent", "toothpaste", "dishwash", "tissue", "cleaner",
        "sponge", "paper towel"
    ]
}

# Spoken Quantity Mapping
QUANTITY_WORD_MAP: Dict[str, int] = {
    "one": 1, "a": 1, "an": 1, "single": 1,
    "two": 2, "couple": 2, "a couple": 2, "a couple of": 2, "pair": 2,
    "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "dozen": 12, "a dozen": 12,
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10, "दर्जन": 12
}


def parse_quantity(val: Any) -> int:
    """Parses spoken numbers, number phrases, or integer values into positive integers."""
    if isinstance(val, int) and val > 0:
        return val

    str_val = str(val).strip().lower()

    # Check direct digits
    digit_match = re.search(r'\b(\d+)\b', str_val)
    if digit_match:
        try:
            return max(1, int(digit_match.group(1)))
        except ValueError:
            pass

    # Check spoken word matches (longer phrases first)
    for key in sorted(QUANTITY_WORD_MAP.keys(), key=len, reverse=True):
        if key in str_val:
            return QUANTITY_WORD_MAP[key]

    return 1


def auto_categorize(item_name: str) -> str:
    """
    Categorizes a product using static category lookup dictionary.
    Defaults to 'other' for unrecognized items.
    """
    clean_name = item_name.lower().strip()
    words = re.findall(r'\b\w+\b', clean_name)

    # Check multi-word compound phrases first
    for category, keywords in CATEGORY_MAPPINGS.items():
        for kw in keywords:
            if " " in kw and kw in clean_name:
                return category

    # Check word tokens
    for category, keywords in CATEGORY_MAPPINGS.items():
        for kw in keywords:
            if kw in words or clean_name == kw:
                return category

    return "other"


class ShoppingListManager:
    """In-memory & JSON serializable Shopping List Manager."""

    def __init__(self):
        self.items: List[Dict[str, Any]] = []

    def get_all_items(self) -> List[Dict[str, Any]]:
        """Returns all shopping list items."""
        return self.items

    def add_item(self, item_name: str, quantity: Any = 1) -> Dict[str, Any]:
        """
        Adds item to list. If item already exists (case-insensitive match),
        increments quantity instead of duplicating.
        """
        clean_name = item_name.strip()
        qty = parse_quantity(quantity)
        category = auto_categorize(clean_name)

        # Check for existing item
        existing = self.find_item_by_name(clean_name)
        if existing:
            existing["quantity"] += qty
            existing["updatedAt"] = datetime.datetime.now().isoformat()
            return {
                "action": "incremented",
                "item": existing,
                "message": f"Updated {existing['item']} quantity to {existing['quantity']}"
            }

        # Create new item
        new_item = {
            "id": str(uuid.uuid4())[:8],
            "item": clean_name.title(),
            "quantity": qty,
            "category": category,
            "addedAt": datetime.datetime.now().isoformat()
        }
        self.items.append(new_item)
        return {
            "action": "added",
            "item": new_item,
            "message": f"Added {qty} {new_item['item']} to {category.title()}"
        }

    def remove_item(self, item_name: str) -> Dict[str, Any]:
        """Removes an item by name using fuzzy/substring matching."""
        target = self.find_item_by_name(item_name)
        if target:
            self.items.remove(target)
            return {
                "action": "removed",
                "item": target,
                "message": f"Removed {target['item']} from shopping list"
            }

        return {
            "action": "not_found",
            "item": None,
            "message": f"Item '{item_name}' not found on list"
        }

    def modify_item(self, item_name: str, new_quantity: int) -> Dict[str, Any]:
        """Modifies quantity for an existing item. Deletes item if quantity <= 0."""
        target = self.find_item_by_name(item_name)
        if not target:
            return {
                "action": "not_found",
                "item": None,
                "message": f"Item '{item_name}' not found on list"
            }

        parsed_qty = max(0, int(new_quantity))
        if parsed_qty == 0:
            return self.remove_item(item_name)

        target["quantity"] = parsed_qty
        target["updatedAt"] = datetime.datetime.now().isoformat()
        return {
            "action": "modified",
            "item": target,
            "message": f"Updated {target['item']} quantity to {parsed_qty}"
        }

    def find_item_by_name(self, query: str) -> Optional[Dict[str, Any]]:
        """Finds item using exact or partial substring matching."""
        clean_query = query.strip().lower()

        # 1. Exact match
        for item in self.items:
            if item["item"].lower() == clean_query:
                return item

        # 2. Substring match
        for item in self.items:
            if clean_query in item["item"].lower() or item["item"].lower() in clean_query:
                return item

        return None

    def clear(self):
        """Clears all items."""
        self.items = []
