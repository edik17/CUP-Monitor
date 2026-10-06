document.addEventListener("DOMContentLoaded", async () => {
  const nreInput = document.getElementById("nreInput");
  const cfInput = document.getElementById("cfInput");
  const provinceSelect = document.getElementById("provinceSelect");
  const intervalSelect = document.getElementById("intervalSelect");
  const toggleBtn = document.getElementById("toggleBtn");
  const checkNowBtn = document.getElementById("checkNowBtn");
  const loginCUPBtn = document.getElementById("loginCUPBtn");
  const statusBadge = document.getElementById("statusBadge");
  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");

  const resultBox = document.getElementById("resultBox");
  const lastCheckTime = document.getElementById("lastCheckTime");
  const lastCheckMessage = document.getElementById("lastCheckMessage");

  // Rimuovi eventuale badge notifica
  chrome.action.setBadgeText({ text: "" });

  // Carica impostazioni salvate
  const data = await chrome.storage.local.get([
    "nre",
    "cf",
    "province",
    "interval",
    "isActive",
    "lastCheck",
    "lastStatus",
    "lastMessage"
  ]);

  if (data.nre) nreInput.value = data.nre;
  if (data.cf) cfInput.value = data.cf;
  if (data.province) provinceSelect.value = data.province;
  if (data.interval) intervalSelect.value = data.interval;

  updateUI(data.isActive);
  if (data.lastStatus) {
    displayResult(data.lastStatus, data.lastMessage, data.lastCheck);
  }

  // Toggle Avvio / Fermata
  toggleBtn.addEventListener("click", async () => {
    const isCurrentlyActive = toggleBtn.getAttribute("data-active") === "true";

    if (!isCurrentlyActive) {
      const nre = nreInput.value.trim();
      const cf = cfInput.value.trim().toUpperCase();

      if (!nre || !cf) {
        alert("Inserisci sia il Numero di Ricetta (NRE) che il Codice Fiscale.");
        return;
      }

      await chrome.storage.local.set({
        nre: nre,
        cf: cf,
        province: provinceSelect.value,
        interval: parseInt(intervalSelect.value, 10),
        isActive: true
      });

      chrome.runtime.sendMessage({ action: "START_MONITORING" });
      updateUI(true);
    } else {
      await chrome.storage.local.set({ isActive: false });
      chrome.runtime.sendMessage({ action: "STOP_MONITORING" });
      updateUI(false);
    }
  });

  // Tasto "Controlla Ora" per test immediato
  checkNowBtn.addEventListener("click", async () => {
    const nre = nreInput.value.trim();
    const cf = cfInput.value.trim().toUpperCase();

    if (!nre || !cf) {
      alert("Inserisci prima NRE e Codice Fiscale.");
      return;
    }

    // Salva i dati prima del controllo
    await chrome.storage.local.set({
      nre: nre,
      cf: cf,
      province: provinceSelect.value,
      interval: parseInt(intervalSelect.value, 10)
    });

    checkNowBtn.disabled = true;
    const originalText = checkNowBtn.innerHTML;
    checkNowBtn.innerHTML = "<span>⏳</span> Controllo...";

    displayResult("CHECKING", "Connessione al portale CUP Marche in corso...", "Adesso");

    chrome.runtime.sendMessage({ action: "CHECK_NOW" }, (response) => {
      checkNowBtn.disabled = false;
      checkNowBtn.innerHTML = originalText;

      if (response) {
        displayResult(response.status, response.message, response.time);
      } else {
        displayResult("ERROR", "Nessuna risposta dal service worker. Prova a ricaricare l'estensione.", new Date().toLocaleTimeString());
      }
    });
  });

  // Apri pagina CUP per login SPID
  loginCUPBtn.addEventListener("click", () => {
    chrome.tabs.create({ url: "https://mycupmarche.it/prenotazionecittadino/web/search/nre" });
  });

  function updateUI(isActive) {
    if (isActive) {
      toggleBtn.setAttribute("data-active", "true");
      toggleBtn.style.background = "#dc2626";
      toggleBtn.innerHTML = "<span>⏹️</span> Ferma Monitoraggio";
      statusDot.className = "status-dot active-dot";
      statusText.textContent = "Monitoraggio Attivo";
      statusBadge.style.color = "#047857";
      statusBadge.style.background = "#ecfdf5";
    } else {
      toggleBtn.setAttribute("data-active", "false");
      toggleBtn.style.background = "#4f46e5";
      toggleBtn.innerHTML = "<span>▶️</span> Avvia Monitoraggio";
      statusDot.className = "status-dot";
      statusText.textContent = "In Pausa";
      statusBadge.style.color = "#475569";
      statusBadge.style.background = "#f1f5f9";
    }
  }

  function displayResult(status, message, time) {
    resultBox.style.display = "block";
    lastCheckTime.textContent = time || new Date().toLocaleTimeString();
    lastCheckMessage.textContent = message || "";

    if (status === "FOUND") {
      resultBox.style.background = "#ecfdf5";
      resultBox.style.borderColor = "#6ee7b7";
      lastCheckMessage.style.color = "#065f46";
      lastCheckMessage.style.fontWeight = "bold";
    } else if (status === "NO_MATCH") {
      resultBox.style.background = "#f0fdf4";
      resultBox.style.borderColor = "#bbf7d0";
      lastCheckMessage.style.color = "#166534";
      lastCheckMessage.style.fontWeight = "normal";
    } else if (status === "SESSION_EXPIRED" || status === "NOT_LOGGED_IN") {
      resultBox.style.background = "#fffbeb";
      resultBox.style.borderColor = "#fde68a";
      lastCheckMessage.style.color = "#92400e";
      lastCheckMessage.style.fontWeight = "bold";
    } else if (status === "CHECKING") {
      resultBox.style.background = "#f8fafc";
      resultBox.style.borderColor = "#cbd5e1";
      lastCheckMessage.style.color = "#475569";
      lastCheckMessage.style.fontWeight = "normal";
    } else {
      resultBox.style.background = "#fef2f2";
      resultBox.style.borderColor = "#fecaca";
      lastCheckMessage.style.color = "#991b1b";
      lastCheckMessage.style.fontWeight = "normal";
    }
  }
});
