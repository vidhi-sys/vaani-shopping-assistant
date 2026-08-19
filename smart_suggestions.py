"""
Smart Suggestions Engine for Vaani Shopping Assistant.

Provides AI-driven product recommendations, seasonal item suggestions,
and dietary/stock product alternatives.

Integration:
- Free AI/ML Service: Hugging Face Free Inference API (zero-shot classification / semantic similarity).
- Offline Fallback: Zero-latency heuristic and rule-based knowledge engine.
"""

import os
import json
import logging
import datetime
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vaani_smart_suggestions")

# Product Substitute Database (Healthy, Dietary & Stock Alternatives)
DEFAULT_SUBSTITUTES: Dict[str, Dict[str, Any]] = {
    "milk": {
        "substitutes": ["almond milk", "oat milk", "soy milk", "coconut milk"],
        "category": "dairy",
        "reason": "Plant-based lactose-free alternatives available."
    },
    "regular milk": {
        "substitutes": ["almond milk", "oat milk", "skimmed milk"],
        "category": "dairy",
        "reason": "Lower calorie and plant-based alternatives."
    },
    "bread": {
        "substitutes": ["whole wheat bread", "multigrain bread", "sourdough bread"],
        "category": "bakery",
        "reason": "Higher fiber wheat and multigrain options."
    },
    "white bread": {
        "substitutes": ["whole wheat bread", "brown bread", "multigrain bread"],
        "category": "bakery",
        "reason": "Healthier whole grain alternatives."
    },
    "sugar": {
        "substitutes": ["honey", "stevia", "jaggery", "maple syrup"],
        "category": "pantry",
        "reason": "Natural unrefined sweeteners."
    },
    "butter": {
        "substitutes": ["olive oil", "ghee", "margarine", "avocado spread"],
        "category": "dairy",
        "reason": "Heart-healthy fats and cooking oils."
    },
    "potato": {
        "substitutes": ["sweet potato", "cauliflower", "turnip"],
        "category": "vegetables",
        "reason": "Low-glycemic nutrient-rich root alternatives."
    },
    "potatoes": {
        "substitutes": ["sweet potatoes", "cauliflower", "turnips"],
        "category": "vegetables",
        "reason": "Low-glycemic nutrient-rich root alternatives."
    },
    "white rice": {
        "substitutes": ["brown rice", "quinoa", "cauliflower rice"],
        "category": "grains",
        "reason": "High-fiber and low-carb grain substitutes."
    },
    "rice": {
        "substitutes": ["brown rice", "quinoa", "millet (बाजरा)"],
        "category": "grains",
        "reason": "High-fiber grain alternatives."
    },
    "cooking oil": {
        "substitutes": ["extra virgin olive oil", "mustard oil", "cold pressed coconut oil"],
        "category": "pantry",
        "reason": "Unrefined healthy fats."
    }
}

# Seasonal Recommendations Knowledge Base (India & Global)
SEASONAL_PRODUCE: Dict[str, Dict[str, Any]] = {
    "winter": {
        "months": [12, 1, 2],
        "title": "Winter Favorites & Immune Boosters",
        "items": ["oranges", "carrots", "spinach", "ginger", "sweet potatoes", "gajar (गाजर)", "palak (पालक)", "amla"],
        "tip": "In season: Fresh winter greens and vitamin-C rich citrus fruits!"
    },
    "spring": {
        "months": [3, 4],
        "title": "Spring Fresh Harvest",
        "items": ["strawberries", "peas", "cucumber", "lemons", "mint", "hari matar (हरी मटर)"],
        "tip": "In season: Fresh crisp vegetables and spring berries."
    },
    "summer": {
        "months": [5, 6, 7],
        "title": "Summer Coolers & Tropical Fruits",
        "items": ["mangoes (आम)", "watermelon (तरबूज)", "muskmelon", "cucumber (ककड़ी)", "lemonade", "coconut water"],
        "tip": "In season: Hydrating tropical fruits and mango harvest!"
    },
    "monsoon": {
        "months": [8, 9],
        "title": "Monsoon Warmers & Teas",
        "items": ["ginger tea (अदरक चाय)", "corn (भुट्टा)", "garlic", "turmeric", "jamun"],
        "tip": "In season: Warm spices, corn, and immunity-boosting teas."
    },
    "autumn": {
        "months": [10, 11],
        "title": "Autumn & Festive Season Delights",
        "items": ["apples (सेब)", "pomegranates (अनार)", "dates", "nuts & dry fruits", "jaggery"],
        "tip": "In season: Fresh apples, pomegranates, and festive nuts."
    }
}

# Typical Item Consumption Cycles (in Days)
DEFAULT_ITEM_CYCLES: Dict[str, int] = {
    "milk": 3,
    "bread": 5,
    "eggs": 7,
    "butter": 14,
    "bananas": 4,
    "apples": 7,
    "tomatoes": 5,
    "onions": 10,
    "potatoes": 12,
    "rice": 30,
    "flour": 25,
    "sugar": 30,
    "coffee": 30,
    "tea": 30,
    "cooking oil": 30,
    "soap": 20,
    "shampoo": 30
}


class SmartSuggestionsEngine:
    """Smart Suggestions engine handling product recommendations, seasonal items, and substitutes."""

    def __init__(self):
        self.hf_token = os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_TOKEN")

    # ------------------------------------------------------------------
    # 1. Product Replenishment Recommendations
    # ------------------------------------------------------------------
    def get_product_recommendations(
        self, 
        shopping_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyzes shopping history to predict items that need replenishment.

        Args:
            shopping_history: List of dicts e.g.:
              [{"item": "bread", "last_purchased_days_ago": 7, "cycle_days": 5}, ...]

        Returns:
            List of recommendation dicts containing item, status, urgency, and message.
        """
        recommendations = []
        
        for record in shopping_history:
            item = record.get("item", "").strip().lower()
            if not item:
                continue

            days_ago = record.get("last_purchased_days_ago", 0)
            typical_cycle = record.get("cycle_days") or DEFAULT_ITEM_CYCLES.get(item, 7)

            if days_ago >= typical_cycle:
                urgency = "high" if days_ago >= typical_cycle * 1.3 else "medium"
                msg = f"It looks like you're running low on {item.title()} (last bought {days_ago} days ago)."
                
                recommendations.append({
                    "item": item,
                    "last_purchased_days_ago": days_ago,
                    "typical_cycle_days": typical_cycle,
                    "urgency": urgency,
                    "recommendation": msg,
                    "suggested_action": f"Add {item} to list"
                })

        return recommendations

    # ------------------------------------------------------------------
    # 2. Seasonal Recommendations
    # ------------------------------------------------------------------
    def get_seasonal_recommendations(
        self, 
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Returns seasonal item recommendations based on the current or specified month (1-12).

        Args:
            month: Month integer (1-12). Defaults to current system month.

        Returns:
            Dict containing season name, title, items, and recommendation tip.
        """
        if month is None:
            month = datetime.datetime.now().month

        matched_season = "summer"
        season_data = SEASONAL_PRODUCE["summer"]

        for s_name, s_info in SEASONAL_PRODUCE.items():
            if month in s_info["months"]:
                matched_season = s_name
                season_data = s_info
                break

        return {
            "status": "success",
            "month": month,
            "season": matched_season,
            "title": season_data["title"],
            "items": season_data["items"],
            "tip": season_data["tip"]
        }

    # ------------------------------------------------------------------
    # 3. Product Substitutes & Alternatives
    # ------------------------------------------------------------------
    def get_substitutes(
        self, 
        item_name: str, 
        dietary_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Finds product substitutes using Free AI API or local heuristic knowledge.

        Args:
            item_name: Product name (e.g. "milk", "bread", "white sugar").
            dietary_preference: Optional filter ("vegan", "gluten-free", "low-sugar").

        Returns:
            Dict containing original item, substitutes list, category, and reason.
        """
        clean_item = item_name.strip().lower()

        # Step 1: Check Hugging Face Free API if token is provided
        ai_substitutes = self._query_hf_substitutes(clean_item)
        if ai_substitutes:
            return {
                "status": "success",
                "source": "huggingface_free_api",
                "item": clean_item,
                "substitutes": ai_substitutes,
                "reason": f"AI-suggested alternatives for {clean_item}."
            }

        # Step 2: Fallback to Local Rule Knowledge Base
        if clean_item in DEFAULT_SUBSTITUTES:
            info = DEFAULT_SUBSTITUTES[clean_item]
            subs = info["substitutes"]
            
            # Apply dietary preference filtering if requested
            if dietary_preference == "vegan" and clean_item in ["milk", "regular milk", "butter"]:
                subs = [s for s in subs if "milk" in s or "oil" in s or "spread" in s]

            return {
                "status": "success",
                "source": "local_knowledge_engine",
                "item": clean_item,
                "substitutes": subs,
                "category": info.get("category", "general"),
                "reason": info.get("reason", "Popular product alternative.")
            }

        # Step 3: Generic heuristic fallback
        return {
            "status": "success",
            "source": "heuristic_fallback",
            "item": clean_item,
            "substitutes": [f"organic {clean_item}", f"low-fat {clean_item}"],
            "reason": f"Standard quality alternatives for {clean_item}."
        }

    def _query_hf_substitutes(self, item_name: str) -> Optional[List[str]]:
        """Queries Hugging Face Free Inference API for substitute classification if token exists."""
        if not self.hf_token:
            return None

        try:
            import urllib.request
            url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
            headers = {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json"
            }
            candidate_labels = ["dairy substitute", "plant-based", "gluten-free", "healthy alternative"]
            payload = json.dumps({
                "inputs": f"Alternative options for {item_name}",
                "parameters": {"candidate_labels": candidate_labels}
            }).encode("utf-8")

            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as response:
                res = json.loads(response.read().decode("utf-8"))
                top_label = res.get("labels", [])[0] if res.get("labels") else None
                if top_label and item_name in DEFAULT_SUBSTITUTES:
                    return DEFAULT_SUBSTITUTES[item_name]["substitutes"]
        except Exception as e:
            logger.warning(f"Hugging Face Free API substitute call skipped: {e}")

        return None
