import logging
import time
import random
import datetime
from pathlib import Path
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger('cup_monitor')

class NREScraper:
    """Gestisce l'estrazione delle disponibilità a partire da NRE e Codice Fiscale."""
    
    def __init__(self, page_timeout_ms: int = 30000, action_delay_ms: int = 2000):
        self.page_timeout_ms = page_timeout_ms
        self.action_delay_ms = action_delay_ms

    def _random_delay(self) -> None:
        """Introduce un ritardo casuale per simulare il comportamento umano."""
        delay = self.action_delay_ms * random.uniform(0.75, 1.25) / 1000.0
        time.sleep(delay)

    def _dismiss_cookie_banner(self, page: Page) -> None:
        """Tenta di chiudere il banner dei cookie se presente."""
        selectors = [
            '#bannerPrivacy button.btn-primary',
            '#bannerPrivacy .btn-primary'
        ]
        
        for sel in selectors:
            try:
                locator = page.locator(sel)
                if locator.count() > 0 and locator.first.is_visible(timeout=3000):
                    locator.first.click(timeout=3000)
                    logger.debug("Banner dei cookie chiuso con successo.")
                    self._random_delay()
                    return
            except Exception:
                continue
        logger.debug("Nessun banner dei cookie trovato o impossibile da chiudere.")

    def _take_error_screenshot(self, page: Page, error_name: str) -> str:
        """Salva uno screenshot per facilitare il debug degli errori."""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = Path('logs') / f'error_{error_name}_{timestamp}.png'
        
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(filepath))
            logger.info(f"Screenshot di errore salvato in: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Errore nel salvataggio dello screenshot: {e}")
            return ""

    def search_nre(self, page: Page, nre: str, codice_fiscale: str) -> list[dict]:
        """
        Compila il modulo NRE e ricerca le disponibilità.
        
        Restituisce una lista di dizionari con i risultati.
        """
        try:
            page.set_default_timeout(self.page_timeout_ms)
            
            # 1. Chiudi banner
            self._dismiss_cookie_banner(page)
            
            # 2. Attendi caricamento base della pagina
            page.wait_for_load_state('domcontentloaded')
            
            # 3. Compilazione Form NRE 
            # Il portale CUP Marche divide l'NRE in due campi: matrice1 (max 7) e matrice2 (max 12)
            # Solitamente l'NRE completo è di 15 caratteri (es. 1100AXXXXXXXXXX)
            
            # Estraiamo i campi, basandoci sulla lunghezza tipica dell'NRE 
            # Se è di 15 caratteri, i primi 3 o 5 potrebbero essere la matrice1.
            # Il sistema sembra pre-compilare matrice1 con "1100A", ma assicuriamoci di gestirlo.
            
            nre = nre.strip()
            
            # Trova matrice1 e matrice2
            matrice1_loc = page.locator("#matrice1")
            matrice2_loc = page.locator("#matrice2")
            
            if matrice1_loc.count() > 0 and matrice2_loc.count() > 0:
                # Modello a 2 campi
                # Proviamo a dividere l'NRE. Se è di 15 caratteri, spesso è 3 + 12 (es 010 + 12 numeri)
                # Oppure 5 + 10. Se matrice1 ha già un valore pre-compilato (es. 1100A)
                
                # Se l'utente ha inserito 15 caratteri e non capiamo, proviamo a dividerlo logicamente.
                # Per ora, proviamo a lasciare matrice1 intatto se è precompilato e l'NRE fornito è corto (es. solo l'identificativo),
                # altrimenti lo dividiamo brutalmente per far stare tutto nei max-lengths.
                
                # Fallback sicuro: cerca di far fittare NRE nei due campi.
                if len(nre) > 12:
                    part1 = nre[:-12]
                    part2 = nre[-12:]
                else:
                    part1 = ""
                    part2 = nre

                # Riempi se ha senso
                if part1:
                    matrice1_loc.first.fill(part1)
                matrice2_loc.first.fill(part2)
                
                logger.info("Form NRE compilato nei campi del portale.")
            else:
                # Modello a 1 campo (fallback se la UI cambia)
                nre_selectors = [
                    "input[name*='nre' i]:not([type='hidden'])", 
                    "input[id*='nre' i]:not([type='hidden'])", 
                    "input[placeholder*='NRE' i]:not([type='hidden'])", 
                    "#nre"
                ]
                
                nre_filled = False
                for sel in nre_selectors:
                    if page.locator(sel).count() > 0:
                        try:
                            page.locator(sel).first.fill(nre, timeout=3000)
                            nre_filled = True
                            logger.info("Form NRE compilato (modello singolo campo).")
                            break
                        except PlaywrightTimeoutError:
                            continue
                
                if not nre_filled:
                    logger.warning("Campi NRE non trovati o non scrivibili.")
            
            self._random_delay()
            
            # 5. Il codice fiscale è in un campo nascosto id="cf"
            # In genere non è necessario toccarlo se è già precompilato correttamente dal login SPID
            cf_loc = page.locator("#cf")
            if cf_loc.count() > 0:
                cf_val = cf_loc.first.get_attribute("value")
                masked_cf = f"{cf_val[:6]}******{cf_val[-3:]}" if cf_val and len(cf_val) == 16 else "***"
                logger.info(f"Codice Fiscale precompilato verificato: {masked_cf}")
            
            self._random_delay()
            
            # 7. Trova e clicca il pulsante Cerca
            btn_selectors = [
                "input[value='Ricerca']",
                "button:has-text('Ricerca')",
                "input[type='button'][onclick='submit()']",
                ".btn-primary[value='Ricerca']",
                "button[type='submit']",
                "input[type='submit']:not([type='hidden'])"
            ]
            
            btn_clicked = False
            for sel in btn_selectors:
                locator = page.locator(sel).first
                if locator.count() > 0 and locator.is_visible():
                    locator.click()
                    btn_clicked = True
                    logger.info("Pulsante di ricerca cliccato.")
                    break
            
            if not btn_clicked:
                logger.error("Impossibile trovare il pulsante di ricerca.")
                self._take_error_screenshot(page, "search_btn_not_found")
                return []
            
            # 8. Attendi caricamento risultati
            try:
                page.wait_for_load_state('networkidle', timeout=self.page_timeout_ms)
                # Attendi specificamente che la pagina cambi o appaia un nuovo elemento
                # page.wait_for_selector(".greenInfo, .searchErrors, table", timeout=5000)
            except PlaywrightTimeoutError:
                logger.warning("Network non è andato idle, procedo comunque con l'estrazione.")
            
            self._random_delay()
            
            # 10. Estrai risultati
            return self._extract_results(page)
            
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout durante la ricerca NRE: {e}")
            self._take_error_screenshot(page, "timeout_nre_search")
            return []
        except Exception as e:
            logger.error(f"Errore generico durante la ricerca NRE: {e}")
            self._take_error_screenshot(page, "error_nre_search")
            raise

    def _extract_results(self, page: Page) -> list[dict]:
        """
        Estrae le disponibilità dal DOM della pagina corrente.
        Usa strategie flessibili poiché il DOM post-login non è noto a priori.
        """
        # NOTA: Questi selettori sono approssimativi e andranno calibrati sul DOM reale post-login
        
        # Verifica se è presente un messaggio di nessuna disponibilità
        no_results_texts = ["nessuna disponibilità", "nessun risultato", "non ci sono appuntamenti"]
        page_text = page.locator("body").inner_text().lower()
        
        for text in no_results_texts:
            if text in page_text:
                logger.info("Nessuna disponibilità trovata (rilevato testo specifico).")
                return []

        results = []
        
        # Tentativi su possibili contenitori di risultati
        container_selectors = [
            "table tbody tr", 
            ".card-result", 
            ".availability-card", 
            ".list-group-item"
        ]
        
        found_containers = None
        for sel in container_selectors:
            elements = page.locator(sel)
            if elements.count() > 0:
                found_containers = elements
                break
                
        if found_containers:
            count = found_containers.count()
            logger.info(f"Trovati {count} elementi raw usando container.")
            for i in range(count):
                row = found_containers.nth(i)
                text = row.inner_text()
                
                results.append({
                    "struttura": "Da calibrare",
                    "indirizzo": "Da calibrare",
                    "data": "Da calibrare",
                    "ora": "Da calibrare",
                    "prestazione": "Da calibrare",
                    "raw_text": text.strip()
                })
        else:
            logger.warning("Nessun contenitore standard trovato per i risultati, restituisco dizionario vuoto.")
            
        logger.info(f"Estrazione completata: {len(results)} risultati trovati.")
        return results
