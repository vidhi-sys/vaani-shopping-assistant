"""
Voice Input Module for Vaani Shopping Assistant.

This module provides end-to-end functionality to convert voice/audio input into
structured shopping list actions.

Pipeline Architecture:
1. Speech-to-Text (STT): OpenAI Whisper (whisper / faster-whisper) transcribes audio (.wav, .webm, bytes)
   into text and detects/accepts language ("en", "hi", etc.).
2. Intent Parsing (NLP): Classifies input text into one of ["add", "remove", "modify", "search"]
   using Sentence-Transformers embeddings (all-MiniLM-L6-v2) with TF-IDF + Cosine Similarity fallback.
3. Entity Extraction: Extracts item names from a product vocabulary list and detects numeric quantities
   in both English and Hindi.

Trade-offs & Design Choices:
- Sentence Embeddings vs Trained Classifier: Nearest-neighbor cosine similarity on pre-computed reference
  phrases is chosen over training a custom model due to zero required training data and instant extensibility.
- Vocabulary Keyword Matching vs Full NER: Lightweight keyword/phrase matching is used instead of a heavy NER
  model (like spaCy or BERT-NER) to keep memory usage minimal on free-tier or constrained edge devices.
"""

import re
import os
import tempfile
import logging
from typing import Dict, Any, Tuple, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vaani_voice_input")

# Standardized Intent Taxonomy
INTENTS = ["add", "remove", "modify", "search"]

# Reference Phrases for Intent Matching (Multilingual: English & Hindi)
REFERENCE_PHRASES: Dict[str, List[str]] = {
    "add": [
        # English
        "add milk to my shopping list",
        "i need to buy apples",
        "please add bananas",
        "put bread on the list",
        "i want apples",
        "buy two kilos of rice",
        "get some butter and cheese",
        "add soap to cart",
        "i need groceries",
        "include sugar in my list",
        # Hindi
        "दूध लिस्ट में जोड़ो",
        "मुझे सेब खरीदने हैं",
        "केला लिस्ट में डालो",
        "चावल जोड़ो",
        "सामान की सूची में मक्खन जोड़ो",
        "मुझे दो किलो आटा चाहिए",
        "चीनी खरीदना है",
    ],
    "remove": [
        # English
        "remove milk from my list",
        "delete bananas from shopping list",
        "take off apples",
        "cancel the bread order",
        "drop butter from cart",
        "remove item",
        "dont buy rice anymore",
        "clear sugar from my list",
        # Hindi
        "दूध लिस्ट से हटाओ",
        "केला लिस्ट से निकालो",
        "सेब हटा दो",
        "चावल मत खरीदना",
        "लिस्ट से चीनी मिटाओ",
        "मक्खन लिस्ट से डिलीट करो",
    ],
    "modify": [
        # English
        "change milk quantity to two",
        "update apples to 5 kilos",
        "modify quantity of bread to 3",
        "make bananas four instead of two",
        "increase sugar to two bags",
        "change amount of rice",
        # Hindi
        "दूध की मात्रा दो कर दो",
        "सेब की संख्या 5 बदलो",
        "केला दो के बजाय चार कर दो",
        "मात्रा बदलो",
        "चावल की मात्रा अपडेट करो",
    ],
    "search": [
        # English
        "search for olive oil",
        "do we have milk on the list",
        "find bananas",
        "check if apples are in the list",
        "look for bread",
        "is sugar in my cart",
        "show me items",
        # Hindi
        "क्या लिस्ट में दूध है",
        "सेब खोजो",
        "केला ढूंढो",
        "चेक करो मक्खन है या नहीं",
        "चावल सर्च करो",
    ],
}

# Product Vocabularies (English & Hindi)
PRODUCT_VOCABULARY: Dict[str, str] = {
    # English -> Standard Item Name
    "milk": "milk",
    "banana": "bananas",
    "bananas": "bananas",
    "apple": "apples",
    "apples": "apples",
    "bread": "bread",
    "butter": "butter",
    "cheese": "cheese",
    "egg": "eggs",
    "eggs": "eggs",
    "rice": "rice",
    "flour": "flour",
    "wheat": "wheat",
    "sugar": "sugar",
    "coffee": "coffee",
    "tea": "tea",
    "soap": "soap",
    "shampoo": "shampoo",
    "oil": "cooking oil",
    "cooking oil": "cooking oil",
    "olive oil": "olive oil",
    "potato": "potatoes",
    "potatoes": "potatoes",
    "tomato": "tomatoes",
    "tomatoes": "tomatoes",
    "onion": "onions",
    "onions": "onions",

    # Hindi -> Standard Item Name
    "दूध": "milk (दूध)",
    "केला": "bananas (केला)",
    "केले": "bananas (केला)",
    "सेब": "apples (सेब)",
    "ब्रेड": "bread (ब्रेड)",
    "मक्खन": "butter (मक्खन)",
    "पनीर": "cheese (पनीर)",
    "अंडा": "eggs (अंडे)",
    "अंडे": "eggs (अंडे)",
    "चावल": "rice (चावल)",
    "आटा": "flour (आटा)",
    "गेहूं": "wheat (गेहूं)",
    "चीनी": "sugar (चीनी)",
    "कॉफी": "coffee (कॉफी)",
    "चाय": "tea (चाय)",
    "साबुन": "soap (साबुन)",
    "शैम्पू": "shampoo (शैम्पू)",
    "तेल": "cooking oil (तेल)",
    "आलू": "potatoes (आलू)",
    "टमाटर": "tomatoes (टमाटर)",
    "प्याज़": "onions (प्याज़)",
    "प्याज": "onions (प्याज़)",
}

# English Number Words Mapping
ENGLISH_NUMBERS: Dict[str, int] = {
    "one": 1, "a": 1, "an": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "dozen": 12
}

# Hindi Number Words Mapping
HINDI_NUMBERS: Dict[str, int] = {
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5,
    "छह": 6, "छः": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10, "दर्जन": 12
}


class SpeechToTextTranscriber:
    """Handles speech-to-text audio transcription using OpenAI Whisper."""

    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper model settings.
        
        Args:
            model_size: Model variant ("tiny", "base", "small", "medium"). Defaults to "base".
        """
        self.model_size = model_size
        self.model = None
        self._is_loaded = False

    def load_model(self):
        """Lazy loader for the Whisper model to speed up initialization."""
        if not self._is_loaded:
            try:
                import whisper
                logger.info(f"Loading OpenAI Whisper model: '{self.model_size}'...")
                self.model = whisper.load_model(self.model_size)
                self._is_loaded = True
                logger.info("Whisper model loaded successfully.")
            except ImportError:
                logger.warning("OpenAI whisper package not found. Attempting faster-whisper fallback...")
                try:
                    from faster_whisper import WhisperModel
                    self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                    self._is_loaded = True
                    self.is_faster_whisper = True
                    logger.info("faster-whisper model loaded successfully.")
                except ImportError:
                    logger.error("Neither 'whisper' nor 'faster-whisper' packages are installed.")
                    self.model = None

    def transcribe(
        self, 
        audio_input: Any, 
        language: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Transcribes audio into text and returns (transcribed_text, detected_language).

        Args:
            audio_input: File path (str), audio bytes (bytes), or file-like object.
            language: Optional language code ("en", "hi", etc.). Defaults to auto-detect (None).

        Returns:
            Tuple[str, str]: (Transcribed text, Language code)
        """
        self.load_model()

        if self.model is None:
            logger.warning("Whisper model unavailable. Returning empty response.")
            return ("", language or "en")

        temp_filepath = None
        try:
            # If audio_input is raw bytes, write to a temporary audio file
            if isinstance(audio_input, bytes):
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                temp_file.write(audio_input)
                temp_file.close()
                temp_filepath = temp_file.name
                file_to_process = temp_filepath
            else:
                file_to_process = str(audio_input)

            if not os.path.exists(file_to_process):
                raise FileNotFoundError(f"Audio file not found: {file_to_process}")

            # Transcribe with Whisper
            if getattr(self, "is_faster_whisper", False):
                segments, info = self.model.transcribe(
                    file_to_process, 
                    language=language, 
                    beam_size=5
                )
                text = " ".join([segment.text for segment in segments]).strip()
                detected_lang = info.language
            else:
                kwargs = {}
                if language:
                    kwargs["language"] = language
                result = self.model.transcribe(file_to_process, **kwargs)
                text = result.get("text", "").strip()
                detected_lang = result.get("language", language or "en")

            return text, detected_lang

        except Exception as e:
            logger.error(f"Error during STT transcription: {e}")
            return "", language or "en"
        finally:
            if temp_filepath and os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except Exception:
                    pass


class IntentParser:
    """Parses transcribed text to extract Intent, Item, and Quantity."""

    def __init__(self):
        self.encoder = None
        self.vectorizer = None
        self.reference_matrix = None
        self.all_reference_texts = []
        self.all_reference_intents = []
        self._init_nlp()

    def _init_nlp(self):
        """Initializes SentenceTransformer or TF-IDF fallback matcher."""
        # Flat list of reference texts and intent labels
        for intent, phrases in REFERENCE_PHRASES.items():
            for phrase in phrases:
                self.all_reference_texts.append(phrase)
                self.all_reference_intents.append(intent)

        # Attempt to load SentenceTransformers
        try:
            from sentence_transformers import SentenceTransformer, util
            logger.info("Initializing SentenceTransformer (all-MiniLM-L6-v2)...")
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
            self.util = util
            self.encoded_references = self.encoder.encode(
                self.all_reference_texts, 
                convert_to_tensor=True
            )
            logger.info("SentenceTransformer intent model initialized successfully.")
        except Exception as e:
            logger.warning(f"SentenceTransformer not available ({e}). Falling back to TF-IDF Cosine Similarity.")
            self._init_tfidf_fallback()

    def _init_tfidf_fallback(self):
        """Fallback matching mechanism using scikit-learn TF-IDF Vectorizer."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2)).fit(self.all_reference_texts)
            self.reference_matrix = self.vectorizer.transform(self.all_reference_texts)
            self.cosine_similarity = cosine_similarity
            logger.info("TF-IDF Intent Matcher fallback initialized.")
        except ImportError:
            logger.warning("Scikit-learn not available. Basic keyword matching will be used for intents.")

    def parse_intent(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Classifies intent and extracts item & quantity from transcribed text.

        Args:
            text: Transcribed speech text.
            language: Language code ("en", "hi").

        Returns:
            Dict containing:
              - intent: one of ["add", "remove", "modify", "search"] or "unknown"
              - item: product name or None
              - quantity: integer (default 1)
              - confidence: float score (0.0 to 1.0)
              - status: "success" or "fallback" / "unrecognized"
        """
        clean_text = text.strip()
        if not clean_text:
            return {
                "status": "error",
                "error": "No speech text detected",
                "intent": "unknown",
                "item": None,
                "quantity": 1,
                "confidence": 0.0,
            }

        intent, confidence = self._classify_intent(clean_text)
        quantity = self._extract_quantity(clean_text)
        item = self._extract_item(clean_text)

        # Fallback handling for unrecognized inputs
        if confidence < 0.25 and item is None:
            return {
                "status": "unrecognized",
                "error": "Could not confidently understand shopping request",
                "raw_text": clean_text,
                "intent": "unknown",
                "item": None,
                "quantity": 1,
                "confidence": round(confidence, 3),
            }

        return {
            "status": "success",
            "raw_text": clean_text,
            "intent": intent,
            "item": item,
            "quantity": quantity,
            "confidence": round(confidence, 3),
            "language": language
        }

    def _classify_intent(self, text: str) -> Tuple[str, float]:
        """Classifies text into an intent category using Hugging Face Free API, embeddings, TF-IDF, or keyword heuristics."""
        # 0. Free Tier Cloud AI Service: Hugging Face Inference API (if HUGGINGFACE_API_KEY is provided)
        hf_token = os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_TOKEN")
        if hf_token:
            try:
                import urllib.request
                import json
                url = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
                headers = {"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
                payload = json.dumps({"inputs": {"source_sentence": text, "sentences": self.all_reference_texts}}).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as response:
                    scores = json.loads(response.read().decode("utf-8"))
                    if isinstance(scores, list) and len(scores) == len(self.all_reference_texts):
                        best_idx = scores.index(max(scores))
                        return self.all_reference_intents[best_idx], float(scores[best_idx])
            except Exception as e:
                logger.warning(f"Hugging Face Free API call skipped ({e}). Falling back to local embeddings/TF-IDF.")

        # 1. Sentence Transformers Embedding Cosine Similarity (Local)
        if self.encoder is not None:
            try:
                query_embedding = self.encoder.encode(text, convert_to_tensor=True)
                cosine_scores = self.util.cos_sim(query_embedding, self.encoded_references)[0]
                best_idx = int(cosine_scores.argmax())
                best_score = float(cosine_scores[best_idx])
                best_intent = self.all_reference_intents[best_idx]
                return best_intent, max(0.0, min(1.0, best_score))
            except Exception as e:
                logger.error(f"Error during SentenceTransformer inference: {e}")

        # 2. TF-IDF Fallback
        if self.vectorizer is not None and self.reference_matrix is not None:
            try:
                query_vec = self.vectorizer.transform([text])
                sims = self.cosine_similarity(query_vec, self.reference_matrix)[0]
                best_idx = int(sims.argmax())
                best_score = float(sims[best_idx])
                best_intent = self.all_reference_intents[best_idx]
                return best_intent, max(0.0, min(1.0, best_score))
            except Exception as e:
                logger.error(f"Error during TF-IDF inference: {e}")

        # 3. Rule-based keyword matching fallback
        lower_text = text.lower()
        if any(w in lower_text for w in ["add", "buy", "need", "put", "खरीदना", "जोड़ो", "डालो"]):
            return "add", 0.6
        if any(w in lower_text for w in ["remove", "delete", "cancel", "drop", "हटाओ", "निकालो"]):
            return "remove", 0.6
        if any(w in lower_text for w in ["change", "update", "modify", "मात्रा", "बदलो"]):
            return "modify", 0.6
        if any(w in lower_text for w in ["search", "find", "check", "खोजो", "ढूंढो"]):
            return "search", 0.6

        return "add", 0.3

    def _extract_item(self, text: str) -> Optional[str]:
        """Extracts product item name using product vocabulary matching and pattern parsing."""
        lower_text = text.lower()

        # Step A: Direct vocabulary search
        for key in sorted(PRODUCT_VOCABULARY.keys(), key=len, reverse=True):
            if key in lower_text or key in text:
                return PRODUCT_VOCABULARY[key]

        # Step B: Heuristic noun-phrase extraction (strip intent & quantity filler words)
        words_to_strip = [
            "add", "remove", "delete", "modify", "update", "search", "find", "buy", "need", "want",
            "to", "my", "shopping", "list", "cart", "please", "some", "the", "from", "for", "item",
            "quantity", "instead", "of", "kilos", "kilo", "kg", "grams", "packets", "bags",
            "जोड़ो", "हटाओ", "निकालो", "बदलो", "खोजो", "ढूंढो", "चाहिए", "खरीदना", "में", "से", "की", "लिस्ट", "सामान"
        ]
        
        # Remove numbers
        cleaned = re.sub(r'\b\d+\b', '', lower_text)
        for w in words_to_strip:
            cleaned = re.sub(r'\b' + re.escape(w) + r'\b', '', cleaned)
        
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned if len(cleaned) > 1 else None

    def _extract_quantity(self, text: str) -> int:
        """Extracts numeric quantity from text in English or Hindi."""
        # Check explicit digits (e.g., "5 apples", "2 kilos")
        digit_match = re.search(r'\b(\d+)\b', text)
        if digit_match:
            try:
                return int(digit_match.group(1))
            except ValueError:
                pass

        tokens = text.lower().split()
        
        # Check English number words
        for token in tokens:
            if token in ENGLISH_NUMBERS:
                return ENGLISH_NUMBERS[token]

        # Check Hindi number words
        for token in text.split():
            if token in HINDI_NUMBERS:
                return HINDI_NUMBERS[token]

        return 1


class VoiceInputPipeline:
    """Unified Facade for Voice Input processing (STT + Intent Parsing)."""

    def __init__(self, whisper_model_size: str = "base"):
        self.stt = SpeechToTextTranscriber(model_size=whisper_model_size)
        self.intent_parser = IntentParser()

    def process_audio(
        self, 
        audio_input: Any, 
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full Pipeline: Audio Blob/File -> Speech-to-Text -> Intent & Entity Parsing.

        Args:
            audio_input: Audio file path, byte payload, or blob.
            language: Optional language override ("en", "hi").

        Returns:
            Dict containing processing status, transcription, intent, item, quantity, language.
        """
        transcription, detected_lang = self.stt.transcribe(audio_input, language=language)
        
        if not transcription:
            return {
                "status": "error",
                "error": "No speech detected or empty audio",
                "transcription": "",
                "intent": "unknown",
                "item": None,
                "quantity": 1,
                "language": detected_lang
            }

        result = self.intent_parser.parse_intent(transcription, language=detected_lang)
        result["transcription"] = transcription
        return result

    def process_text(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Direct text input pipeline for fast testing and text-based commands."""
        result = self.intent_parser.parse_intent(text, language=language)
        result["transcription"] = text
        return result
