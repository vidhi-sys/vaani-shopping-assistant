# Vaani - Smart Voice Store 🎙️🛒

![Vaani Smart Store](static/logo.png)

**Vaani** is a voice-first, multilingual shopping assistant and smart store manager. It converts spoken audio commands into structured shopping list actions (`intent`, `item`, `quantity`, `category`) in **English** and **Hindi**, performs regex-powered voice catalog searches with price bounds, and provides AI-driven smart recommendations.

---

## 📋 Table of Contents

- [Features Architecture](#-features-architecture)
- [System Architecture & Pipeline](#-system-architecture--pipeline)
- [Modules Overview](#-modules-overview)
- [API Reference](#-api-reference)
- [Mobile-First UI/UX Design](#-mobile-first-uiux-design)
- [Free-Tier Hosting & Deployment Guide](#-free-tier-hosting--deployment-guide)
- [Installation & Local Setup](#-installation--local-setup)
- [Automated Verification & Test Suites](#-automated-verification--test-suites)

---

## 🌟 Features Architecture

### 1. Voice Input & Intent Pipeline (`voice_input.py`)
- **Speech-to-Text (STT)**: Transcribes browser `.webm`/`.wav` audio using OpenAI's Whisper model (`"base"` or `"small"`).
- **Multilingual Support**: Supports auto-detection and explicit language selection for English and Hindi.
- **Intent Parsing**: Classifies text into `["add", "remove", "modify", "search"]` using `sentence-transformers` (`all-MiniLM-L6-v2`) with a zero-latency `scikit-learn` TF-IDF fallback.

### 2. Shopping List Management (`shopping_list.py`)
- **Data Model**: `{ id: string, item: string, quantity: number, category: string, addedAt: string }`
- **Smart Operations**:
  - `add_item(item, quantity)`: Automatically increments item quantity on duplicate additions.
  - `remove_item(item)`: Fuzzy substring removal (e.g. *"milk"* removes *"Milk 2%"*).
  - `modify_item(item, new_quantity)`: Updates item quantity or deletes if $\le 0$.
- **Auto-Categorization**: Static lookup dictionary mapping items to `Dairy`, `Produce`, `Bakery`, `Beverages`, `Snacks`, `Household`, or `Other`.
- **Spoken Quantity Parsing**: Converts spoken words (*"two"*, *"a couple of"* $\rightarrow 2$, *"a dozen"* $\rightarrow 12$).
- **Client Persistence**: Browser `localStorage` sync for offline state management.

### 3. Voice-Activated Search Engine (`voice_search.py` & `catalog.json`)
- **Product Catalog**: 35+ grocery items with `id`, `name`, `brand`, `category`, `price`, and `size`.
- **Price Regex Parsing**: Extracts price bounds e.g. *"under $5"*, *"less than 10 dollars"*, *"between 3 and 8 dollars"* into `{min_price, max_price}`.
- **Relevance Ranking**: Ranks results by exact match > brand match > partial keyword match.

### 4. Smart Suggestions Engine (`smart_suggestions.py`)
- **Replenishment Alerts**: Predicts restock needs based on past purchase frequency (*"It looks like you're running low on bread"*).
- **Seasonal Recommendations**: Recommends seasonal produce based on current month (Summer mangoes, Winter oranges & spinach).
- **Product Substitutes**: Finds healthy/dietary alternatives (`milk` $\rightarrow$ `almond milk`, `sugar` $\rightarrow$ `honey`) using Hugging Face Free API (`facebook/bart-large-mnli`) or local fallback.

---

## 🏗️ System Architecture & Pipeline

```
+----------------------------------------------------------------------------------------+
|                              Vaani Smart Voice Store                                   |
|               (Mobile-First Web SPA with MediaRecorder Audio & UI Tabs)                |
+-------------------------------------------+--------------------------------------------+
                                            |
                         +------------------+------------------+
                         |                                     |
                         v                                     v
          +-----------------------------+       +------------------------------+
          | Shopping List Manager       |       | Voice-Activated Search Engine|
          | - add / remove / modify     |       | - 35+ Product Catalog        |
          | - Auto-Categorization       |       | - Price Regex Parser ($ min/max)
          | - LocalStorage Sync         |       | - Relevance Ranking          |
          +-----------------------------+       +------------------------------+
                         |                                     |
                         +------------------+------------------+
                                            |
                                            v
                         +-------------------------------------+
                         |      FastAPI Backend Server         |
                         | - /api/voice/process                |
                         | - /api/list/*                       |
                         | - /api/search                       |
                         | - /api/suggestions/*                |
                         | - Static UI Asset Hosting           |
                         +-------------------------------------+
```

---

## 🔌 API Reference

### Voice Endpoints
- `POST /api/voice/process`: Upload audio file (`file: UploadFile`). Returns structured action `{ intent, item, quantity, list_action, smart_suggestions }`.
- `POST /api/voice/parse-text`: Send JSON payload `{"text": "Add 2 milk"}` for direct intent parsing.

### Shopping List Endpoints
- `GET /api/list/items`: Retrieve active shopping list.
- `POST /api/list/add`: Body `{"item": "Bread", "quantity": 2}`.
- `POST /api/list/remove`: Body `{"item": "Bread"}`.
- `POST /api/list/modify`: Body `{"item": "Bread", "quantity": 5}`.

### Voice Search Endpoint
- `GET /api/search?q=organic+milk+under+$5`: Returns filtered, ranked catalog items.

### Smart Suggestions Endpoints
- `POST /api/suggestions/recommendations`: Body `{"history": [...]}`.
- `GET /api/suggestions/seasonal?month=6`: Returns seasonal produce for month.
- `POST /api/suggestions/substitutes`: Body `{"item": "milk", "dietary_preference": "vegan"}`.

---

## 🎨 Mobile-First UI/UX Design

The web interface (`static/index.html`) is built with a vibrant, modern warm orange (`#ff7a00`) and rich red (`#e62e00`) visual identity inspired by the **Vaani Smart Store** logo:
- **Pulsing Mic Button**: Interactive voice button with real-time state changes (`idle`, `listening`, `processing`).
- **Live Transcript Display**: Shows recognized speech and inline status hints.
- **Tabbed Interface**:
  1. 🛒 **My List**: Categorized shopping list with category color dots, quantity badges, and manual `(X)` remove buttons.
  2. 🔍 **Search Catalog**: Product search drawer with price filter chips and `+ Add` buttons.
  3. 💡 **Smart Suggestions**: Restock alerts, seasonal produce chips, and substitute lookups.

---

## 🌐 FREE-TIER HOSTING & DEPLOYMENT GUIDE

### 1. Frontend Deployment (Netlify / Vercel / GitHub Pages)
- **HTTPS Requirement**: Modern web browsers require HTTPS to grant microphone access (`navigator.mediaDevices.getUserMedia`). Netlify and Vercel issue automatic free SSL certificates.
- **Publish Directory**: Set publish directory to `static/`.

### 2. Backend Deployment (Render.com / Railway)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  - `WHISPER_MODEL_SIZE`: `base`
  - `HUGGINGFACE_API_KEY`: Optional free HF token (see `.env.example`).

#### ⚠️ Free-Tier Cold Start Trade-off:
> Free backend instances on Render/Railway sleep after 15 minutes of inactivity. The first request after a sleep period incurs a **30-50 second cold-start delay** while PyTorch and Whisper load into memory. Subsequent requests execute in real-time (~1s).

---

## 💻 Installation & Local Setup

### 1. Clone Repository & Install Dependencies
```bash
git clone https://github.com/vidhi-sys/vaani-shopping-assistant.git
cd vaani-shopping-assistant
pip install -r requirements.txt
```

> **Note**: Install System `ffmpeg` for Whisper audio conversion:
> - Windows: `winget install ffmpeg`
> - macOS: `brew install ffmpeg`
> - Linux: `sudo apt install ffmpeg`

### 2. Run Server Locally
```bash
uvicorn app:app --reload --port 8000
```
Open **`http://localhost:8000`** in your browser!

---

## 🧪 Automated Verification & Test Suites

Run the automated test suite scripts to verify engine components:

```bash
# 1. Voice Input & Multilingual Intent Parser
python test_voice_input.py

# 2. Shopping List Manager & Auto-Categorization
python test_shopping_list.py

# 3. Voice-Activated Search Engine & Price Regex Parser
python test_voice_search.py

# 4. Smart Suggestions & Hugging Face API Engine
python test_suggestions.py
```
