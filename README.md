# 🏥 CUP Monitor — Assistente Intelligente per Prenotazioni Sanitarie

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Configurator-emerald)](docs/index.html)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Privacy First](https://img.shields.io/badge/Privacy-100%25%20Locale-green.svg)](#-privacy-e-sicurezza-dei-dati)

Un assistente open-source automatizzato che monitora costantemente le agende dei portali sanitari (CUP) per trovare appuntamenti, visite o esami anticipati non appena si libera un posto (disdette o nuove agende), inviando notifiche istantanee via **Telegram** o **Telefono (WhatsApp / SMS)**.

---

## 🌟 Caratteristiche Principali

- 🌐 **Sito Web & Configuratore Guidato**: Interfaccia grafica moderna (ospitabile gratis su GitHub Pages) che guida l'utente nella configurazione passo-passo.
- 📱 **Canali di Notifica a Scelta**:
  - **Bot Telegram**: notifiche push istantanee gratuite e illimitate.
  - **WhatsApp (Telefono)**: notifiche gratuite tramite webhook CallMeBot.
  - **SMS (Telefono)**: supporto a SMS tradizionali tramite Twilio.
- 🗺️ **Filtro Territoriale Flessibile**: Scegli una o più province/città accettabili (es. Ancona, Macerata, Pesaro-Urbino, o l'intera regione) per escludere strutture troppo lontane.
- 🛡️ **Autenticazione Sicura con SPID**: Interazione umana con OTP nel browser dell'utente e session persistence locale.
- ⏰ **Automazione 24/7 in Background**: Esecuzione silenziosa e programmata ogni 30 minuti tramite Task Scheduler di Windows o Cron Linux.
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

## 📜 Licenza

Rilasciato sotto licenza [MIT](LICENSE). Utilizzo consentito per fini personali e non commerciali.
