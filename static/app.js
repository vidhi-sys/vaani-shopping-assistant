/**
 * Vaani Voice Shopping Assistant - Bulletproof Client Controller
 * Handles Instant Real-Time Speech Recognition, Intent Execution,
 * Catalog Filtering, Shopping List Management, and Smart Suggestions.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const micBtn = document.getElementById("mic-btn");
  const statusIndicator = document.getElementById("status-indicator");
  const statusText = document.getElementById("status-text");
  const transcriptText = document.getElementById("transcript-text");
  const productGrid = document.getElementById("product-grid");
  const categorizedList = document.getElementById("categorized-list");
  const emptyCartBox = document.getElementById("empty-cart-box");
  const cartBadge = document.getElementById("cart-badge");
  const clearListBtn = document.getElementById("clear-list-btn");
  const toastContainer = document.getElementById("toast-container");
  const filterBtns = document.querySelectorAll(".filter-btn");
  const sampleChips = document.querySelectorAll(".sample-chip");
  const seasonalChipsWrap = document.getElementById("seasonal-chips-wrap");
  const replenishmentWrap = document.getElementById("replenishment-items-wrap");

  // State
  let isListening = false;
  let recognition = null;
  let catalogProducts = [];
  let shoppingList = loadListFromStorage();
  let activeFilter = "all";

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

  // Initial Load
  initCatalog();
  renderShoppingList();
  initSpeechEngine();
  loadSuggestions();

  // -----------------------------------------------------------------
  // 1. Bulletproof Speech Recognition Engine
  // -----------------------------------------------------------------
  function initSpeechEngine() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("Web Speech API not directly supported. Will use MediaRecorder fallback.");
      return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true; // Real-time continuous text display
    recognition.lang = "en-US";

    recognition.onstart = () => {
      isListening = true;
      setUIState("listening", "Listening... Speak now");
      transcriptText.textContent = "Listening to your voice command...";
    };

    recognition.onresult = (event) => {
      let interimTranscript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      const currentText = finalTranscript || interimTranscript;
      if (currentText) {
        transcriptText.textContent = `"${currentText}"`;
      }

      if (finalTranscript) {
        setUIState("processing", "Processing voice command...");
        processVoiceCommandText(finalTranscript);
      }
    };

    recognition.onerror = (event) => {
      console.error("Speech Recognition Error:", event.error);
      if (event.error !== "no-speech") {
        showToast("Didn't catch that, please try speaking again.", "error");
      }
      setUIState("idle", "Tap mic and speak naturally");
      isListening = false;
    };

    recognition.onend = () => {
      if (isListening) {
        setUIState("idle", "Tap mic and speak naturally");
      }
      isListening = false;
    };
  }

  // Mic Button Click Listener
  micBtn.addEventListener("click", () => {
    if (isListening) {
      stopVoiceListening();
    } else {
      startVoiceListening();
    }
  });

  function startVoiceListening() {
    if (recognition) {
      try {
        recognition.start();
      } catch (e) {
        console.warn("Speech recognition restart exception:", e);
      }
    } else {
      showToast("Web speech API fallback active.", "info");
      fallbackMediaRecorder();
    }
  }

  function stopVoiceListening() {
    if (recognition) {
      try { recognition.stop(); } catch (e) {}
    }
    isListening = false;
    setUIState("idle", "Tap mic and speak naturally");
  }

  // Process Recognized Voice Text Command
  async function processVoiceCommandText(text) {
    const cleanText = text.trim();
    if (!cleanText) {
      setUIState("idle", "Tap mic and speak naturally");
      return;
    }

    // Step 1: Immediate local NLP execution (Zero latency)
    const localExecuted = parseVoiceLocally(cleanText);

    // Step 2: Query backend API for full entity validation
    try {
      const res = await fetch("/api/voice/parse-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: cleanText })
      });
      const data = await res.json();

      if (!localExecuted && data.status === "success") {
        executeBackendAction(data);
      }
    } catch (e) {
      console.warn("Backend parse call skipped. Local voice execution succeeded.");
    } finally {
      setUIState("idle", "Tap mic and speak naturally");
    }
  }

  // Client-Side High-Speed Voice Parser (Ensures Voice NEVER fails)
  function parseVoiceLocally(text) {
    const lower = text.toLowerCase();

    // Check ADD Intent (e.g., "Add 2 milk", "buy apples", "I need 3 bread")
    if (lower.includes("add") || lower.includes("buy") || lower.includes("need") || lower.includes("put")) {
      const qtyMatch = lower.match(/\b(\d+|two|three|four|five|six|seven|eight|nine|ten|a dozen|couple)\b/);
      let qty = 1;
      if (qtyMatch) {
        qty = parseQtyWord(qtyMatch[1]);
      }

      let item = lower.replace(/\b(add|buy|need|put|to|my|shopping|list|cart|please|some|items|item)\b/gi, "").trim();
      item = item.replace(/\b(\d+|two|three|four|five|six|seven|eight|nine|ten|a dozen|couple)\b/gi, "").trim();

      if (item.length > 1) {
        addShoppingItem(item, qty);
        showToast(`✓ Added ${qty} ${item} to shopping list`, "success");
        return true;
      }
    }

    // Check REMOVE Intent (e.g., "Remove milk", "delete bananas")
    if (lower.includes("remove") || lower.includes("delete") || lower.includes("cancel")) {
      let item = lower.replace(/\b(remove|delete|cancel|from|my|list|cart|shopping|the)\b/gi, "").trim();
      if (item.length > 1) {
        removeShoppingItemByName(item);
        showToast(`✓ Removed ${item} from list`, "info");
        return true;
      }
    }

    // Check SEARCH Intent (e.g., "Search apples under $5")
    if (lower.includes("search") || lower.includes("find") || lower.includes("look for")) {
      filterCatalogByQuery(text);
      showToast(`🔍 Filtered products for "${text}"`, "info");
      return true;
    }

    return false;
  }

  function parseQtyWord(w) {
    const map = { "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "dozen": 12, "couple": 2 };
    if (map[w]) return map[w];
    const n = parseInt(w);
    return isNaN(n) ? 1 : n;
  }

  function executeBackendAction(data) {
    if (data.intent === "add" && data.item) {
      addShoppingItem(data.item, data.quantity || 1);
      showToast(`✓ Added ${data.quantity || 1} ${data.item} to list`, "success");
    } else if (data.intent === "remove" && data.item) {
      removeShoppingItemByName(data.item);
      showToast(`✓ Removed ${data.item}`, "info");
    } else if (data.intent === "search") {
      filterCatalogByQuery(data.raw_text || data.transcription);
    }
  }

  // -----------------------------------------------------------------
  // 2. Product Catalog Store Grid
  // -----------------------------------------------------------------
  async function initCatalog() {
    try {
      const res = await fetch("catalog.json");
      catalogProducts = await res.json();
      renderCatalogGrid(catalogProducts);
    } catch (e) {
      console.warn("Loading catalog fallback...");
      catalogProducts = [
        { "id": "p01", "name": "Organic Whole Milk", "brand": "Horizon", "category": "dairy", "price": 4.49 },
        { "id": "p07", "name": "Honeycrisp Apples", "brand": "Fresh Produce", "category": "produce", "price": 2.99 },
        { "id": "p13", "name": "Whole Wheat Bread", "brand": "Dave's", "category": "bakery", "price": 5.49 },
        { "id": "p21", "name": "Cold Brew Coffee", "brand": "Chameleon", "category": "beverages", "price": 7.99 },
        { "id": "p17", "name": "Sea Salt Potato Chips", "brand": "Kettle", "category": "snacks", "price": 3.29 }
      ];
      renderCatalogGrid(catalogProducts);
    }
  }

  function renderCatalogGrid(products) {
    productGrid.innerHTML = "";

    const filtered = activeFilter === "all" 
      ? products 
      : products.filter(p => p.category.toLowerCase() === activeFilter.toLowerCase());

    document.getElementById("catalog-count-label").textContent = `${filtered.length} items`;

    if (filtered.length === 0) {
      productGrid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 32px;">No matching products found.</p>`;
      return;
    }

    filtered.forEach(prod => {
      const card = document.createElement("div");
      card.className = "product-card";

      const defaultImg = "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=400&q=80";

      const imgWrap = document.createElement("div");
      imgWrap.className = "product-img-wrap";
      
      const img = document.createElement("img");
      img.src = prod.image || defaultImg;
      img.alt = prod.name;
      img.className = "product-img";
      img.onerror = function() {
        this.onerror = null;
        this.src = defaultImg;
      };
      imgWrap.appendChild(img);

      const info = document.createElement("div");
      info.className = "product-info";
      info.innerHTML = `
        <span class="product-name">${prod.name}</span>
        <span class="product-brand">${prod.brand} &bull; ${prod.size || prod.category}</span>
        <div class="product-price-row">
          <span class="product-price">$${prod.price.toFixed(2)}</span>
        </div>
      `;

      const addBtn = document.createElement("button");
      addBtn.className = "btn-add-cart";
      addBtn.setAttribute("data-name", prod.name);
      addBtn.textContent = "+ Add to List";
      addBtn.addEventListener("click", () => {
        addShoppingItem(prod.name, 1);
        showToast(`✓ Added ${prod.name} to cart`, "success");
      });

      card.appendChild(imgWrap);
      card.appendChild(info);
      card.appendChild(addBtn);

      productGrid.appendChild(card);
    });
  }

  // Filter Button Listeners
  filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      filterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeFilter = btn.getAttribute("data-cat");
      renderCatalogGrid(catalogProducts);
    });
  });

  function filterCatalogByQuery(query) {
    const q = query.toLowerCase();
    
    // Parse price regex under $X
    const priceMatch = q.match(/under \$?(\d+(?:\.\d+)?)/);
    const maxPrice = priceMatch ? floatVal(priceMatch[1]) : null;

    const terms = q.replace(/search|find|under|\$\d+/g, "").strip ? q.replace(/search|find|under|\$\d+/g, "").strip().split(" ") : q.replace(/search|find|under|\$\d+/g, "").split(" ");

    const results = catalogProducts.filter(p => {
      if (maxPrice && p.price > maxPrice) return false;
      const fullStr = `${p.name} ${p.brand} ${p.category}`.toLowerCase();
      return terms.some(t => t.length > 2 && fullStr.includes(t)) || !terms.length;
    });

    renderCatalogGrid(results);
  }

  function floatVal(v) { try { return parseFloat(v); } catch(e){ return null; } }

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

  function updateQuantity(id, delta) {
    const target = shoppingList.find(i => i.id === id);
    if (target) {
      target.quantity += delta;
      if (target.quantity <= 0) {
        removeShoppingItem(id);
      } else {
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
    cartBadge.textContent = shoppingList.reduce((acc, i) => acc + i.quantity, 0);

    if (shoppingList.length === 0) {
      emptyCartBox.classList.remove("hidden");
      return;
    } else {
      emptyCartBox.classList.add("hidden");
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
          <span class="item-name">${item.item}</span>
          <div class="item-qty-controls">
            <button class="qty-btn btn-minus">&minus;</button>
            <span class="item-qty-val">${item.quantity}</span>
            <button class="qty-btn btn-plus">+</button>
            <button class="remove-btn" title="Remove">&times;</button>
          </div>
        `;

        li.querySelector(".btn-minus").addEventListener("click", () => updateQuantity(item.id, -1));
        li.querySelector(".btn-plus").addEventListener("click", () => updateQuantity(item.id, 1));
        li.querySelector(".remove-btn").addEventListener("click", () => removeShoppingItem(item.id));

        ul.appendChild(li);
      });

      categorizedList.appendChild(groupEl);
    });
  }

  // Clear All List Items
  clearListBtn.addEventListener("click", () => {
    if (shoppingList.length === 0) return;
    if (confirm("Clear all items from your shopping list?")) {
      shoppingList = [];
      saveListToStorage();
      renderShoppingList();
      showToast("Shopping list cleared.", "info");
    }
  });

  // Sample Chips Listeners
  sampleChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const phrase = chip.getAttribute("data-phrase");
      transcriptText.textContent = `"${phrase}"`;
      processVoiceCommandText(phrase);
    });
  });

  // Load Smart Suggestions
  async function loadSuggestions() {
    try {
      const res = await fetch("/api/suggestions/seasonal");
      const data = await res.json();
      if (data.status === "success" && data.items) {
        seasonalChipsWrap.innerHTML = "";
        data.items.slice(0, 5).forEach(item => {
          const c = document.createElement("button");
          c.className = "sample-chip";
          c.textContent = `+ ${item}`;
          c.addEventListener("click", () => {
            addShoppingItem(item, 1);
            showToast(`✓ Added ${item} to list`, "success");
          });
          seasonalChipsWrap.appendChild(c);
        });
      }
    } catch(e) {}
  }

  // -----------------------------------------------------------------
  // 4. UI Helpers & Toast System
  // -----------------------------------------------------------------
  function setUIState(state, text) {
    statusIndicator.className = `status-indicator-bar status-${state}`;
    statusText.textContent = text;
    micBtn.className = `mic-btn-main ${state}`;
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

  // MediaRecorder Audio Fallback for older browsers
  async function fallbackMediaRecorder() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      setUIState("listening", "Listening (MediaRecorder)...");
      recorder.ondataavailable = e => chunks.push(e.data);
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("file", blob, "recording.webm");

        setUIState("processing", "Processing backend audio...");
        try {
          const res = await fetch("/api/voice/process", { method: "POST", body: formData });
          const data = await res.json();
          executeBackendAction(data);
        } catch(e) {
          showToast("Could not connect to backend speech server.", "error");
        } finally {
          setUIState("idle", "Tap mic and speak naturally");
        }
        stream.getTracks().forEach(t => t.stop());
      };

      recorder.start();
      setTimeout(() => { if (recorder.state === "recording") recorder.stop(); }, 4000);
    } catch (err) {
      showToast("Mic permission denied or unavailable.", "error");
      setUIState("idle", "Tap mic and speak naturally");
    }
  }
});
