// CUP Monitor — Background Service Worker (Manifest V3)

chrome.runtime.onInstalled.addListener(() => {
  console.log("CUP Monitor Extension installata con successo.");
});

// Ascolto messaggi dal popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "START_MONITORING") {
    startAlarm();
    sendResponse({ status: "STARTED" });
  } else if (request.action === "STOP_MONITORING") {
    stopAlarm();
    sendResponse({ status: "STOPPED" });
  } else if (request.action === "CHECK_NOW") {
    performCUPCheck().then((result) => {
      sendResponse(result);
    });
    return true; // Rende la risposta asincrona
  }
});

async function startAlarm() {
  const data = await chrome.storage.local.get(["interval"]);
  const intervalMinutes = data.interval || 30;

  chrome.alarms.create("CUP_MONITOR_ALARM", {
    periodInMinutes: intervalMinutes
  });

  const nextCheck = Date.now() + intervalMinutes * 60 * 1000;
  await chrome.storage.local.set({ nextCheckTimestamp: nextCheck });

  console.log(`CUP Monitor: allarme impostato ogni ${intervalMinutes} minuti. Prossimo alle: ${new Date(nextCheck).toLocaleTimeString()}`);
  
  // Esegui subito il primo controllo
  performCUPCheck();
}

function stopAlarm() {
  chrome.alarms.clear("CUP_MONITOR_ALARM");
  chrome.storage.local.set({
    lastStatus: "STOPPED",
    lastMessage: "Monitoraggio in pausa.",
    lastCheck: new Date().toLocaleTimeString(),
    nextCheckTimestamp: null
  });
  console.log("CUP Monitor: allarme fermato.");
}

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === "CUP_MONITOR_ALARM") {
    const data = await chrome.storage.local.get(["interval"]);
    const intervalMinutes = data.interval || 30;
    const nextCheck = Date.now() + intervalMinutes * 60 * 1000;
    await chrome.storage.local.set({ nextCheckTimestamp: nextCheck });

    performCUPCheck();
  }
});

const REGIONAL_PORTALS_CONFIG = {
  "Abruzzo": { domain: "sanita.regione.abruzzo.it", searchUrl: "https://sanita.regione.abruzzo.it" },
  "Basilicata": { domain: "portale.aslbasilicata.it", searchUrl: "https://portale.aslbasilicata.it" },
  "Calabria": { domain: "rcup.regione.calabria.it", searchUrl: "https://rcup.regione.calabria.it" },
  "Campania": { domain: "sinfonia.regione.campania.it", searchUrl: "https://sinfonia.regione.campania.it" },
  "Emilia-Romagna": { domain: "cupweb.it", searchUrl: "https://www.cupweb.it" },
  "Friuli-Venezia Giulia": { domain: "sesamo.sanita.fvg.it", searchUrl: "https://sesamo.sanita.fvg.it" },
  "Lazio": { domain: "prenotasanita.regione.lazio.it", searchUrl: "https://prenotasanita.regione.lazio.it" },
  "Liguria": { domain: "prenotosanita.regione.liguria.it", searchUrl: "https://prenotosanita.regione.liguria.it" },
  "Lombardia": { domain: "prenotasalute.regione.lombardia.it", searchUrl: "https://prenotasalute.regione.lombardia.it" },
  "Marche": { domain: "mycupmarche.it", searchUrl: "https://mycupmarche.it/prenotazionecittadino/web/search/nre", postUrl: "https://mycupmarche.it/prenotazionecittadino/web/search/nre/result/" },
  "Molise": { domain: "asrem.gov.it", searchUrl: "https://www.asrem.gov.it" },
  "Piemonte": { domain: "salutepiemonte.it", searchUrl: "https://www.salutepiemonte.it" },
  "Puglia": { domain: "sanita.puglia.it", searchUrl: "https://www.sanita.puglia.it" },
  "Sardegna": { domain: "cupweb.sardegnasalute.it", searchUrl: "https://cupweb.sardegnasalute.it" },
  "Sicilia": { domain: "siciliainsalute.it", searchUrl: "https://siciliainsalute.it" },
  "Toscana": { domain: "prenota.sanita.toscana.it", searchUrl: "https://prenota.sanita.toscana.it" },
  "Trentino-Alto Adige": { domain: "apss.tn.it", searchUrl: "https://www.apss.tn.it" },
  "Umbria": { domain: "cupumbria.it", searchUrl: "https://cupumbria.it" },
  "Valle d'Aosta": { domain: "ausl.vda.it", searchUrl: "https://www.ausl.vda.it" },
  "Veneto": { domain: "azero.veneto.it", searchUrl: "https://www.azero.veneto.it" }
};

async function performCUPCheck() {
  const data = await chrome.storage.local.get(["nre", "cf", "region", "province", "isActive"]);
  const nre = (data.nre || "").trim();
  const cf = (data.cf || "").trim().toUpperCase();
  const region = data.region || "Marche";
  const portalCfg = REGIONAL_PORTALS_CONFIG[region] || REGIONAL_PORTALS_CONFIG["Marche"];

  if (!nre || !cf) {
    const res = {
      status: "ERROR",
      message: "Dati mancanti: inserisci NRE e Codice Fiscale nel popup.",
      time: new Date().toLocaleTimeString()
    };
    await saveStatus(res);
    return res;
  }

  console.log(`CUP Monitor: avvio verifica disponibilità per ${region} (NRE: ${nre})`);

  try {
    // 1. Verifica presenza cookie per il dominio regionale
    const cookies = await chrome.cookies.getAll({ domain: portalCfg.domain });
    if (!cookies || cookies.length === 0) {
      const res = {
        status: "NOT_LOGGED_IN",
        message: `Nessuna sessione trovata per CUP ${region}. Clicca su 'Apri Portale CUP' ed effettua il login SPID.`,
        time: new Date().toLocaleTimeString()
      };
      notifyUser(`Accesso SPID Richiesto (${region}) 🔑`, res.message);
      await saveStatus(res);
      return res;
    }

    // 2. Verifica se la sessione è valida tramite GET sulla pagina di ricerca
    const checkRes = await fetch(portalCfg.searchUrl, {
      method: "GET",
      credentials: "include"
    });

    const checkText = await checkRes.text();

    if (checkText.includes("WAYF.aspx") || checkText.includes("cohesion") || checkRes.url.includes("WAYF.aspx") || checkText.includes("Autenticazione")) {
      const res = {
        status: "SESSION_EXPIRED",
        message: `Sessione SPID scaduta per CUP ${region}. Clicca su 'Apri Portale CUP' per rientrare.`,
        time: new Date().toLocaleTimeString()
      };
      notifyUser(`Sessione SPID Scaduta (${region}) ☕`, res.message);
      await saveStatus(res);
      return res;
    }

    // 3. Prepariamo la richiesta POST per cercare le disponibilità
    let matrice1 = "1100A";
    let matrice2 = nre;
    if (nre.length > 12) {
      matrice1 = nre.slice(0, nre.length - 12);
      matrice2 = nre.slice(nre.length - 12);
    }

    const formData = new URLSearchParams();
    formData.append("cf", cf);
    formData.append("matrice1", matrice1);
    formData.append("matrice2", matrice2);
    formData.append("c.cntr0", "1");

    const postEndpoint = portalCfg.postUrl || portalCfg.searchUrl;
    console.log(`CUP Monitor (${region}): invio richiesta POST a ${postEndpoint}`);

    const searchRes = await fetch(postEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: formData.toString(),
      credentials: "include"
    });

    const searchText = await searchRes.text();
    const lowerText = searchText.toLowerCase();

    // 4. Analisi esito della risposta
    if (lowerText.includes("nessuna disponibilità") || lowerText.includes("non ci sono appuntamenti") || lowerText.includes("nessun risultato")) {
      const res = {
        status: "NO_MATCH",
        message: "Controllo eseguito: al momento nessuna disponibilità trovata.",
        time: new Date().toLocaleTimeString()
      };
      await saveStatus(res);
      return res;
    }

    // Se ci sono errori specifici (es. ricetta errata)
    if (lowerText.includes("errore") || lowerText.includes("non valida") || lowerText.includes("non trovata")) {
      const res = {
        status: "WARNING",
        message: "Il portale CUP segnala un avviso sulla ricetta (verifica NRE e CF).",
        time: new Date().toLocaleTimeString()
      };
      await saveStatus(res);
      return res;
    }

    // Se siamo arrivati qui e la pagina contiene tabelle o risultati:
    const res = {
      status: "FOUND",
      message: "🎉 DISPONIBILITÀ TROVATA! Clicca per prenotare subito sul CUP Marche.",
      time: new Date().toLocaleTimeString()
    };

    notifyUser("🎉 Posto Trovato! CUP Marche", res.message, true);
    await saveStatus(res);
    return res;

  } catch (err) {
    console.error("Errore durante il controllo CUP:", err);
    const res = {
      status: "ERROR",
      message: `Errore di connessione: ${err.message || err}`,
      time: new Date().toLocaleTimeString()
    };
    await saveStatus(res);
    return res;
  }
}

async function saveStatus(info) {
  await chrome.storage.local.set({
    lastStatus: info.status,
    lastMessage: info.message,
    lastCheck: info.time
  });
}

function notifyUser(title, message, isMatch = false) {
  try {
    const iconPath = chrome.runtime.getURL("icons/icon128.png");
    chrome.notifications.create({
      type: "basic",
      iconUrl: iconPath,
      title: title,
      message: message,
      priority: 2,
      requireInteraction: true
    }, (notificationId) => {
      if (chrome.runtime.lastError) {
        console.warn("Avviso notifica Chrome:", chrome.runtime.lastError.message);
      }
    });

    if (isMatch) {
      chrome.action.setBadgeText({ text: "1" });
      chrome.action.setBadgeBackgroundColor({ color: "#10b981" });
    }
  } catch (err) {
    console.error("Errore notifica utente:", err);
  }
}

// Cliccando sulla notifica si apre la pagina del CUP regionale configurato
chrome.notifications.onClicked.addListener(async () => {
  const data = await chrome.storage.local.get(["region"]);
  const region = data.region || "Marche";
  const portalCfg = REGIONAL_PORTALS_CONFIG[region] || REGIONAL_PORTALS_CONFIG["Marche"];
  chrome.tabs.create({ url: portalCfg.searchUrl });
});
