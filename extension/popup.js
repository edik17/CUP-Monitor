document.addEventListener("DOMContentLoaded", async () => {
  const nreInput = document.getElementById("nreInput");
  const cfInput = document.getElementById("cfInput");
  const provinceSelect = document.getElementById("provinceSelect");
  const intervalSelect = document.getElementById("intervalSelect");
  const toggleBtn = document.getElementById("toggleBtn");
  const loginCUPBtn = document.getElementById("loginCUPBtn");
  const statusBadge = document.getElementById("statusBadge");
  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");

  // Rimuovi eventuale badge notifica
  chrome.action.setBadgeText({ text: "" });

  // Carica impostazioni salvate
  const data = await chrome.storage.local.get([
    "nre",
    "cf",
    "province",
    "interval",
    "isActive",
    "lastCheck"
  ]);

  if (data.nre) nreInput.value = data.nre;
  if (data.cf) cfInput.value = data.cf;
  if (data.province) provinceSelect.value = data.province;
  if (data.interval) intervalSelect.value = data.interval;

  updateUI(data.isActive, data.lastCheck);

  // Toggle Avvio / Fermata
  toggleBtn.addEventListener("click", async () => {
    const isCurrentlyActive = toggleBtn.getAttribute("data-active") === "true";

    if (!isCurrentlyActive) {
      // Validazione minima
      const nre = nreInput.value.trim();
      const cf = cfInput.value.trim().toUpperCase();

      if (!nre || !cf) {
        alert("Inserisci sia il Numero di Ricetta (NRE) che il Codice Fiscale.");
        return;
      }

      // Salva
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
      // Ferma monitoraggio
      await chrome.storage.local.set({ isActive: false });
      chrome.runtime.sendMessage({ action: "STOP_MONITORING" });
      updateUI(false);
    }
  });

  // Apri pagina CUP per login
  loginCUPBtn.addEventListener("click", () => {
    chrome.tabs.create({ url: "https://mycupmarche.it/prenotazionecittadino/web/search/nre" });
  });

  function updateUI(isActive, lastCheck) {
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
});
