import os
import logging
import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext, Page, Error as PlaywrightError

logger = logging.getLogger('cup_monitor')

class SessionManager:
    """Gestisce la sessione di login tramite Playwright."""
    
    def __init__(self, storage_path: str, base_url: str, page_timeout_ms: int = 30000):
        self.storage_path = Path(storage_path)
        self.base_url = base_url
        self.page_timeout_ms = page_timeout_ms

    def session_exists(self) -> bool:
        """Verifica se il file di sessione esiste e non è vuoto."""
        try:
            return self.storage_path.exists() and self.storage_path.stat().st_size > 0
        except Exception as e:
            logger.error(f"Errore nel controllo dell'esistenza della sessione: {e}")
            return False

    def is_session_valid(self) -> bool:
        """Verifica se la sessione esiste ed è stata modificata nelle ultime 4 ore."""
        if not self.session_exists():
            return False
            
        try:
            mtime = os.path.getmtime(self.storage_path)
            now = datetime.datetime.now().timestamp()
            # 4 ore = 14400 secondi
            if (now - mtime) < 14400:
                return True
            return False
        except Exception as e:
            logger.error(f"Errore nel controllo della validità della sessione: {e}")
            return False

    def interactive_login(self) -> bool:
        """
        Lancia un browser in modalità headful per permettere all'utente di 
        effettuare il login SPID manualmente, poi salva la sessione.
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False, slow_mo=100)
                context = browser.new_context()
                page = context.new_page()
                page.set_default_timeout(self.page_timeout_ms)
                
                logger.info(f"Navigazione verso: {self.base_url}")
                page.goto(self.base_url)
                
                print("\nEffettua il login SPID nel browser aperto. Premi INVIO qui quando hai completato il login...")
                input()
                
                # Assicura che la cartella padre esista
                self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Salva lo stato
                context.storage_state(path=str(self.storage_path))
                logger.info(f"Sessione salvata con successo in {self.storage_path}")

                # Rimuove l'eventuale flag di notifica scadenza
                flag_file = self.storage_path.parent / "expired_notified.flag"
                if flag_file.exists():
                    flag_file.unlink(missing_ok=True)
                
                browser.close()
                return True
        except Exception as e:
            logger.error(f"Errore durante il login interattivo: {e}")
            return False

    def create_context(self, browser) -> BrowserContext:
        """Crea un BrowserContext, utilizzando lo state file se esistente."""
        try:
            if self.session_exists():
                logger.info(f"Ripristino sessione da: {self.storage_path}")
                return browser.new_context(storage_state=str(self.storage_path))
            else:
                logger.info("Nessuna sessione trovata, creazione di un nuovo contesto vuoto.")
                return browser.new_context()
        except PlaywrightError as e:
            logger.error(f"Errore nella creazione del context: {e}")
            raise

    def save_session(self, context: BrowserContext) -> None:
        """Salva lo stato corrente del contesto di navigazione."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(self.storage_path))
            logger.info("Sessione aggiornata e salvata.")
        except Exception as e:
            logger.error(f"Errore nel salvataggio della sessione: {e}")

    def check_login_redirect(self, page: Page) -> bool:
        """
        Verifica se la pagina corrente ha subito un redirect al login.
        Ritorna True se la sessione sembra non valida/scaduta.
        """
        url = page.url.lower()
        if 'cohesion' in url or 'login' in url or 'wayf' in url:
            logger.warning(f"Redirect di login rilevato: {page.url}")
            return True
        return False
