<p align="center">
  <img src="static/logo.png" alt="Vaani Smart Store Logo" width="220" />
</p>

<h1 align="center">Vaani - Smart Voice Store 🎙️🛒</h1>

<p align="center">
  <b>Multilingual Voice-Powered Shopping Assistant, Smart Search & AI Recommendation Platform</b>
  <b>Voice Commanding Project </b>
</p>

<p align="center">
  <a href="https://github.com/vidhi-sys/vaani-shopping-assistant"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" /></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" /></a>
  <a href="https://openai.com/research/whisper"><img src="https://img.shields.io/badge/OpenAI-Whisper_STT-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI Whisper" /></a>
  <a href="https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2"><img src="https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="HuggingFace" /></a>
  <a href="https://github.com/vidhi-sys/vaani-shopping-assistant/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License" /></a>
  <a href="https://vercel.com/"><img src="https://img.shields.io/badge/Vercel-Deployment-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Vercel" /></a>
</p>

<p align="center">
  <a href="#-quick-start-">Quick Start</a> •
  <a href="#-how-it-works">How It Works</a> •
  <a href="#-system-architecture">Architecture</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-api-specification">API Reference</a> •
  <a href="#-free-tier-cloud-deployment">Deployment</a>
</p>

---

## 💡 Overview & Vision

**Vaani** (*हिंदी: वाणी - Voice*) is an end-to-end open-source, voice-first shopping assistant designed to simplify grocery management and ecommerce interaction. 

Built with an **API-first, modular architecture**, Vaani converts spoken commands in **English** and **Hindi** into structured shopping list actions (`intent`, `item`, `quantity`, `category`), executes voice search with regex-extracted price bounds (*"under $5"*, *"between $3 and $8"*), and provides automated AI product replenishment and substitute recommendations.

### 🌟 Core Philosophy & Design Principles
- **Voice-First Simplicity**: Real-time microphone audio processing with live transcript feedback.
- **Decoupled Architecture**: Speech-to-Text, NLP Intent Parsing, List Management, and Product Search operate as independent, reusable micro-modules.
- **Zero-Latency Offline Fallback**: Features local Sentence Transformer embeddings (`all-MiniLM-L6-v2`) and TF-IDF matching that function 100% offline without mandatory paid API subscriptions.
- **Bi-Directional Multilingual Engine**: Built-in support for English and Hindi voice commands and produce vocabularies.
- **100% Free-Tier Cloud Deployment**: Designed to run cost-free on Vercel, Netlify, Render, GCP Cloud Run, or AWS.

---

## 📊 Tech Stack & Frameworks Used

| Domain | Technologies & Frameworks | Description |
| :--- | :--- | :--- |
| **Backend Engine** | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) ![Uvicorn](https://img.shields.io/badge/Uvicorn-4051B5?style=flat-square) | High-performance asynchronous Python web server handling REST endpoints and static file delivery. |
| **Speech Recognition** | ![OpenAI Whisper](https://img.shields.io/badge/OpenAI_Whisper-412991?style=flat-square&logo=openai&logoColor=white) ![FFmpeg](https://img.shields.io/badge/FFmpeg-0078D7?style=flat-square&logo=ffmpeg&logoColor=white) | Server-side Speech-to-Text engine (`base`/`small` models) for `.webm` and `.wav` audio transcription. |
| **NLP & Intent Embeddings** | ![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white) ![HuggingFace](https://img.shields.io/badge/SentenceTransformers-FFD21E?style=flat-square&logo=huggingface&logoColor=black) ![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat-square&logo=scikit-learn&logoColor=white) | Cosine similarity semantic matching (`all-MiniLM-L6-v2`) with automatic TF-IDF vectorizer fallback. |
| **Frontend Web SPA** | ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white) ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white) ![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=flat-square&logo=javascript&logoColor=black) | Mobile-first SPA featuring MediaRecorder audio capture, tabbed navigation, and Web Speech API fallback. |
| **State & Persistence** | ![LocalStorage](https://img.shields.io/badge/Browser_LocalStorage-4285F4?style=flat-square) | Client-side offline synchronization for shopping list state across reloads. |
| **Cloud & Deployment** | ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white) ![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white) ![Render](https://img.shields.io/badge/Render-46E3B7?style=flat-square) ![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=flat-square&logo=firebase&logoColor=black) | Production deployment configs for Docker, Vercel, Netlify, Render, GCP Cloud Run, and Firebase Hosting. |

---

## ⚙️ How It Works (Pipeline Architecture)

```
                    +------------------------------------------+
                    |  Audio Command (.webm/.wav Audio Blob)   |
                    +--------------------+---------------------+
                                         |
                                         v
                    +------------------------------------------+
                    |        SpeechToTextTranscriber           |
                    |        OpenAI Whisper STT Engine         |
                    +--------------------+---------------------+
                                         | Transcribed Text & Language
                                         v
                    +------------------------------------------+
                    |               IntentParser               |
                    |  - Sentence Transformers Similarity      |
                    |  - TF-IDF Cosine Matcher (Fallback)      |
                    |  - Spoken Quantity Parser ("two" -> 2)   |
                    |  - Item Vocabulary & Pattern Extractor   |
                    +--------------------+---------------------+
                                         | Structured Object: { intent, item, quantity }
                                         v
          +------------------------------+------------------------------+
          |                              |                              |
          v                              v                              v
+-------------------+          +-------------------+          +-------------------+
| Shopping List     |          | Voice Search      |          | Smart Suggestions |
| Engine            |          | Engine            |          | Engine            |
| - Auto-Category   |          | - Regex Price Bounds         | - Restock Frequency|
| - Qty Increment   |          | - Catalog Ranking |          | - Seasonal Produce|
| - Fuzzy Removal   |          | - Filter Bounds   |          | - Product Alternatives
+-------------------+          +-------------------+          +-------------------+
```

### Detailed Pipeline Breakdown

1. **Audio Ingestion & STT (`voice_input.py`)**:
   - Accepts microphone audio blobs from the browser UI via `/api/voice/process`.
   - Transcribes audio into text using OpenAI Whisper and identifies spoken language (`"en"`, `"hi"`).

2. **Semantic Intent Classification**:
   - Computes cosine similarity scores against reference phrases for intents: `["add", "remove", "modify", "search"]`.
   - Primary NLP matcher: `sentence-transformers/all-MiniLM-L6-v2`.
   - Fallback NLP matcher: `scikit-learn` TF-IDF vectorizer + cosine similarity matrix.

3. **Entity & Quantity Extraction**:
   - **Quantity Parsing**: Converts numeric strings ("3"), English number words ("two", "a couple of" $\rightarrow 2$, "a dozen" $\rightarrow 12$), and Hindi number words ("दो", "तीन", "पांच").
   - **Product Extraction**: Keyword dictionary lookup against multilingual vocabulary list + pattern residue stripping.

4. **Shopping List Operations (`shopping_list.py`)**:
   - `add_item`: If item exists (case-insensitive match), increments quantity instead of duplicating.
   - `remove_item`: Performs fuzzy substring removal (e.g. *"milk"* removes *"Milk 2%"*).
   - `auto_categorize`: Maps items to `Dairy`, `Produce`, `Bakery`, `Beverages`, `Snacks`, `Household`, or `Other`.

5. **Voice-Activated Search (`voice_search.py`)**:
   - Parses regex price constraints: *"under $5"*, *"less than 10 dollars"*, *"between 3 and 8 dollars"*.
   - Ranks catalog products (`catalog.json`) based on relevance score (Exact Name > Brand Match > Partial Match).

---

## 🎨 Category System & Color Scheme

Vaani uses a visual color-coded badge system for category classification:

| Category Badge | Color Code | Included Products & Keywords |
| :--- | :--- | :--- |
| 🔵 **Dairy & Cheese** | `#2563eb` | Whole Milk, Almond Milk, Butter, Cheese, Yogurt, Dahi, Paneer, Ghee |
| 🟢 **Fresh Produce** | `#16a34a` | Apples, Bananas, Potatoes, Tomatoes, Onions, Spinach, Oranges, Lemons, Ginger |
| 🟠 **Bakery & Bread** | `#d97706` | Whole Wheat Bread, Sourdough Loaf, Bagels, Buns, Muffins, Toast |
| 🟣 **Beverages** | `#9333ea` | Cold Brew Coffee Concentrates, Green Tea Bags, Sparkling Water, Orange Juice |
| 💗 **Snacks & Sweets** | `#db2777` | Potato Chips, Dark Chocolate, Roasted Almonds, Cookies, Namkeen |
| 🩵 **Household Essentials**| `#0d9488` | Dish Soap, Laundry Detergent, Paper Towels, Toothpaste, Cleaners |
| 🩶 **Other Items** | `#475569` | Uncategorized pantry items, general store goods |

---

## 🌐 Multilingual Support Matrix

Vaani natively processes bilingual queries in **English** and **Hindi**:

```
+------------------------------------+------------------------------------+
|          English Command           |           Hindi Command            |
+------------------------------------+------------------------------------+
| "Add 2 liters of milk to my list"  | "दूध लिस्ट में जोड़ो"              |
| "Remove bananas from shopping list"| "केला लिस्ट से निकालो"             |
| "Change milk quantity to two"      | "दूध की मात्रा दो कर दो"           |
| "Search organic apples under $5"   | "क्या लिस्ट में मक्खन है"           |
+------------------------------------+------------------------------------+
```

---

## 🔌 API Specification & REST Endpoints

### 🎙️ Voice Processing API
```http
POST /api/voice/process
Content-Type: multipart/form-data

file: <audio_file_blob> (.webm / .wav)
language: "en" (optional)
```
**Response Output (`200 OK`)**:
```json
{
  "status": "success",
  "transcription": "Add two kilos of apples to my list",
  "intent": "add",
  "item": "apples",
  "quantity": 2,
  "confidence": 0.892,
  "language": "en",
  "list_action": {
    "action": "added",
    "item": { "id": "a1b2c3d4", "item": "Apples", "quantity": 2, "category": "produce" }
  },
  "smart_suggestions": {
    "substitutes": ["organic apples", "green apples"],
    "tip": "Fresh produce item."
  }
}
```

```http
POST /api/voice/parse-text
Content-Type: application/json

{
  "text": "Add 2 milk to my shopping list",
  "language": "en"
}
```

---

### 🛒 Shopping List Management API

| Endpoint | Method | Description | Payload Example |
| :--- | :--- | :--- | :--- |
| `/api/list/items` | `GET` | Retrieve active shopping list | None |
| `/api/list/add` | `POST` | Add or increment item quantity | `{"item": "Bread", "quantity": 2}` |
| `/api/list/remove` | `POST` | Fuzzy remove item by name | `{"item": "Bread"}` |
| `/api/list/modify` | `POST` | Modify existing item quantity | `{"item": "Bread", "quantity": 5}` |

---

### 🔍 Voice Search & Catalog API

```http
GET /api/search?q=organic+milk+under+$5
```
**Response Output (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Found 1 matching products.",
  "query": "organic milk under $5",
  "filters": { "min_price": null, "max_price": 5.0 },
  "count": 1,
  "results": [
    {
      "id": "p02",
      "name": "Almond Breeze Unsweetened Milk",
      "brand": "Blue Diamond",
      "category": "dairy",
      "price": 3.99,
      "size": "64 oz"
    }
  ]
}
```

---

### 💡 Smart Suggestions API

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/suggestions/recommendations` | `POST` | Product replenishment prediction alerts based on purchase history |
| `/api/suggestions/seasonal` | `GET` | In-season produce recommendations (e.g. `?month=6`) |
| `/api/suggestions/substitutes` | `POST` | Healthy & dietary product alternatives lookup |

---

## 🚀 Quick Start & Installation

### Prerequisites
- **Python**: 3.10 or higher
- **FFmpeg**: Required by OpenAI Whisper for audio format decoding.

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone https://github.com/vidhi-sys/vaani-shopping-assistant.git
cd vaani-shopping-assistant

python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

> **FFmpeg Installation Guide**:
> - **Windows**: `winget install ffmpeg` or `choco install ffmpeg`
> - **macOS**: `brew install ffmpeg`
> - **Linux**: `sudo apt update && sudo apt install -y ffmpeg`

### Step 3: Run Development Server
```bash
uvicorn app:app --reload --port 8000
```
Open **`http://localhost:8000`** in your browser to launch the Vaani web interface!

---

## 🧪 Automated Test Suite

Vaani includes a robust automated test harness covering intent classification, list management, search regex, and suggestions:

```bash
# Test 1: Voice STT & Multilingual Intent Classifier
python test_voice_input.py

# Test 2: Shopping List Manager & Auto-Categorizer
python test_shopping_list.py

# Test 3: Voice Search Engine & Price Regex Parser
python test_voice_search.py

# Test 4: Smart Suggestions Engine
python test_suggestions.py
```

---

## ☁️ Free-Tier Cloud Deployment Guide

### 1. Vercel / Netlify (Frontend SPA - 100% Free)
> **Note on Browser Microphone Permissions**: Browsers require an **HTTPS URL** to grant microphone access (`navigator.mediaDevices.getUserMedia`). Vercel and Netlify issue automatic SSL certificates free of charge.

- **Vercel**: Connect repo `vidhi-sys/vaani-shopping-assistant` $\rightarrow$ Set Framework to *Other* $\rightarrow$ Set Publish Directory to `static`.
- **Netlify**: Connect repo $\rightarrow$ Set Build Directory to `static`.

### 2. Render.com / GCP Cloud Run (Backend API Engine)
- **Render.com**: Create Free Web Service $\rightarrow$ Build Command: `pip install -r requirements.txt` $\rightarrow$ Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
- **Docker / GCP Cloud Run**: Use the included [`Dockerfile`](Dockerfile) or [`app.yaml`](app.yaml):
  ```bash
  gcloud run deploy vaani-assistant --source . --region us-central1 --allow-unauthenticated
  ```

---

## 📄 License & Community

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

Developed with 🧡 for the open-source voice AI community. Contributions, issues, and feature requests are welcome!
