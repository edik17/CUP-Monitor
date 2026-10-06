# 🏥 CUP Monitor — Assistente Intelligente per Prenotazioni Sanitarie

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Configurator-emerald)](docs/index.html)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: Proprietary / All Rights Reserved](https://img.shields.io/badge/License-Proprietary%20%7C%20All%20Rights%20Reserved-red.svg)](LICENSE)
[![Privacy First](https://img.shields.io/badge/Privacy-100%25%20Locale-green.svg)](#-privacy-e-sicurezza-dei-dati)

Un assistente intelligente automatizzato e protetto che monitora costantemente le agende dei portali sanitari (CUP) per trovare appuntamenti, visite o esami anticipati non appena si libera un posto (disdette o nuove agende), inviando notifiche istantanee via **Telegram** o **Telefono (WhatsApp / SMS)**.

---

## 🌟 Caratteristiche Principali

- 🌐 **Sito Web & Configuratore Guidato**: Interfaccia grafica moderna (ospitabile gratis su GitHub Pages) che guida l'utente nella configurazione passo-passo.
- 🧩 **Due Modalità a Scelta**:
  - **Strada Messaggistica**: Script background con notifiche push su **Telegram**, **WhatsApp** o **SMS**.
  - **Strada Web Browser**: Estensione Chrome/Edge per fare **tutto nel browser al 100% senza terminale**.
- 🗺️ **Filtro Territoriale Flessibile**: Scegli una o più province/città accettabili (es. Ancona, Macerata, Pesaro-Urbino, o l'intera regione) per escludere strutture troppo lontane.
- 🛡️ **Autenticazione Sicura con SPID**: Interazione umana con OTP nel browser dell'utente e session persistence locale.
- ⏰ **Automazione Flessibile**: Scegli ogni quanto eseguire il controllo (ogni 15 min, 30 min, 1 ora, 2 ore).
- 🎭 **Messaggi Satirici & Meme**: Notifiche scritte con ironia sulla sanità italiana e le attese burocratiche.

---

## 🔒 Privacy e Sicurezza dei Dati

> [!IMPORTANT]
> **I tuoi dati sanitari non lasciano mai il tuo computer.**
> Questo repository è strutturato in modo che **nessun dato personale** (Codice Fiscale, NRE, numeri di telefono o cookie di sessione SPID) venga caricato su GitHub:
> - Il file `.gitignore` blocca automaticamente `config.yaml`, la cartella `session/` e tutti i `logs/`.
> - Il sito web frontend (`docs/index.html`) viene eseguito al 100% all'interno del browser dell'utente (lato client) senza salvare nulla online.

---

## 🚀 Come Pubblicare il Sito su GitHub Pages

Puoi pubblicare gratuitamente il configuratore guidato per te o per altri utenti in 2 passaggi:

1. Fai il push di questo repository sul tuo profilo GitHub.
2. Vai su **Settings** del repository → **Pages** (sulla barra a sinistra):
   - Sotto **Build and deployment** > **Source**, seleziona `Deploy from a branch`.
   - Seleziona il branch `main` (o `master`) e imposta la cartella su `/docs`.
   - Clicca **Save**.
3. In meno di 60 secondi il tuo sito sarà online all'indirizzo `https://<tuo-username>.github.io/<nome-repo>/`!

---

## 💻 Installazione & Uso Locale

### 1. Prerequisiti
- **Python 3.10+** installato ([python.org](https://www.python.org/downloads/))

### 2. Clona il repository
```bash
git clone https://github.com/TuoUsername/CUP-Monitor.git
cd CUP-Monitor
```

### 3. Installa le dipendenze
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 🖥️ Modalità 1: Dashboard Grafica Locale (Consigliata)

Puoi avviare l'interfaccia grafica direttamente sul tuo PC con:
```bash
python web_app.py
```
Si aprirà automaticamente il browser su `http://localhost:5000`:
- Configura canali di notifica, province e ricetta con la procedura guidata.
- Clicca **"Salva in config.yaml"** per applicare la configurazione.
- Clicca **"Fai Login SPID"** per aprire il browser e autenticarti.
- Clicca **"Testa Notifica Ora"** per verificare che i messaggi arrivino.

---

## ⌨️ Modalità 2: Da Riga di Comando (CLI)

Se preferisci lavorare da terminale:

1. Copia il template di configurazione:
   ```bash
   copy config.example.yaml config.yaml
   ```
2. Modifica `config.yaml` inserendo il tuo Codice Fiscale, NRE e credenziali di notifica.
3. Effettua il login SPID iniziale:
   ```bash
   python src/main.py --login
   ```
4. Esegui il monitoraggio manuale:
   ```bash
   python src/main.py --debug
   ```

---

## 🧩 Modalità 3: Estensione Web Browser (Zero Terminale • 100% nel Browser)

Se non vuoi installare Python o usare il terminale, puoi eseguire il monitoraggio direttamente all'interno del browser:

1. Apri Google Chrome o Microsoft Edge e vai alla pagina delle estensioni:
   - Su Chrome / Brave: `chrome://extensions`
   - Su Edge: `edge://extensions`
2. Attiva l'interruttore **"Modalità sviluppatore"** in alto a destra.
3. Clicca su **"Carica estensione non pacchettizzata"** e seleziona la cartella [`extension/`](extension/) di questo repository.
4. Clicca sull'icona 🏥 in alto a destra del browser, inserisci il tuo **NRE**, **Codice Fiscale** e seleziona la frequenza desiderata.
5. Clicca su *"Apri Portale CUP per SPID"* ed effettua il login SPID nel browser.
6. Clicca su *"Avvia Monitoraggio"*: l'estensione verificherà le disponibilità in background e ti invierà **notifiche desktop native** appena si libera un posto!

#### 🛑 Come annullare o fermare nell'estensione:
- Clicca sull'icona dell'estensione e premi **"Ferma Monitoraggio"**, oppure disattiva l'estensione con un clic da `chrome://extensions`.

---

## ⏰ Esecuzione Automatica (Ogni 30 Minuti)

### Su Windows (Task Scheduler)
È già presente lo script [`run_bot.bat`](run_bot.bat). Per registrarlo automaticamente tra le attività pianificate di Windows:

```powershell
$action = New-ScheduledTaskAction -Execute "$PWD\run_bot.bat"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -TaskName "CUP Marche Monitor" -Force
```

### Su Linux / Mac (Crontab)
```cron
*/30 * * * * cd /percorso/progetto && python3 src/main.py >> logs/scheduler.log 2>&1
```

### 🛑 Come Annullare o Fermare il Monitoraggio
Quando hai finalmente prenotato la visita o l'esame desiderato e vuoi fermare il bot per non ricevere più notifiche:

**Su Windows (PowerShell):**
```powershell
Unregister-ScheduledTask -TaskName "CUP Marche Monitor" -Confirm:$false
```
*In alternativa, apri l'app di sistema **Utilità di pianificazione** (`taskschd.msc`), fai clic destro su **"CUP Marche Monitor"** e seleziona **Elimina**.*

**Su Linux / Mac:**
Apri il crontab con `crontab -e` e cancella la riga del bot.

---

## 📁 Struttura del Progetto

```
CUP-Monitor/
├── .gitignore               # Protezione dati sensibili per GitHub
├── config.example.yaml      # Template pubblico pulito
├── requirements.txt         # Dipendenze Python
├── web_app.py               # Server locale con dashboard interattiva
├── run_bot.bat              # Script batch per Windows Task Scheduler
├── README.md                # Questa guida
├── docs/                    # Sito web per GitHub Pages
│   └── index.html           # Single Page Application con Wizard interattivo
└── src/
    ├── __init__.py
    ├── main.py              # Entry point orchestratore
    ├── auth.py              # Gestione sessione e login SPID Playwright
    ├── scraper.py           # Scraping automatizzato modulo NRE
    ├── filter.py            # Catalogo territoriale e filtri multi-provincia
    ├── notifier.py          # Notifiche multi-canale (Telegram, WhatsApp, SMS)
    ├── logger_setup.py      # Gestione file di log rotativi
    └── get_chat_id.py       # Helper per trovare il Chat ID Telegram
```

---

## 📜 Licenza e Diritti d'Autore
 
Copyright © 2026 **Edoardo Dottori (Edik1700)**. Tutti i diritti riservati (*All Rights Reserved*).
 
Questo software è protetto da licenza proprietaria esclusiva ad uso personale:
- ✅ **Uso consentito**: Gratuito per cittadini e utenti privati per monitorare le proprie prenotazioni sanitarie locali.
- 🚫 **Divieto di alterazione**: È severamente vietato modificare, manomettere, decompilare o creare versioni derivate non autorizzate (*fork*).
- 🚫 **Divieto di ridistribuzione**: È vietato ripubblicare o distribuire il software o l'estensione su store terzi (Chrome Web Store, Edge Add-ons, ecc.) o altri siti senza consenso scritto.
- 🚫 **Divieto commerciale**: È vietata la vendita, monetizzazione o inclusione in pacchetti a pagamento.
 
Consulta il testo integrale e vincolante nel file [LICENSE](LICENSE).
