"""Server Web Locale e Dashboard Grafica per CUP Monitor.

Avvia una dashboard interattiva su http://localhost:5000 che consente di:
- Usare il configuratore guidato direttamente dal browser
- Salvare automaticamente il file config.yaml
- Testare le notifiche (Telegram / WhatsApp / SMS) con un click
- Avviare la procedura di login SPID con un click

Utilizza esclusivamente librerie standard di Python (nessuna dipendenza extra).
"""

import http.server
import json
import logging
import os
import socketserver
import subprocess
import sys
import webbrowser
from pathlib import Path

import time
from urllib.parse import urlparse

PORT = 5000
BASE_DIR = Path(__file__).parent.resolve()
DOCS_DIR = BASE_DIR / "docs"

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("web_dashboard")

_last_subprocess_time = 0.0


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS_DIR), **kwargs)

    def end_headers(self):
        # Header di sicurezza HTTP universali
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        if self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/status":
            session_file = BASE_DIR / "session" / "state.json"
            config_file = BASE_DIR / "config.yaml"
            data = {
                "ok": True,
                "config_exists": config_file.exists(),
                "session_exists": session_file.exists() and session_file.stat().st_size > 0,
            }
            self._send_json(data)
            return
        super().do_GET()

    def do_POST(self):
        # Protezione anti-CSRF rigorosa: convalida precisa di Origin e Referer
        origin = self.headers.get("Origin") or self.headers.get("Referer", "")
        if not origin:
            logger.warning("Bloccata richiesta POST senza header Origin o Referer.")
            self.send_error(403, "Accesso negato: richiesta non locale.")
            return

        try:
            parsed = urlparse(origin)
            allowed_hosts = ("localhost", "127.0.0.1")
            if parsed.hostname not in allowed_hosts or parsed.port != PORT:
                logger.warning("Bloccata richiesta non autorizzata da host '%s' porta '%s'", parsed.hostname, parsed.port)
                self.send_error(403, "Accesso negato: le API locali accettano comandi solo da localhost:5000")
                return
        except Exception as e:
            logger.error("Errore analisi origin: %s", e)
            self.send_error(403, "Accesso negato")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        # Limite anti-DoS sul payload (max 1 MB)
        if content_length > 1024 * 1024:
            self.send_error(413, "Payload troppo grande")
            return

        body = self.rfile.read(content_length)

        if self.path == "/api/save-config":
            try:
                yaml_text = body.decode("utf-8")
                # Convalida sintattica e strutturale YAML prima del salvataggio
                try:
                    import yaml
                    parsed_yaml = yaml.safe_load(yaml_text)
                    if not isinstance(parsed_yaml, dict):
                        self._send_json({"ok": False, "message": "Struttura YAML non valida (deve essere un oggetto di configurazione)."}, status=400)
                        return
                except ImportError:
                    pass
                except Exception as parse_err:
                    self._send_json({"ok": False, "message": f"Errore di sintassi YAML: {parse_err}"}, status=400)
                    return

                target_file = BASE_DIR / "config.yaml"
                target_file.write_text(yaml_text, encoding="utf-8")
                logger.info("File config.yaml salvato con successo dal pannello web.")
                self._send_json({"ok": True, "message": "✅ File config.yaml salvato con successo sul tuo computer!"})
            except Exception as e:
                logger.error("Errore salvataggio config: %s", e)
                self._send_json({"ok": False, "message": f"❌ Errore salvataggio: {e}"}, status=500)
            return

        elif self.path in ("/api/test-notification", "/api/login-spid"):
            # Protezione anti-flood / DoS da processi multipli concorrenti
            global _last_subprocess_time
            now = time.time()
            if now - _last_subprocess_time < 5.0:
                self._send_json({"ok": False, "message": "Attendi qualche secondo prima di richiedere una nuova operazione."}, status=429)
                return
            _last_subprocess_time = now

            if self.path == "/api/test-notification":
                try:
                    subprocess.Popen([sys.executable, str(BASE_DIR / "src" / "main.py"), "--test-telegram"])
                    self._send_json({"ok": True, "message": "🚀 Notifica di test inviata! Controlla Telegram o il tuo Telefono."})
                except Exception as e:
                    self._send_json({"ok": False, "message": f"❌ Errore avvio test: {e}"}, status=500)
                return

            elif self.path == "/api/login-spid":
                try:
                    subprocess.Popen(
                        [sys.executable, str(BASE_DIR / "src" / "main.py"), "--login"],
                        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
                    )
                    self._send_json({
                        "ok": True,
                        "message": "🔑 Finestra browser aperta sul PC! Esegui il login SPID e premi INVIO nel terminale che è comparso.",
                    })
                except Exception as e:
                    self._send_json({"ok": False, "message": f"❌ Errore avvio SPID: {e}"}, status=500)
                return

        self.send_error(404, "Endpoint non trovato")

    def _send_json(self, data: dict, status: int = 200):
        res = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(res)))
        self.end_headers()
        self.wfile.write(res)


def main():
    if not DOCS_DIR.exists():
        print(f"Errore: Cartella {DOCS_DIR} non trovata.")
        sys.exit(1)

    print("=" * 60)
    print(f"🏥 CUP Monitor — Interfaccia Grafica Web in esecuzione!")
    print(f"🌐 Aperta all'indirizzo: http://localhost:{PORT}")
    print("=" * 60)
    print("Premi CTRL+C per chiudere il server.\n")

    # Tenta di aprire automaticamente il browser
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except Exception:
        pass

    with socketserver.TCPServer(("127.0.0.1", PORT), DashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer web arrestato.")


if __name__ == "__main__":
    main()
