"""
FastAPI Server for Vaani Shopping Assistant.

Integrates Voice Input, Intent Parsing, Smart Suggestions, Shopping List Manager,
Voice-Activated Search, and Static Web UI Hosting.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import os
import uvicorn

from voice_input import VoiceInputPipeline
from smart_suggestions import SmartSuggestionsEngine
from shopping_list import ShoppingListManager, parse_quantity, auto_categorize
from voice_search import VoiceSearchEngine

# Initialize FastAPI app
app = FastAPI(
    title="Vaani Shopping Assistant",
    description="Full Voice Input, Shopping List Management, Search, and Suggestions API.",
    version="2.0.0"
)

# Enable CORS for browser frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Singletons
pipeline = VoiceInputPipeline(whisper_model_size="base")
suggestions_engine = SmartSuggestionsEngine()
list_manager = ShoppingListManager()
search_engine = VoiceSearchEngine(catalog_path="catalog.json")
logger = logging.getLogger("vaani_app")


# Request Models
class TextParseRequest(BaseModel):
    text: str
    language: Optional[str] = "en"


class AddItemRequest(BaseModel):
    item: str
    quantity: Optional[Any] = 1


class RemoveItemRequest(BaseModel):
    item: str


class ModifyItemRequest(BaseModel):
    item: str
    quantity: int


class HistoryRecommendationRequest(BaseModel):
    history: List[Dict[str, Any]]


class SubstituteRequest(BaseModel):
    item: str
    dietary_preference: Optional[str] = None


@app.get("/health")
def health_check():
    """Health check endpoint to verify backend service status."""
    return {
        "status": "healthy",
        "service": "Vaani Shopping Assistant",
        "modules": ["voice_input", "shopping_list", "voice_search", "smart_suggestions"]
    }


# =====================================================================
# 1. Voice Processing Endpoints
# =====================================================================

@app.post("/api/voice/process")
async def process_voice_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Accepts recorded audio (.wav/.webm/.mp3 blob) from browser.
    Returns structured action, updates server-side list state if appropriate,
    and enriches response with smart suggestions.
    """
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio payload received.")

        result = pipeline.process_audio(audio_bytes, language=language)

        item = result.get("item")
        intent = result.get("intent")
        qty = result.get("quantity") or 1

        # Auto-execute list mutations on server manager
        if intent == "add" and item:
            list_action = list_manager.add_item(item, qty)
            result["list_action"] = list_action
        elif intent == "remove" and item:
            list_action = list_manager.remove_item(item)
            result["list_action"] = list_action
        elif intent == "modify" and item:
            list_action = list_manager.modify_item(item, qty)
            result["list_action"] = list_action

        # Attach smart substitute suggestions if item present
        if item:
            sub_data = suggestions_engine.get_substitutes(item)
            result["smart_suggestions"] = {
                "substitutes": sub_data.get("substitutes", []),
                "tip": sub_data.get("reason")
            }

        return result

    except Exception as e:
        logger.error(f"Error processing voice upload: {e}")
        return {
            "status": "error",
            "error": str(e),
            "transcription": "",
            "intent": "unknown",
            "item": None,
            "quantity": 1
        }


@app.post("/api/voice/parse-text")
def parse_voice_text(request: TextParseRequest) -> Dict[str, Any]:
    """Parses a transcribed text string directly into structured shopping action."""
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text field cannot be empty.")

    result = pipeline.process_text(request.text, language=request.language or "en")
    
    item = result.get("item")
    intent = result.get("intent")
    qty = result.get("quantity") or 1

    if intent == "add" and item:
        result["list_action"] = list_manager.add_item(item, qty)
    elif intent == "remove" and item:
        result["list_action"] = list_manager.remove_item(item)

    if item:
        sub_data = suggestions_engine.get_substitutes(item)
        result["smart_suggestions"] = {
            "substitutes": sub_data.get("substitutes", []),
            "tip": sub_data.get("reason")
        }

    return result


# =====================================================================
# 2. Shopping List Management Endpoints
# =====================================================================

@app.get("/api/list/items")
def get_shopping_list() -> Dict[str, Any]:
    """Returns all items currently in shopping list."""
    items = list_manager.get_all_items()
    return {"status": "success", "count": len(items), "items": items}


@app.post("/api/list/add")
def add_item_to_list(request: AddItemRequest) -> Dict[str, Any]:
    """Adds or increments item in shopping list."""
    if not request.item:
        raise HTTPException(status_code=400, detail="Item name required.")

    res = list_manager.add_item(request.item, request.quantity)
    return {"status": "success", **res}


@app.post("/api/list/remove")
def remove_item_from_list(request: RemoveItemRequest) -> Dict[str, Any]:
    """Removes item by name match."""
    res = list_manager.remove_item(request.item)
    return {"status": "success", **res}


@app.post("/api/list/modify")
def modify_item_quantity(request: ModifyItemRequest) -> Dict[str, Any]:
    """Modifies quantity for an existing item."""
    res = list_manager.modify_item(request.item, request.quantity)
    return {"status": "success", **res}


# =====================================================================
# 3. Voice-Activated Search Endpoints
# =====================================================================

@app.get("/api/search")
def search_product_catalog(
    q: str = Query(..., description="Search query string e.g. 'organic milk under $5'"),
    brand: Optional[str] = Query(None, description="Optional brand filter")
) -> Dict[str, Any]:
    """Searches catalog products with price regex parsing and relevance ranking."""
    return search_engine.search_items(query=q, brand_filter=brand)


# =====================================================================
# 4. Smart Suggestions Endpoints
# =====================================================================

@app.post("/api/suggestions/recommendations")
def get_product_recommendations(request: HistoryRecommendationRequest) -> Dict[str, Any]:
    """Predicts items due for replenishment based on shopping history cycles."""
    recommendations = suggestions_engine.get_product_recommendations(request.history)
    return {"status": "success", "count": len(recommendations), "recommendations": recommendations}


@app.get("/api/suggestions/seasonal")
def get_seasonal_recommendations(month: Optional[int] = None) -> Dict[str, Any]:
    """Returns seasonal produce recommendations."""
    return suggestions_engine.get_seasonal_recommendations(month=month)


@app.post("/api/suggestions/substitutes")
def get_product_substitutes(request: SubstituteRequest) -> Dict[str, Any]:
    """Returns product alternatives."""
    return suggestions_engine.get_substitutes(
        item_name=request.item,
        dietary_preference=request.dietary_preference
    )


# =====================================================================
# 5. Static Web UI Hosting
# =====================================================================

if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
