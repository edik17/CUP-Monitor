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

async function performCUPCheck() {
  const data = await chrome.storage.local.get(["nre", "cf", "province", "isActive"]);
  const nre = (data.nre || "").trim();
  const cf = (data.cf || "").trim().toUpperCase();

  if (!nre || !cf) {
    const res = {
      status: "ERROR",
      message: "Dati mancanti: inserisci NRE e Codice Fiscale nel popup.",
      time: new Date().toLocaleTimeString()
    };
    await saveStatus(res);
    return res;
  }

  console.log("CUP Monitor: avvio verifica disponibilità per NRE:", nre);

  try {
    // 1. Verifica presenza cookie per mycupmarche.it
    const cookies = await chrome.cookies.getAll({ domain: "mycupmarche.it" });
    if (!cookies || cookies.length === 0) {
      const res = {
        status: "NOT_LOGGED_IN",
        message: "Nessuna sessione trovata. Clicca su 'Apri Portale CUP' ed effettua il login SPID.",
        time: new Date().toLocaleTimeString()
      };
      notifyUser("Accesso SPID Richiesto 🔑", res.message);
      await saveStatus(res);
      return res;
    }

    // 2. Verifica se la sessione è valida tramite GET sulla pagina di ricerca
    const checkRes = await fetch("https://mycupmarche.it/prenotazionecittadino/web/search/nre", {
      method: "GET",
      credentials: "include"
    });

    const checkText = await checkRes.text();

    if (checkText.includes("WAYF.aspx") || checkText.includes("cohesion") || checkRes.url.includes("WAYF.aspx") || checkText.includes("Autenticazione")) {
      const res = {
        status: "SESSION_EXPIRED",
        message: "Sessione SPID scaduta. Clicca su 'Apri Portale CUP' per rientrare.",
        time: new Date().toLocaleTimeString()
      };
      notifyUser("Sessione SPID Scaduta ☕", res.message);
      await saveStatus(res);
      return res;
    }

    // 3. Prepariamo la richiesta POST per cercare le disponibilità
    // L'NRE viene solitamente diviso: primi caratteri (max 5-7, es 1100A) e restante (max 12 cifre)
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

    console.log(`CUP Monitor: invio richiesta POST (matrice1: ${matrice1}, matrice2: ${matrice2})`);

    const searchRes = await fetch("https://mycupmarche.it/prenotazionecittadino/web/search/nre/result/", {
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
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icons/icon128.png",
    title: title,
    message: message,
    priority: 2,
    requireInteraction: true
  });

  if (isMatch) {
    chrome.action.setBadgeText({ text: "1" });
    chrome.action.setBadgeBackgroundColor({ color: "#10b981" });
  }
}

// Cliccando sulla notifica si apre la pagina del CUP
chrome.notifications.onClicked.addListener(() => {
  chrome.tabs.create({ url: "https://mycupmarche.it/prenotazionecittadino/web/search/nre" });
});
