/**
 * Vaani Smart Store - Frontend SPA Controller
 * Handles Voice Recording, Speech Recognition, LocalStorage Persistence,
 * Categorized UI Rendering, Voice Catalog Search, and Smart Suggestions.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const micBtn = document.getElementById("mic-btn");
  const statusIndicator = document.getElementById("status-indicator");
  const statusText = document.getElementById("status-text");
  const transcriptText = document.getElementById("transcript-text");
  const categorizedList = document.getElementById("categorized-list");
  const emptyState = document.getElementById("empty-state");
  const itemCountBadge = document.getElementById("item-count");
  const clearListBtn = document.getElementById("clear-list-btn");
  const manualForm = document.getElementById("manual-add-form");
  const manualInput = document.getElementById("manual-item-input");
  const toastContainer = document.getElementById("toast-container");
  const hintChips = document.querySelectorAll(".chip");

  // Tab Elements
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  // Search Tab Elements
  const searchForm = document.getElementById("search-form");
  const searchInput = document.getElementById("search-input");
  const searchResultsList = document.getElementById("search-results-list");
  const filterChips = document.querySelectorAll(".filter-chip");

  // Suggestions Tab Elements
  const replenishmentContainer = document.getElementById("replenishment-container");
  const seasonalTitle = document.getElementById("seasonal-title");
  const seasonalTip = document.getElementById("seasonal-tip");
  const seasonalContainer = document.getElementById("seasonal-container");
  const substituteInput = document.getElementById("substitute-input");
  const findSubstituteBtn = document.getElementById("find-substitute-btn");
  const substituteResults = document.getElementById("substitute-results");

  // State
  let isRecording = false;
  let mediaRecorder = null;
  let audioChunks = [];
  let shoppingList = loadListFromStorage();

  // Category Display Names
  const CATEGORY_NAMES = {
    dairy: "Dairy & Cheese",
    produce: "Fresh Produce",
    bakery: "Bakery & Bread",
    beverages: "Beverages",
    snacks: "Snacks & Sweets",
    household: "Household Essentials",
    other: "Other Items"
  };

  // Initializations
  renderShoppingList();
  loadSuggestionsData();

  // -----------------------------------------------------------------
  // 1. Navigation Tab Switching
  // -----------------------------------------------------------------
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      
      tabBtns.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.add("hidden"));

      btn.classList.add("active");
      document.getElementById(targetTab).classList.remove("hidden");

      if (targetTab === "suggestions-tab") {
        loadSuggestionsData();
      }
    });
  });

  // -----------------------------------------------------------------
  // 2. Microphone Voice Control (MediaRecorder + WebSpeech Fallback)
  // -----------------------------------------------------------------
  micBtn.addEventListener("click", () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  });

  async function startRecording() {
    audioChunks = [];
    setUIState("listening", "Listening... Speak now");
    transcriptText.textContent = "Listening to your voice command...";

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
        await processAudioBlob(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      isRecording = true;
    } catch (err) {
      console.warn("Microphone access unavailable. Using browser speech fallback...", err);
      showToast("Mic access unavailable. Using browser speech recognition fallback.", "error");
      fallbackWebSpeech();
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    isRecording = false;
    setUIState("processing", "Processing voice input...");
  }

  async function processAudioBlob(blob) {
    const formData = new FormData();
    formData.append("file", blob, "recording.webm");

    try {
      const response = await fetch("/api/voice/process", {
        method: "POST",
        body: formData
      });

      if (!response.ok) throw new Error(`Server returned status ${response.status}`);

      const result = await response.json();
      handleVoiceResult(result);
    } catch (err) {
      fallbackWebSpeech();
    }
  }

  // Web Speech API Fallback
  function fallbackWebSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      showToast("Speech Recognition not supported in this browser.", "error");
      setUIState("idle", "Tap mic to speak");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;

    recognition.onstart = () => {
      setUIState("listening", "Listening (Browser Speech)...");
    };

    recognition.onresult = async (event) => {
      const text = event.results[0][0].transcript;
      transcriptText.textContent = `"${text}"`;
      setUIState("processing", "Parsing intent...");

      try {
        const res = await fetch("/api/voice/parse-text", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: text })
        });
        const data = await res.json();
        handleVoiceResult(data);
      } catch (err) {
        handleLocalTextParse(text);
      }
    };

    recognition.onerror = () => {
      showToast("Didn't catch that, please try again.", "error");
      setUIState("idle", "Tap mic to speak");
    };

    recognition.onend = () => {
      if (isRecording) setUIState("idle", "Tap mic to speak");
      isRecording = false;
    };

    recognition.start();
    isRecording = true;
  }

  // Handle Structured Voice Action Response
  function handleVoiceResult(result) {
    setUIState("idle", "Tap mic to speak");

    const text = result.transcription || result.raw_text || "";
    transcriptText.textContent = text ? `"${text}"` : "No speech detected";

    if (result.status === "error" || !result.intent || result.intent === "unknown") {
      showToast(result.error || "Didn't understand command, try again.", "error");
      return;
    }

    const intent = result.intent;
    const item = result.item;
    const qty = result.quantity || 1;

    if (intent === "add" && item) {
      addShoppingItem(item, qty);
      let msg = `✓ Added ${qty} ${item} to list`;
      if (result.smart_suggestions && result.smart_suggestions.substitutes.length > 0) {
        msg += ` (Try ${result.smart_suggestions.substitutes[0]})`;
      }
      showToast(msg, "success");
    } else if (intent === "remove" && item) {
      removeShoppingItemByName(item);
      showToast(`✓ Removed ${item} from list`, "info");
    } else if (intent === "modify" && item) {
      modifyShoppingItemQuantity(item, qty);
      showToast(`✓ Updated ${item} quantity to ${qty}`, "info");
    } else if (intent === "search") {
      // Switch to Search tab and execute search query
      switchTab("search-tab");
      searchInput.value = text;
      executeSearch(text);
    } else {
      showToast("Unrecognized action, please rephrase.", "error");
    }
  }

  function handleLocalTextParse(text) {
    setUIState("idle", "Tap mic to speak");
    const lower = text.toLowerCase();
    
    if (lower.includes("add") || lower.includes("buy") || lower.includes("need")) {
      const cleaned = lower.replace(/add|buy|need|to|my|shopping|list|please|some/g, "").trim();
      if (cleaned) {
        addShoppingItem(cleaned, 1);
        showToast(`✓ Added 1 ${cleaned} to list`, "success");
      }
    } else if (lower.includes("search") || lower.includes("find")) {
      switchTab("search-tab");
      searchInput.value = text;
      executeSearch(text);
    } else {
      showToast(`Command parsed: "${text}"`, "info");
    }
  }

  function switchTab(tabId) {
    tabBtns.forEach(b => b.classList.remove("active"));
    tabContents.forEach(c => c.classList.add("hidden"));
    
    const targetBtn = Array.from(tabBtns).find(b => b.getAttribute("data-tab") === tabId);
    if (targetBtn) targetBtn.classList.add("active");
    document.getElementById(tabId).classList.remove("hidden");
  }

  // -----------------------------------------------------------------
  // 3. Shopping List Core & LocalStorage Persistence
  // -----------------------------------------------------------------
  function loadListFromStorage() {
    try {
      const saved = localStorage.getItem("vaani_shopping_list");
      return saved ? JSON.parse(saved) : [];
    } catch (e) { return []; }
  }

  function saveListToStorage() {
    try {
      localStorage.setItem("vaani_shopping_list", JSON.stringify(shoppingList));
    } catch (e) {}
  }

  function addShoppingItem(name, qty = 1) {
    const cleanName = name.trim();
    if (!cleanName) return;

    const existing = shoppingList.find(i => i.item.toLowerCase() === cleanName.toLowerCase());
    if (existing) {
      existing.quantity += qty;
    } else {
      shoppingList.push({
        id: Date.now().toString(),
        item: cleanName.charAt(0).toUpperCase() + cleanName.slice(1),
        quantity: qty,
        category: autoCategorize(cleanName),
        addedAt: new Date().toISOString()
      });
    }

    saveListToStorage();
    renderShoppingList();
  }

  function removeShoppingItem(id) {
    shoppingList = shoppingList.filter(i => i.id !== id);
    saveListToStorage();
    renderShoppingList();
  }

  function removeShoppingItemByName(name) {
    const clean = name.trim().toLowerCase();
    shoppingList = shoppingList.filter(i => !i.item.toLowerCase().includes(clean));
    saveListToStorage();
    renderShoppingList();
  }

  function modifyShoppingItemQuantity(name, newQty) {
    const clean = name.trim().toLowerCase();
    const target = shoppingList.find(i => i.item.toLowerCase().includes(clean));
    if (target) {
      if (newQty <= 0) {
        removeShoppingItem(target.id);
      } else {
        target.quantity = newQty;
        saveListToStorage();
        renderShoppingList();
      }
    }
  }

  function autoCategorize(name) {
    const n = name.toLowerCase();
    if (/milk|doodh|butter|cheese|yogurt|dahi|paneer|cream|ghee/.test(n)) return "dairy";
    if (/apple|banana|potato|tomato|onion|spinach|orange|lemon|fruit|vegetable/.test(n)) return "produce";
    if (/bread|bun|bagel|cake|muffin|toast/.test(n)) return "bakery";
    if (/coffee|tea|chai|juice|soda|water|beverage/.test(n)) return "beverages";
    if (/chip|biscuit|cookie|chocolate|snack|popcorn|nut/.test(n)) return "snacks";
    if (/soap|shampoo|detergent|tissue|paper|toothpaste|cleaner/.test(n)) return "household";
    return "other";
  }

  function renderShoppingList() {
    categorizedList.innerHTML = "";
    itemCountBadge.textContent = shoppingList.length;

    if (shoppingList.length === 0) {
      emptyState.classList.remove("hidden");
      return;
    } else {
      emptyState.classList.add("hidden");
    }

    const groups = {};
    shoppingList.forEach(item => {
      const cat = item.category || "other";
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(item);
    });

    Object.keys(groups).forEach(catKey => {
      const items = groups[catKey];
      const groupEl = document.createElement("div");
      groupEl.className = "category-group";

      const catTitle = CATEGORY_NAMES[catKey] || "Other Items";
      groupEl.innerHTML = `
        <div class="category-header">
          <span class="cat-dot ${catKey}"></span>
          <span>${catTitle} (${items.length})</span>
        </div>
        <ul class="item-list"></ul>
      `;

      const ul = groupEl.querySelector("ul");
      items.forEach(item => {
        const li = document.createElement("li");
        li.className = "item-row";
        li.innerHTML = `
          <div class="item-details">
            <span class="item-name">${item.item}</span>
            <span class="item-qty">x${item.quantity}</span>
          </div>
          <button class="remove-btn" title="Remove Item">&times;</button>
        `;

        li.querySelector(".remove-btn").addEventListener("click", () => {
          removeShoppingItem(item.id);
          showToast(`Removed ${item.item}`, "info");
        });

        ul.appendChild(li);
      });

      categorizedList.appendChild(groupEl);
    });
  }

  // Clear All
  clearListBtn.addEventListener("click", () => {
    if (shoppingList.length === 0) return;
    if (confirm("Clear all items from your shopping list?")) {
      shoppingList = [];
      saveListToStorage();
      renderShoppingList();
      showToast("Shopping list cleared.", "info");
    }
  });

  // Manual Input Form
  manualForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const val = manualInput.value.trim();
    if (val) {
      addShoppingItem(val, 1);
      showToast(`✓ Added ${val} to list`, "success");
      manualInput.value = "";
    }
  });

  // Hint Chips
  hintChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const phrase = chip.getAttribute("data-phrase");
      transcriptText.textContent = `"${phrase}"`;
      handleLocalTextParse(phrase);
    });
  });

  // -----------------------------------------------------------------
  // 4. Voice Search & Catalog Query
  // -----------------------------------------------------------------
  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = searchInput.value.trim();
    if (query) executeSearch(query);
  });

  filterChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-query");
      searchInput.value = q;
      executeSearch(q);
    });
  });

  async function executeSearch(query) {
    searchResultsList.innerHTML = `<p style="padding: 12px; text-align: center; color: var(--text-muted);">Searching catalog...</p>`;

    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      renderSearchResults(data);
    } catch (err) {
      searchResultsList.innerHTML = `<p style="padding: 12px; text-align: center; color: var(--store-red);">Search offline. Check server connection.</p>`;
    }
  }

  function renderSearchResults(data) {
    searchResultsList.innerHTML = "";

    if (data.status === "no_results" || !data.results || data.results.length === 0) {
      searchResultsList.innerHTML = `<p style="padding: 16px; text-align: center; color: var(--text-muted);">${data.message || "No matching products found."}</p>`;
      return;
    }

    data.results.forEach(prod => {
      const card = document.createElement("div");
      card.className = "search-result-card";
      card.innerHTML = `
        <div>
          <strong>${prod.name}</strong> (${prod.brand})
          <br><small style="color: var(--text-muted);">${prod.size} &bull; ${prod.category}</small>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
          <span class="product-price">$${prod.price.toFixed(2)}</span>
          <button class="btn-primary" style="padding: 6px 12px; font-size: 0.8rem;">+ Add</button>
        </div>
      `;

      card.querySelector("button").addEventListener("click", () => {
        addShoppingItem(prod.name, 1);
        showToast(`✓ Added ${prod.name} to shopping list`, "success");
      });

      searchResultsList.appendChild(card);
    });
  }

  // -----------------------------------------------------------------
  // 5. Smart Suggestions Tab Loader
  // -----------------------------------------------------------------
  async function loadSuggestionsData() {
    // 1. Load Seasonal Produce
    try {
      const sRes = await fetch("/api/suggestions/seasonal");
      const sData = await sRes.json();
      if (sData.status === "success") {
        seasonalTitle.textContent = `${sData.title} (${sData.season.toUpperCase()})`;
        seasonalTip.textContent = sData.tip;
        
        seasonalContainer.innerHTML = "";
        sData.items.forEach(item => {
          const chip = document.createElement("button");
          chip.className = "seasonal-chip";
          chip.textContent = `+ ${item}`;
          chip.addEventListener("click", () => {
            addShoppingItem(item, 1);
            showToast(`✓ Added ${item} to list`, "success");
          });
          seasonalContainer.appendChild(chip);
        });
      }
    } catch (e) {}

    // 2. Load Replenishment Recommendations based on local history
    if (shoppingList.length > 0) {
      const mockHistory = shoppingList.map(item => ({
        item: item.item,
        last_purchased_days_ago: 7,
        cycle_days: 5
      }));

      try {
        const rRes = await fetch("/api/suggestions/recommendations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ history: mockHistory })
        });
        const rData = await rRes.json();
        
        if (rData.recommendations && rData.recommendations.length > 0) {
          replenishmentContainer.innerHTML = "";
          rData.recommendations.forEach(r => {
            const itemDiv = document.createElement("div");
            itemDiv.className = "suggestion-item";
            itemDiv.innerHTML = `
              <div>
                <strong>${r.item.toUpperCase()}</strong>
                <br><small style="color: var(--text-muted);">${r.recommendation}</small>
              </div>
              <button class="btn-primary" style="padding: 4px 10px; font-size: 0.75rem;">+ Restock</button>
            `;

            itemDiv.querySelector("button").addEventListener("click", () => {
              addShoppingItem(r.item, 1);
              showToast(`✓ Restocked ${r.item}`, "success");
            });

            replenishmentContainer.appendChild(itemDiv);
          });
        } else {
          replenishmentContainer.innerHTML = `<p style="font-size: 0.85rem; color: var(--text-muted);">All items in stock!</p>`;
        }
      } catch (e) {}
    } else {
      replenishmentContainer.innerHTML = `<p style="font-size: 0.85rem; color: var(--text-muted);">Add items to your list to get automatic restock predictions.</p>`;
    }
  }

  // Find Substitutes
  findSubstituteBtn.addEventListener("click", async () => {
    const val = substituteInput.value.trim();
    if (!val) return;

    substituteResults.textContent = "Searching healthy alternatives...";
    try {
      const res = await fetch("/api/suggestions/substitutes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item: val })
      });
      const data = await res.json();
      if (data.substitutes && data.substitutes.length > 0) {
        substituteResults.innerHTML = `
          <strong>Alternatives for ${data.item}:</strong>
          <br>${data.substitutes.join(", ")}
          <br><small style="color: var(--text-muted);">${data.reason}</small>
        `;
      } else {
        substituteResults.textContent = `No specific substitutes found for ${val}.`;
      }
    } catch (e) {
      substituteResults.textContent = "Error fetching substitutes.";
    }
  });

  // -----------------------------------------------------------------
  // 6. UI Helpers & Toast System
  // -----------------------------------------------------------------
  function setUIState(state, text) {
    statusIndicator.className = `status-badge state-${state}`;
    statusText.textContent = text;
    micBtn.className = `mic-btn state-${state}`;
  }

  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }
});
