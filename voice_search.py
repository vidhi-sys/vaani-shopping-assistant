"""
Voice-Activated Search Engine for Vaani Shopping Assistant.

Parses voice search queries for item names, brands, and price constraints
("under $5", "less than 10 dollars", "between 3 and 8 dollars"), then searches
and ranks matching products from catalog.json.
"""

import json
import re
import os
from typing import Dict, Any, List, Optional, Tuple


def parse_price_filter(query: str) -> Tuple[Optional[float], Optional[float], str]:
    """
    Extracts price constraints from natural language query using regex patterns.

    Supported patterns:
    - "under $5", "less than 10 dollars", "below 8 bucks", "under 5"
    - "above $10", "more than 5 dollars", "over 4 bucks"
    - "between 3 and 8 dollars", "between $3 and $8"

    Returns:
        Tuple[min_price, max_price, cleaned_query_without_price_phrase]
    """
    clean_query = query.lower().strip()
    min_price = None
    max_price = None

    # Pattern A: Between X and Y dollars / between $X and $Y
    between_match = re.search(r'\bbetween\s+\$?(\d+(?:\.\d+)?)\s*(?:and|-)\s*\$?(\d+(?:\.\d+)?)\b', clean_query)
    if between_match:
        try:
            min_price = float(between_match.group(1))
            max_price = float(between_match.group(2))
            clean_query = re.sub(between_match.group(0), '', clean_query)
            return min_price, max_price, clean_query.strip()
        except ValueError:
            pass

    # Pattern B: Under / less than / below / under $X / X dollars
    under_match = re.search(r'\b(?:under|less than|below)\s+\$?(\d+(?:\.\d+)?)(?:\s*(?:dollars|bucks|\$))?\b', clean_query)
    if under_match:
        try:
            max_price = float(under_match.group(1))
            clean_query = re.sub(under_match.group(0), '', clean_query)
            return min_price, max_price, clean_query.strip()
        except ValueError:
            pass

    # Pattern C: Over / more than / above / over $X / X dollars
    over_match = re.search(r'\b(?:over|more than|above|greater than)\s+\$?(\d+(?:\.\d+)?)(?:\s*(?:dollars|bucks|\$))?\b', clean_query)
    if over_match:
        try:
            min_price = float(over_match.group(1))
            clean_query = re.sub(over_match.group(0), '', clean_query)
            return min_price, max_price, clean_query.strip()
        except ValueError:
            pass

    return min_price, max_price, clean_query.strip()


class VoiceSearchEngine:
    """Product catalog search engine with relevance ranking and price filtering."""

    def __init__(self, catalog_path: str = "catalog.json"):
        self.catalog_path = catalog_path
        self.products: List[Dict[str, Any]] = []
        self.load_catalog()

    def load_catalog(self):
        """Loads product catalog from JSON file."""
        if os.path.exists(self.catalog_path):
            try:
                with open(self.catalog_path, "r", encoding="utf-8") as f:
                    self.products = json.load(f)
            except Exception as e:
                print(f"Error loading catalog file {self.catalog_path}: {e}")
                self.products = []
        else:
            print(f"Catalog file {self.catalog_path} not found.")
            self.products = []

    def search_items(
        self, 
        query: str, 
        brand_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes voice-activated product search.

        Args:
            query: Natural language query (e.g. "organic milk under $5").
            brand_filter: Optional explicit brand filter.

        Returns:
            Dict containing status, query, filters applied, results list, and count.
        """
        if not query or not query.strip():
            return {
                "status": "empty_query",
                "message": "Please enter or speak a product search query.",
                "query": "",
                "count": 0,
                "results": []
            }

        # Step 1: Extract price bounds from query string
        min_price, max_price, term_query = parse_price_filter(query)

        # Remove filler search words
        filler_words = ["search", "find", "for", "look", "me", "show", "is", "there", "any", "cheap", "buy"]
        search_terms = [w for w in term_query.split() if w not in filler_words and len(w) > 1]
        search_string = " ".join(search_terms)

        scored_results = []

        for prod in self.products:
            p_name = prod["name"].lower()
            p_brand = prod["brand"].lower()
            p_cat = prod["category"].lower()
            price = prod["price"]

            # Filter Check: Price range
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue

            # Filter Check: Brand
            if brand_filter and brand_filter.lower() not in p_brand:
                continue

            # Step 2: Calculate Relevance Score
            score = 0
            
            # Exact product name match
            if search_string and search_string in p_name:
                score += 100
            elif search_string and p_name in search_string:
                score += 80

            # Word token matches
            for term in search_terms:
                if term in p_name:
                    score += 20
                if term in p_brand:
                    score += 15
                if term in p_cat:
                    score += 10

            if score > 0 or not search_terms:
                scored_results.append((score, prod))

        # Sort by relevance score descending, then price ascending
        scored_results.sort(key=lambda x: (-x[0], x[1]["price"]))
        final_results = [item[1] for item in scored_results]

        if not final_results:
            return {
                "status": "no_results",
                "message": f"No products found matching '{query}'. Try rephrasing your search or adjusting price filters.",
                "query": query,
                "filters": {"min_price": min_price, "max_price": max_price, "brand": brand_filter},
                "count": 0,
                "results": []
            }

        return {
            "status": "success",
            "message": f"Found {len(final_results)} matching products.",
            "query": query,
            "filters": {"min_price": min_price, "max_price": max_price, "brand": brand_filter},
            "count": len(final_results),
            "results": final_results
        }
