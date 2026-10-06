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

const REGIONAL_PROVINCES_KEYWORDS = {
  "Marche": {
    "Ancona": [
      "ancona", "torrette", "inrca", "jesi", "fabriano", "senigallia", "osimo",
      "chiaravalle", "loreto", "castelfidardo", "falconara", "camerano",
      "agugliano", "montemarciano", "filottrano", "cupramontana", "arcevia",
      "sassoferrato", "serra san quirico", "genga", "staffolo", "cerreto",
      "polverigi", "offagna", "numana", "sirolo", "monte san vito"
    ],
    "Pesaro e Urbino": [
      "pesaro", "fano", "urbino", "fossombrone", "cagli", "pergola", "mondolfo",
      "colli al metauro", "gabicce", "gradara", "tavullia", "vallefoglia"
    ],
    "Macerata": [
      "macerata", "civitanova", "recanati", "tolentino", "san severino",
      "potenza picena", "porto recanati", "corridonia", "morrovalle", "matelica", "camerino"
    ],
    "Fermo": [
      "fermo", "porto san giorgio", "sant'elpidio", "porto sant'elpidio",
      "montegranaro", "amandola", "monte urano"
    ],
    "Ascoli Piceno": [
      "ascoli", "san benedetto", "grottammare", "monteprandone",
      "folignano", "castel di lama", "spinetoli", "offida"
    ]
  },
  "Abruzzo": {
    "L'Aquila": ["l'aquila", "avezzano", "sulmona", "castel di sangro"],
    "Chieti": ["chieti", "vasto", "lanciano", "ortona", "atessa"],
    "Pescara": ["pescara", "penne", "popoli", "montesilvano"],
    "Teramo": ["teramo", "giulianova", "atri", "sant'omero"]
  },
  "Basilicata": {
    "Potenza": ["potenza", "melfi", "venosa", "villa d'agri", "lagonegro"],
    "Matera": ["matera", "policoro", "tinchi", "stigliano", "pisticci"]
  },
  "Calabria": {
    "Catanzaro": ["catanzaro", "lamezia", "soverato"],
    "Cosenza": ["cosenza", "rende", "rossano", "corigliano", "castrovillari", "paola"],
    "Crotone": ["crotone", "cirò"],
    "Reggio Calabria": ["reggio calabria", "gioia tauro", "locri", "polistena"],
    "Vibo Valentia": ["vibo valentia", "tropea"]
  },
  "Campania": {
    "Napoli": ["napoli", "cardarelli", "policlinico", "pozzuoli", "giugliano", "castellammare", "nola"],
    "Salerno": ["salerno", "ruggi", "battipaglia", "nocera", "cava de' tirreni", "eboli"],
    "Caserta": ["caserta", "aversa", "marcianise", "santa maria capua vetere"],
    "Avellino": ["avellino", "moscati", "ariano"],
    "Benevento": ["benevento", "san pio", "rummo"]
  },
  "Emilia-Romagna": {
    "Bologna": ["bologna", "sant'orsola", "maggiore", "rizzoli", "bellaria", "imola"],
    "Modena": ["modena", "policlinico", "baggiovara", "carpi", "sassuolo"],
    "Reggio Emilia": ["reggio emilia", "santa maria nuova", "guastalla"],
    "Parma": ["parma", "maggiore", "fidenza"],
    "Ferrara": ["ferrara", "cona", "cento"],
    "Forlì-Cesena": ["forlì", "cesena", "bufalini"],
    "Ravenna": ["ravenna", "faenza", "lugo"],
    "Rimini": ["rimini", "riccione"],
    "Piacenza": ["piacenza"]
  },
  "Friuli-Venezia Giulia": {
    "Trieste": ["trieste", "cattinara"],
    "Udine": ["udine", "santa maria della misericordia", "tolmezzo"],
    "Pordenone": ["pordenone", "san vito"],
    "Gorizia": ["gorizia", "monfalcone"]
  },
  "Lazio": {
    "Roma": ["roma", "umberto i", "gemelli", "sant'andrea", "san camillo", "tor vergata", "san giovanni", "tivoli", "civita"],
    "Latina": ["latina", "aprilia", "terracina", "formia"],
    "Frosinone": ["frosinone", "cassino", "sora"],
    "Viterbo": ["viterbo", "belcolle"],
    "Rieti": ["rieti"]
  },
  "Liguria": {
    "Genova": ["genova", "san martino", "galliera", "gaslini", "villa scassi"],
    "La Spezia": ["la spezia", "sarzana"],
    "Savona": ["savona", "pietra ligure", "albenga"],
    "Imperia": ["imperia", "sanremo"]
  },
  "Lombardia": {
    "Milano": ["milano", "niguarda", "policlinico", "san raffaele", "humanitas", "san carlo", "san paolo", "sesto", "legnano"],
    "Brescia": ["brescia", "spedali civili", "desenzano", "chiari"],
    "Bergamo": ["bergamo", "papa giovanni", "treviglio"],
    "Monza e Brianza": ["monza", "san gerardo", "desio", "vimercate"],
    "Como": ["como", "sant'anna", "cantù"],
    "Varese": ["varese", "circolo", "busto arsizio", "gallarate", "saronno"],
    "Pavia": ["pavia", "san matteo", "vigevano", "voghera"],
    "Cremona": ["cremona", "crema"],
    "Mantova": ["mantova", "carlo poma"],
    "Lecco": ["lecco"],
    "Lodi": ["lodi"],
    "Sondrio": ["sondrio"]
  },
  "Molise": {
    "Campobasso": ["campobasso", "cardarelli", "termoli"],
    "Isernia": ["isernia", "venafro"]
  },
  "Piemonte": {
    "Torino": ["torino", "molinette", "cto", "mauriziano", "san luigi", "rivoli"],
    "Cuneo": ["cuneo", "santa croce", "alba"],
    "Alessandria": ["alessandria", "casale"],
    "Novara": ["novara", "maggiore"],
    "Asti": ["asti"],
    "Biella": ["biella"],
    "Vercelli": ["vercelli"],
    "Verbano-Cusio-Ossola": ["verbania", "domodossola"]
  },
  "Puglia": {
    "Bari": ["bari", "policlinico", "di venere", "san paolo"],
    "Lecce": ["lecce", "vito fazzi"],
    "Taranto": ["taranto", "annunziata"],
    "Foggia": ["foggia", "riuniti"],
    "Brindisi": ["brindisi", "perrino"],
    "Barletta-Andria-Trani": ["barletta", "andria", "trani"]
  },
  "Sardegna": {
    "Cagliari": ["cagliari", "brotzu", "monserrato"],
    "Sassari": ["sassari", "alghero"],
    "Nuoro": ["nuoro"],
    "Oristano": ["oristano"],
    "Sud Sardegna": ["carbonia", "iglesias"]
  },
  "Sicilia": {
    "Palermo": ["palermo", "civico", "policlinico", "villa sofia"],
    "Catania": ["catania", "garibaldi", "cannizzaro", "policlinico"],
    "Messina": ["messina", "policlinico", "papardo"],
    "Agrigento": ["agrigento", "sciacca"],
    "Trapani": ["trapani", "marsala"],
    "Siracusa": ["siracusa"],
    "Ragusa": ["ragusa"],
    "Caltanissetta": ["caltanissetta"],
    "Enna": ["enna"]
  },
  "Toscana": {
    "Firenze": ["firenze", "careggi", "meyer", "santa maria nuova"],
    "Pisa": ["pisa", "cisanello"],
    "Livorno": ["livorno"],
    "Arezzo": ["arezzo"],
    "Pistoia": ["pistoia"],
    "Lucca": ["lucca", "versilia"],
    "Prato": ["prato"],
    "Grosseto": ["grosseto"],
    "Siena": ["siena", "le scotte"],
    "Massa-Carrara": ["massa", "carrara"]
  },
  "Trentino-Alto Adige": {
    "Trento": ["trento", "santa chiara", "rovereto"],
    "Bolzano": ["bolzano", "merano", "bressanone"]
  },
  "Umbria": {
    "Perugia": ["perugia", "santa maria della misericordia", "foligno", "città di castello"],
    "Terni": ["terni", "santa maria", "orvieto"]
  },
  "Valle d'Aosta": {
    "Aosta": ["aosta", "parini"]
  },
  "Veneto": {
    "Venezia": ["venezia", "mestre", "chioggia", "san donà"],
    "Verona": ["verona", "borgo trento", "borgo roma", "legnago"],
    "Padova": ["padova", "sant'antonio", "schiavonia"],
    "Vicenza": ["vicenza", "san bortolo", "bassano"],
    "Treviso": ["treviso", "conegliano"],
    "Rovigo": ["rovigo"],
    "Belluno": ["belluno", "feltre"]
  }
};

/**
 * Isola ed estrae il testo pulito dei SOLI risultati/appuntamenti effettivi,
 * rimuovendo completamente header, footer, script, stili e menu a tendina (<select>).
 */
function extractCleanAppointmentsText(html) {
  if (!html) return "";

  // 1. Se esiste il form specifico con i risultati di prenotazione, isoliamo il suo blocco
  const prenFormMatch = html.match(/<form[^>]*id=["']prenForm["'][^>]*>([\s\S]*?)<\/form>/i);
  let targetHtml = prenFormMatch ? prenFormMatch[1] : html;

  // 2. Se non c'è prenForm, cerchiamo il blocco id="content" escludendo il footer
  if (!prenFormMatch) {
    const cIdx = html.indexOf('id="content"');
    const fIdx = html.indexOf('id="footer"');
    if (cIdx !== -1) {
      targetHtml = fIdx > cIdx ? html.substring(cIdx, fIdx) : html.substring(cIdx);
    }
  }

  // 3. FONDAMENTALE: Rimuovi TUTTI i menu a tendina <select>...</select>
  // I menu a tendina del portale contengono l'elenco di tutte le AST/province (anche se non ci sono posti!)
  let cleaned = targetHtml.replace(/<select\b[^>]*>[\s\S]*?<\/select>/gi, " ");

  // 4. Rimuovi script, stili, navigation, header, footer e searchbar
  cleaned = cleaned
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, " ")
    .replace(/<header\b[^>]*>[\s\S]*?<\/header>/gi, " ")
    .replace(/<footer\b[^>]*>[\s\S]*?<\/footer>/gi, " ")
    .replace(/<nav\b[^>]*>[\s\S]*?<\/nav>/gi, " ")
    .replace(/<div[^>]*id=["']searchbar["'][^>]*>[\s\S]*?<\/div>/gi, " ")
    .replace(/<div[^>]*id=["']header["'][^>]*>[\s\S]*?<\/div>/gi, " ")
    .replace(/<div[^>]*id=["']menuTemplate["'][^>]*>[\s\S]*?<\/div>/gi, " ");

  // 5. Rimuovi tutti i tag HTML rimanenti
  cleaned = cleaned.replace(/<[^>]+>/g, " ");

  // 6. Normalizza spazi e caratteri
  cleaned = cleaned
    .replace(/&nbsp;/gi, " ")
    .replace(/&[a-z]+;/gi, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();

  return cleaned;
}

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

    // 5. Estrai il testo pulito dei SOLI risultati/appuntamenti effettivi (escludendo header, footer e menu a tendina)
    const appointmentsText = extractCleanAppointmentsText(searchText);
    console.log(`CUP Monitor (${region}): testo appuntamenti pulito:`, appointmentsText);

    // 6. Filtraggio territoriale per Provincia selezionata
    const selectedProvince = data.province || "Tutte";
    if (selectedProvince && selectedProvince !== "Tutte") {
      const regKeywords = REGIONAL_PROVINCES_KEYWORDS[region] || {};
      const provKeywords = regKeywords[selectedProvince] || [selectedProvince.toLowerCase()];
      const searchTerms = [selectedProvince.toLowerCase(), ...provKeywords];

      // Verifichiamo se almeno un presidio/comune della provincia richiesta compare negli appuntamenti
      const matchFound = searchTerms.some(term => appointmentsText.includes(term.toLowerCase()));

      if (!matchFound) {
        // Rileviamo se compare il nome di un'altra provincia della stessa regione
        let otherProvinceName = "";
        for (const [pName, pKeywords] of Object.entries(regKeywords)) {
          if (pName !== selectedProvince) {
            const otherTerms = [pName.toLowerCase(), ...pKeywords];
            if (otherTerms.some(t => appointmentsText.includes(t.toLowerCase()))) {
              otherProvinceName = pName;
              break;
            }
          }
        }

        const hint = otherProvinceName ? ` (trovato posto solo a ${otherProvinceName})` : "";
        console.log(`CUP Monitor: trovata disponibilità sul portale${hint}, ma NESSUNA in provincia di ${selectedProvince}.`);

        const res = {
          status: "NO_MATCH",
          message: `Disponibilità presente in altre province${hint}, ma nessuna in provincia di ${selectedProvince}. Il monitoraggio resta attivo.`,
          time: new Date().toLocaleTimeString()
        };
        await saveStatus(res);
        return res;
      }
    }

    // Se arriviamo qui, c'è disponibilità effettiva per la provincia selezionata (o per "Tutte"):
    const res = {
      status: "FOUND",
      message: `🎉 DISPONIBILITÀ TROVATA${selectedProvince !== "Tutte" ? " in provincia di " + selectedProvince : ""}! Clicca per prenotare subito.`,
      time: new Date().toLocaleTimeString()
    };

    notifyUser(`🎉 Posto Trovato (${selectedProvince !== "Tutte" ? selectedProvince : region})!`, res.message, true);
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
