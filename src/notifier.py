"""Modulo unificato per l'invio di notifiche Telegram e Telefono (WhatsApp/SMS).

Gestisce:
- Telegram Bot (@BotFather)
- WhatsApp gratuito via CallMeBot API
- SMS via Twilio (opzionale)

Supporta messaggi meme randomici e satirici sulla sanità italiana.
"""

import logging
import random
import urllib.parse
from pathlib import Path
from typing import Any
import requests

logger = logging.getLogger("cup_monitor")

# --- LISTE DI MESSAGGI MEME RANDOMICI ---

CONNECTION_MEMES = [
    "📡 *Connessione stabilita con il mainframe della Sanità!* 💻🏥\nAbbiamo agganciato il modem 56k a carbonella della Regione. Radar attivo e pronto a caccia di buchi!",
    "🚀 *Script connesso e operativo come una mina!* 💥🛜\nSistemi sincronizzati con il canale di notifica. Se si libera mezzo secondo di appuntamento, lo becchiamo al volo!",
    "🥷 *Siamo dentro! Il bot pattuglia la fortezza del CUP!* 🛡️🕹️\nConnessione stabilita. Radar puntato fisso sulle disponibilità!",
    "🔌 *Contatto stabilito con la burocrazia sanitaria!* 📠📋\nIl criceto sulla ruota dei server ha iniziato a correre. Monitoraggio attivo a 360°!",
    "🤖 *Bot CUP online!* 🦾⚡\nPronto a fare a pugni virtuali contro le liste d'attesa del 2042. Canali di notifica verificati al 100%!",
]

LOGIN_SUCCESS_MEMES = [
    "🎉 *SPID accettato dai potenti server regionali!* 🪪\nSessione salvata con successo. Il bot ha ripreso a pattugliare le liste d'attesa come un falco 🦅",
    "🔓 *Porta della Regione scardinata con successo!* 🏰\nLa sessione è attiva. Ora ci piazziamo davanti allo sportello virtuale e non ci muoviamo più 🩺⏱️",
    "☕ *Fine della pausa caffè per i server!* 💻\nLogin registrato. Il radar è di nuovo a caccia di miracoli 🎯",
]

NO_MATCH_MEMES = [
    "ℹ️ *Nessuna disponibilità nei territori selezionati...*\n\nQuelli fadigano troppo 🥵... dagli tregua porelli 🛑 (prendono anche troppo poco 💸)",
    "🕸️ *Deserto totale nelle agende sanitarie...*\n\nNon c'è posto neanche per farsi misurare la febbre 🌡️. Le agende forse riaprono nel 2039, nel dubbio mangiati un ciauscolo e stappa un Verdicchio 🥖🍷",
    "⏳ *Il CUP dice: RITENTA SARAI PIÙ FORTUNATO*\n\nZero buchi liberi 🚫. I medici sono fuggiti o stanno ancora decifrando una ricetta scritta in geroglifico su carta carbone 📠🧑‍⚕️",
    "🙅‍♂️ *Tutto blindato! Mancano solo i cecchini all'ingresso* 🎯\n\nNemmeno con una supplica a San Ciriaco si trova una data utile oggi ⛪. Continuiamo a monitorare sereni a oltranza ⛏️",
    "🐢 *Velocità del SSN: bradipo in letargo*\n\nNessuna visita disponibile nei paraggi 🕳️. Pare che il prossimo buco libero coincida con la data della pensione di tutti noi 👴👵",
    "📭 *Buca delle lettere vuota: zero disponibilità*\n\nAbbiamo scansionato tutti gli ospedali e presidi configurati, ma regna la quiete più assoluta 🧘‍♂️. Ci riproviamo al prossimo controllo!",
]

SESSION_EXPIRED_MEMES = [
    "🛋️ *Bot in stand-by (fine sessione SPID)* ☕\n\nNessun errore e nessun server da riavviare: per motivi di sicurezza lo SPID dura solo poche ore.\nIl bot resta attivo e funzionante in background; quando hai tempo per riagganciare la sessione, basta lanciare:\n`python src/main.py --login`",
    "🛡️ *Pausa tecnica SPID (normativa regionale)* 📋\n\nIl portale regionale ha chiuso l'accesso per limite di tempo (tutto regolare, nessun blocco!). Lo script è sempre pronto in background.\nQuando vuoi riprendere le ricerche, ricollegalo con:\n`python src/main.py --login`",
    "🪪 *Rinnovo SPID periodico* ⏳\n\nLa sessione temporanea è terminata per sicurezza. Nessun crash: il bot continua a vegliare!\nPer sbloccare di nuovo le interrogazioni quando sei comodo:\n`python src/main.py --login`",
]

MATCH_MEMES = [
    "🚨 *MIRACOLO DEL SSN!* 🚨\n\nQualcuno ha disdetto o si sono accorti di avere un medico in corsia! Hanno trovato un buco:\n\n{body}\n\n🏃‍♂️💨 *Corri a prenotare prima che se ne accorga la Regione!*",
    "🍾 *EVENTO EPOCALE NELLE DISPONIBILITÀ!* 🎉\n\nSi è liberato un posto! Nemmeno l'allineamento dei pianeti produceva un evento così raro 🪐:\n\n{body}\n\n⚡ *Vola sul portale CUP prima che svanisca nel vuoto quantico!*",
    "🎯 *COLPO GROSSO! BUCO TROVATO!* 🏥💥\n\nLa tenacia ha pagato! Abbiamo beccato una data utile prima che andasse esaurita:\n\n{body}\n\n📲 *Accedi subito e chiudi la prenotazione!*",
]

ERROR_MEMES = [
    "💥 *Qualcosa è esploso nei meandri del portale CUP!*",
    "🤦‍♂️ *I server regionali hanno tirato le cuoia momentaneamente*",
    "🧯 *Fumo nella sala macchine della Regione*",
    "🌪️ *Vortice burocratico imprevisto nel sistema sanitario*",
]


class TelegramChannel:
    """Invio messaggi tramite Telegram Bot API."""

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token.strip() if bot_token else ""
        self.chat_id = str(chat_id).strip() if chat_id else ""
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id and self.bot_token != "INSERIRE_BOT_TOKEN")

    def send(self, text: str, parse_mode: str = "Markdown") -> bool:
        if not self.is_configured:
            return False
        try:
            payload: dict[str, Any] = {"chat_id": self.chat_id, "text": text}
            if parse_mode:
                payload["parse_mode"] = parse_mode
            res = requests.post(self.api_url, json=payload, timeout=10)
            if res.status_code != 200 and parse_mode and "can't parse entities" in res.text.lower():
                payload.pop("parse_mode", None)
                res = requests.post(self.api_url, json=payload, timeout=10)
            return res.status_code == 200 and res.json().get("ok", False)
        except Exception as e:
            logger.error("Errore invio Telegram: %s", e)
            return False


class WhatsAppChannel:
    """Invio messaggi WhatsApp gratuiti via CallMeBot API."""

    def __init__(self, phone_number: str, api_key: str) -> None:
        self.phone = "".join(filter(str.isdigit, phone_number or ""))
        self.api_key = (api_key or "").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.phone and self.api_key and self.api_key != "INSERIRE_API_KEY_CALLMEBOT")

    def send(self, text: str) -> bool:
        if not self.is_configured:
            return False
        try:
            # Pulisce markdown per WhatsApp (*grassetto* è supportato, rimuove markdown non supportato)
            clean_text = text.replace("`", "")
            encoded_text = urllib.parse.quote(clean_text)
            url = f"https://api.callmebot.com/whatsapp.php?phone={self.phone}&text={encoded_text}&apikey={self.api_key}"
            res = requests.get(url, timeout=15)
            return res.status_code == 200
        except Exception as e:
            logger.error("Errore invio WhatsApp: %s", e)
            return False


class SMSChannel:
    """Invio SMS via Twilio API."""

    def __init__(self, account_sid: str, auth_token: str, from_number: str, to_number: str) -> None:
        self.account_sid = (account_sid or "").strip()
        self.auth_token = (auth_token or "").strip()
        self.from_number = (from_number or "").strip()
        self.to_number = (to_number or "").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_number and self.to_number and "INSERIRE" not in self.account_sid)

    def send(self, text: str) -> bool:
        if not self.is_configured:
            return False
        try:
            # Gli SMS non supportano markdown e devono essere concisi
            plain_text = text.replace("*", "").replace("`", "")
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            res = requests.post(
                url,
                data={"From": self.from_number, "To": self.to_number, "Body": plain_text},
                auth=(self.account_sid, self.auth_token),
                timeout=10,
            )
            return res.status_code in (200, 201)
        except Exception as e:
            logger.error("Errore invio SMS: %s", e)
            return False


class NotificationDispatcher:
    """Gestore unificato delle notifiche multi-canale (Telegram / WhatsApp / SMS)."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        config = config or {}
        notif_cfg = config.get("notifications", {})
        
        # Supporta sia la nuova configurazione annidata che quella legacy
        self.channel = notif_cfg.get("channel", "telegram")
        
        # Canale Telegram
        tg_cfg = notif_cfg.get("telegram") or config.get("telegram", {})
        self.telegram = TelegramChannel(
            bot_token=tg_cfg.get("bot_token", ""),
            chat_id=tg_cfg.get("chat_id", ""),
        )

        # Canale WhatsApp (Telefono)
        wa_cfg = notif_cfg.get("whatsapp", {})
        self.whatsapp = WhatsAppChannel(
            phone_number=wa_cfg.get("phone_number", ""),
            api_key=wa_cfg.get("api_key", ""),
        )

        # Canale SMS (Telefono)
        sms_cfg = notif_cfg.get("sms", {})
        self.sms = SMSChannel(
            account_sid=sms_cfg.get("account_sid", ""),
            auth_token=sms_cfg.get("auth_token", ""),
            from_number=sms_cfg.get("from_number", ""),
            to_number=sms_cfg.get("to_number", ""),
        )

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Invia un messaggio attraverso i canali configurati."""
        sent_any = False
        target = self.channel.lower()

        # Invio Telegram
        if target in ("telegram", "both", "all") or (target not in ("whatsapp", "sms") and self.telegram.is_configured):
            if self.telegram.is_configured:
                ok = self.telegram.send(text, parse_mode=parse_mode)
                if ok:
                    sent_any = True

        # Invio WhatsApp (Telefono)
        if target in ("whatsapp", "phone", "both", "all") or (self.whatsapp.is_configured and target == "whatsapp"):
            if self.whatsapp.is_configured:
                ok = self.whatsapp.send(text)
                if ok:
                    sent_any = True

        # Invio SMS (Telefono)
        if target in ("sms", "phone", "both", "all") or (self.sms.is_configured and target == "sms"):
            if self.sms.is_configured:
                ok = self.sms.send(text)
                if ok:
                    sent_any = True

        if sent_any:
            logger.info("Messaggio di notifica inviato con successo.")
        else:
            logger.warning("Nessun canale di notifica è riuscito a recapitare il messaggio.")
        return sent_any

    def notify_match(self, results: list[dict]) -> bool:
        try:
            if not results:
                return False
            items = []
            for item in results:
                struttura = item.get("struttura", "N/D")
                indirizzo = item.get("indirizzo", "N/D")
                data = item.get("data", "N/D")
                ora = item.get("ora", "N/D")
                prestazione = item.get("prestazione", "N/D")
                items.append(
                    f"🏥 *Struttura:* {struttura}\n"
                    f"📍 *Indirizzo:* {indirizzo}\n"
                    f"📅 *Data:* {data}\n"
                    f"🕐 *Ora:* {ora}\n"
                    f"💊 *Prestazione:* {prestazione}"
                )
            body = "\n\n---\n\n".join(items)
            template = random.choice(MATCH_MEMES)
            return self.send_message(template.format(body=body))
        except Exception as e:
            logger.error("Errore notifica disponibilità: %s", e)
            return False

    def notify_no_match(self) -> bool:
        try:
            return self.send_message(random.choice(NO_MATCH_MEMES))
        except Exception as e:
            logger.error("Errore notifica mancata disponibilità: %s", e)
            return False

    def notify_session_expired(self) -> bool:
        try:
            flag_file = Path("session/expired_notified.flag")
            if flag_file.exists():
                logger.info("Notifica sessione scaduta già inviata in precedenza. Salto duplicato.")
                return True
            sent = self.send_message(random.choice(SESSION_EXPIRED_MEMES))
            if sent:
                flag_file.parent.mkdir(parents=True, exist_ok=True)
                flag_file.write_text("notified", encoding="utf-8")
            return sent
        except Exception as e:
            logger.error("Errore notifica sessione scaduta: %s", e)
            return False

    def notify_login_success(self) -> bool:
        try:
            flag_file = Path("session/expired_notified.flag")
            if flag_file.exists():
                flag_file.unlink(missing_ok=True)
            return self.send_message(random.choice(LOGIN_SUCCESS_MEMES))
        except Exception as e:
            logger.error("Errore notifica login: %s", e)
            return False

    def notify_error(self, error_type: str, details: str = "") -> bool:
        try:
            header = random.choice(ERROR_MEMES)
            msg = f"{header}\n\n❌ *Dettaglio:* {error_type}" + (f"\n{details}" if details else "")
            return self.send_message(msg)
        except Exception as e:
            logger.error("Errore notifica errore: %s", e)
            return False

    def test_connection(self) -> bool:
        try:
            return self.send_message(random.choice(CONNECTION_MEMES))
        except Exception as e:
            logger.error("Errore test connessione: %s", e)
            return False


# Retrocompatibilità per codice esistente che importa TelegramNotifier
TelegramNotifier = NotificationDispatcher
