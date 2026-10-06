document.addEventListener("DOMContentLoaded", async () => {
  const nreInput = document.getElementById("nreInput");
  const cfInput = document.getElementById("cfInput");
  const regionSelect = document.getElementById("regionSelect");
  const provinceSelect = document.getElementById("provinceSelect");
  const intervalSelect = document.getElementById("intervalSelect");
  const toggleBtn = document.getElementById("toggleBtn");
  const checkNowBtn = document.getElementById("checkNowBtn");
  const loginCUPBtn = document.getElementById("loginCUPBtn");
  const statusBadge = document.getElementById("statusBadge");
  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");

  const countdownBox = document.getElementById("countdownBox");
  const countdownTimer = document.getElementById("countdownTimer");

  const resultBox = document.getElementById("resultBox");
  const lastCheckTime = document.getElementById("lastCheckTime");
  const lastCheckMessage = document.getElementById("lastCheckMessage");

  let countdownIntervalId = null;

  const REGIONAL_PORTALS_MAP = {
    "Abruzzo": "https://sanita.regione.abruzzo.it",
    "Basilicata": "https://portale.aslbasilicata.it",
    "Calabria": "https://rcup.regione.calabria.it",
    "Campania": "https://sinfonia.regione.campania.it",
    "Emilia-Romagna": "https://www.cupweb.it",
    "Friuli-Venezia Giulia": "https://sesamo.sanita.fvg.it",
    "Lazio": "https://prenotasanita.regione.lazio.it",
    "Liguria": "https://prenotosanita.regione.liguria.it",
    "Lombardia": "https://prenotasalute.regione.lombardia.it",
    "Marche": "https://mycupmarche.it/prenotazionecittadino/web/search/nre",
    "Molise": "https://www.asrem.gov.it",
    "Piemonte": "https://www.salutepiemonte.it",
    "Puglia": "https://www.sanita.puglia.it",
    "Sardegna": "https://cupweb.sardegnasalute.it",
    "Sicilia": "https://siciliainsalute.it",
    "Toscana": "https://prenota.sanita.toscana.it",
    "Trentino-Alto Adige": "https://www.apss.tn.it",
    "Umbria": "https://cupumbria.it",
    "Valle d'Aosta": "https://www.ausl.vda.it",
    "Veneto": "https://www.azero.veneto.it"
  };

  const REGIONAL_PROVINCES_MAP = {
    "Abruzzo": ["L'Aquila", "Chieti", "Pescara", "Teramo"],
    "Basilicata": ["Potenza", "Matera"],
    "Calabria": ["Catanzaro", "Cosenza", "Crotone", "Reggio Calabria", "Vibo Valentia"],
    "Campania": ["Napoli", "Salerno", "Caserta", "Avellino", "Benevento"],
    "Emilia-Romagna": ["Bologna", "Modena", "Reggio Emilia", "Parma", "Ferrara", "Forlì-Cesena", "Ravenna", "Rimini", "Piacenza"],
    "Friuli-Venezia Giulia": ["Trieste", "Udine", "Pordenone", "Gorizia"],
    "Lazio": ["Roma", "Latina", "Frosinone", "Viterbo", "Rieti"],
    "Liguria": ["Genova", "La Spezia", "Savona", "Imperia"],
    "Lombardia": ["Milano", "Brescia", "Bergamo", "Monza e Brianza", "Como", "Varese", "Pavia", "Cremona", "Mantova", "Lecco", "Lodi", "Sondrio"],
    "Marche": ["Ancona", "Pesaro e Urbino", "Macerata", "Fermo", "Ascoli Piceno"],
    "Molise": ["Campobasso", "Isernia"],
    "Piemonte": ["Torino", "Cuneo", "Alessandria", "Novara", "Asti", "Biella", "Vercelli", "Verbano-Cusio-Ossola"],
    "Puglia": ["Bari", "Lecce", "Taranto", "Foggia", "Brindisi", "Barletta-Andria-Trani"],
    "Sardegna": ["Cagliari", "Sassari", "Nuoro", "Oristano", "Sud Sardegna"],
    "Sicilia": ["Palermo", "Catania", "Messina", "Agrigento", "Trapani", "Siracusa", "Ragusa", "Caltanissetta", "Enna"],
    "Toscana": ["Firenze", "Pisa", "Livorno", "Arezzo", "Pistoia", "Lucca", "Prato", "Grosseto", "Siena", "Massa-Carrara"],
    "Trentino-Alto Adige": ["Trento", "Bolzano"],
    "Umbria": ["Perugia", "Terni"],
    "Valle d'Aosta": ["Aosta"],
    "Veneto": ["Venezia", "Verona", "Padova", "Vicenza", "Treviso", "Rovigo", "Belluno"]
  };

  function updateProvinceOptions(selectedRegion, selectedProvince) {
    const provs = REGIONAL_PROVINCES_MAP[selectedRegion] || [];
    provinceSelect.innerHTML = '<option value="Tutte">Tutte le province</option>';
    provs.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p;
      opt.textContent = p;
      if (p === selectedProvince) opt.selected = true;
      provinceSelect.appendChild(opt);
    });
  }

  // Rimuovi eventuale badge notifica
  chrome.action.setBadgeText({ text: "" });

  // Carica impostazioni salvate
  const data = await chrome.storage.local.get([
    "nre",
    "cf",
    "region",
    "province",
    "interval",
    "isActive",
    "lastCheck",
    "lastStatus",
    "lastMessage",
    "nextCheckTimestamp"
  ]);

  if (data.nre) nreInput.value = data.nre;
  if (data.cf) cfInput.value = data.cf;
  if (data.region) regionSelect.value = data.region;
  updateProvinceOptions(regionSelect.value, data.province);
  if (data.interval) intervalSelect.value = data.interval;

  regionSelect.addEventListener("change", () => {
    updateProvinceOptions(regionSelect.value, "Tutte");
  });

  updateUI(data.isActive);
  if (data.lastStatus) {
    displayResult(data.lastStatus, data.lastMessage, data.lastCheck);
  }
  if (data.isActive && data.nextCheckTimestamp) {
    startCountdown(data.nextCheckTimestamp);
  }

  // Ascolta aggiornamenti dallo storage in tempo reale
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local") return;
    if (changes.isActive) {
      updateUI(changes.isActive.newValue);
    }
    if (changes.nextCheckTimestamp) {
      if (changes.nextCheckTimestamp.newValue) {
        startCountdown(changes.nextCheckTimestamp.newValue);
      } else {
        stopCountdown();
      }
    }
    if (changes.lastStatus || changes.lastMessage || changes.lastCheck) {
      chrome.storage.local.get(["lastStatus", "lastMessage", "lastCheck"], (d) => {
        if (d.lastStatus) displayResult(d.lastStatus, d.lastMessage, d.lastCheck);
      });
    }
  });

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

      const intVal = parseInt(intervalSelect.value, 10);
      const nextTimestamp = Date.now() + intVal * 60 * 1000;

      await chrome.storage.local.set({
        nre: nre,
        cf: cf,
        region: regionSelect.value,
        province: provinceSelect.value,
        interval: intVal,
        isActive: true,
        nextCheckTimestamp: nextTimestamp
      });

      chrome.runtime.sendMessage({ action: "START_MONITORING" });
      updateUI(true);
      startCountdown(nextTimestamp);
    } else {
      await chrome.storage.local.set({
        isActive: false,
        nextCheckTimestamp: null
      });
      chrome.runtime.sendMessage({ action: "STOP_MONITORING" });
      updateUI(false);
      stopCountdown();
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

    await chrome.storage.local.set({
      nre: nre,
      cf: cf,
      region: regionSelect.value,
      province: provinceSelect.value,
      interval: parseInt(intervalSelect.value, 10)
    });

    checkNowBtn.disabled = true;
    const originalText = checkNowBtn.innerHTML;
    checkNowBtn.innerHTML = "<span>⏳</span> Controllo...";

    displayResult("CHECKING", `Connessione al portale CUP ${regionSelect.value} in corso...`, "Adesso");

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

  // Apri pagina CUP per login SPID per la regione selezionata
  loginCUPBtn.addEventListener("click", () => {
    const reg = regionSelect.value;
    const url = REGIONAL_PORTALS_MAP[reg] || "https://mycupmarche.it/prenotazionecittadino/web/search/nre";
    chrome.tabs.create({ url: url });
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
      stopCountdown();
    }
  }

  function startCountdown(targetTimestamp) {
    if (countdownIntervalId) clearInterval(countdownIntervalId);
    if (!targetTimestamp) {
      stopCountdown();
      return;
    }

    countdownBox.style.display = "flex";

    function update() {
      const remainingMs = targetTimestamp - Date.now();
      if (remainingMs <= 0) {
        countdownTimer.textContent = "Verifica in corso... ⏳";
        return;
      }

      const totalSec = Math.floor(remainingMs / 1000);
      const min = Math.floor(totalSec / 60);
      const sec = totalSec % 60;
      countdownTimer.textContent = `${min}m ${sec < 10 ? '0' : ''}${sec}s`;
    }

    update();
    countdownIntervalId = setInterval(update, 1000);
  }

  function stopCountdown() {
    if (countdownIntervalId) {
      clearInterval(countdownIntervalId);
      countdownIntervalId = null;
    }
    countdownBox.style.display = "none";
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
