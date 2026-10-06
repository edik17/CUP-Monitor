// CUP Monitor — Background Service Worker (Manifest V3)

chrome.runtime.onInstalled.addListener(() => {
  console.log("CUP Monitor Extension installata con successo.");
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "START_MONITORING") {
    startAlarm();
  } else if (request.action === "STOP_MONITORING") {
    stopAlarm();
  }
});

async function startAlarm() {
  const data = await chrome.storage.local.get(["interval"]);
  const intervalMinutes = data.interval || 30;

  chrome.alarms.create("CUP_MONITOR_ALARM", {
    periodInMinutes: intervalMinutes
  });

  console.log(`CUP Monitor: allarme impostato ogni ${intervalMinutes} minuti.`);
  
  // Esegui subito il primo controllo
  performCUPCheck();
}

function stopAlarm() {
  chrome.alarms.clear("CUP_MONITOR_ALARM");
  console.log("CUP Monitor: allarme fermato.");
}

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "CUP_MONITOR_ALARM") {
    performCUPCheck();
  }
});

async function performCUPCheck() {
  const data = await chrome.storage.local.get(["nre", "cf", "province", "isActive"]);
  if (!data.isActive || !data.nre) return;

  console.log("CUP Monitor: avvio verifica disponibilità...");

  try {
    const res = await fetch("https://mycupmarche.it/prenotazionecittadino/web/search/nre", {
      method: "GET",
      credentials: "include" // Include automaticamente i cookie SPID del browser!
    });

    const text = await res.text();

    // Se reindirizza a Cohesion, la sessione SPID è scaduta
    if (text.includes("WAYF.aspx") || text.includes("cohesion") || res.url.includes("WAYF.aspx")) {
      notifyUser(
        "Sessione SPID Scaduta ☕",
        "I server regionali richiedono un nuovo accesso. Clicca sull'estensione per accedere al CUP Marche."
      );
      return;
    }

    // Qui la sessione è attiva: verifichiamo la presenza di disponibilità
    console.log("Sessione SPID valida verificata con successo.");

    await chrome.storage.local.set({ lastCheck: new Date().toLocaleTimeString() });

  } catch (err) {
    console.error("Errore durante la scansione:", err);
  }
}

function notifyUser(title, message) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icons/icon128.png",
    title: title,
    message: message,
    priority: 2
  });
}
