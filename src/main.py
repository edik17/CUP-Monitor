"""Entry point e orchestratore principale del bot di monitoraggio CUP Marche.

Uso:
    python src/main.py              # Esecuzione normale (scraping + notifica)
    python src/main.py --login      # Login manuale per generare/rinnovare sessione
    python src/main.py --dry-run    # Esecuzione senza invio notifiche Telegram
    python src/main.py --debug      # Abilita logging DEBUG
    python src/main.py --test-telegram  # Testa la connessione Telegram
"""

import argparse
import sys
import logging
import traceback
import yaml
from pathlib import Path

# Assicura che la directory src/ sia nel sys.path per gli import locali
sys.path.insert(0, str(Path(__file__).parent))

from logger_setup import setup_logger
from notifier import NotificationDispatcher, TelegramNotifier
from auth import SessionManager
from scraper import NREScraper
from filter import filter_by_provincia, format_results_summary, get_keywords_for_selection


def load_config(config_path: str = None) -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Optional path to the configuration file.

    Returns:
        Dictionary containing configuration parameters.

    Raises:
        FileNotFoundError: If the configuration file is not found.
    """
    if config_path:
        path = Path(config_path)
    else:
        project_root = Path(__file__).parent.parent
        path = project_root / 'config.yaml'

    if not path.is_file():
        raise FileNotFoundError(
            f"Errore: File di configurazione non trovato in '{path}'.\n"
            f"Copia config.yaml nella root del progetto e configura i parametri."
        )

    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main() -> int:
    """Main orchestration logic for the CUP monitor bot.

    Returns:
        Exit code:
          0 = success
          1 = generic error
          2 = session expired / missing
          3 = site unavailable
          4 = DOM structure changed
    """
    parser = argparse.ArgumentParser(
        description="Bot di Monitoraggio CUP Marche — Ricerca disponibilità NRE"
    )
    parser.add_argument(
        '--login', action='store_true',
        help="Forza il login manuale per generare/aggiornare la sessione"
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help="Esegui senza inviare notifiche Telegram"
    )
    parser.add_argument(
        '--debug', action='store_true',
        help="Abilita log a livello DEBUG"
    )
    parser.add_argument(
        '--test-telegram', action='store_true',
        help="Testa la connessione Telegram ed esci"
    )
    parser.add_argument(
        '--config', type=str, default=None,
        help="Percorso personalizzato per il file di configurazione"
    )

    args = parser.parse_args()
    notifier = None
    logger = None

    try:
        # ── 1. Carica configurazione ──
        config = load_config(args.config)

        cup_cfg = config.get('cup', {})
        filter_cfg = config.get('filter', {})
        telegram_cfg = config.get('telegram', {})
        session_cfg = config.get('session', {})
        logging_cfg = config.get('logging', {})
        timing_cfg = config.get('timing', {})

        # ── 2. Setup logging ──
        log_level = 'DEBUG' if args.debug else logging_cfg.get('level', 'INFO')
        logger = setup_logger(
            log_file=logging_cfg.get('file', './logs/cup_monitor.log'),
            level=log_level,
            max_size_mb=logging_cfg.get('max_size_mb', 5),
            backup_count=logging_cfg.get('backup_count', 3),
        )
        logger.info("=" * 60)
        logger.info("Avvio Bot di Monitoraggio CUP Marche")
        logger.info("=" * 60)

        # ── 3. Inizializza notifiche (Telegram / WhatsApp / SMS) ──
        notifier = NotificationDispatcher(config)

        # Modalità test notifiche
        if args.test_telegram:
            logger.info("Avvio test canali di notifica...")
            success = notifier.test_connection()
            if success:
                logger.info("✅ Test notifica completato con successo.")
            else:
                logger.error("❌ Test notifica fallito. Verifica i parametri in config.yaml.")
            return 0 if success else 1

        # ── 4. Inizializza Session Manager ──
        session_manager = SessionManager(
            storage_path=session_cfg.get('storage_path', './session/state.json'),
            base_url=cup_cfg.get('base_url', ''),
            page_timeout_ms=timing_cfg.get('page_timeout_ms', 30000),
        )

        # Modalità login interattivo
        if args.login:
            logger.info("Avvio procedura di login interattivo...")
            success = session_manager.interactive_login()
            if success:
                logger.info("✅ Login completato con successo. Sessione salvata.")
                if notifier and not args.dry_run:
                    notifier.notify_login_success()
                return 0
            else:
                logger.error("❌ Errore durante il login interattivo.")
                return 1

        # ── 5. Verifica sessione ──
        if not session_manager.session_exists():
            logger.error(
                "Nessuna sessione trovata. Esegui: python src/main.py --login"
            )
            if not args.dry_run:
                notifier.notify_session_expired()
            return 2

        if not session_manager.is_session_valid():
            logger.warning(
                "La sessione potrebbe essere scaduta (file troppo vecchio). "
                "Si tenta comunque l'accesso..."
            )

        # ── 6. Parametri di scraping ──
        base_url = cup_cfg.get('base_url', '')
        nre = cup_cfg.get('nre', '')
        codice_fiscale = cup_cfg.get('codice_fiscale', '')
        regione = filter_cfg.get('regione', 'Marche')
        province = filter_cfg.get('province') or filter_cfg.get('provincia', ['Ancona'])
        raw_keywords = filter_cfg.get('keywords', [])
        keywords = get_keywords_for_selection(regione, province, raw_keywords)
        send_no_match = config.get('notifications', {}).get('send_no_match', telegram_cfg.get('send_no_match', True))

        if not nre or nre == 'INSERIRE_NRE':
            logger.error("NRE non configurato in config.yaml. Inserire il numero di ricetta.")
            return 1

        if not codice_fiscale or codice_fiscale == 'INSERIRE_CF':
            logger.error("Codice Fiscale non configurato in config.yaml.")
            return 1

        logger.info(f"Ricerca per NRE: {nre[:4]}{'*' * (len(nre) - 4)}")  # Maschera parziale

        # ── 7. Avvia Playwright e procedi con lo scraping ──
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            try:
                context = session_manager.create_context(browser)
                page = context.new_page()
                page.set_default_timeout(timing_cfg.get('page_timeout_ms', 30000))

                logger.info(f"Navigazione verso: {base_url}")
                page.goto(base_url, wait_until='domcontentloaded')

                # Verifica redirect al login
                if session_manager.check_login_redirect(page):
                    logger.error(
                        "Sessione scaduta (redirect al login rilevato). "
                        "Esegui: python src/main.py --login"
                    )
                    if not args.dry_run:
                        notifier.notify_session_expired()
                    return 2

                logger.info("✅ Sessione valida. Procedo con la ricerca...")

                # Scraping
                scraper = NREScraper(
                    page_timeout_ms=timing_cfg.get('page_timeout_ms', 30000),
                    action_delay_ms=timing_cfg.get('action_delay_ms', 2000),
                )
                results = scraper.search_nre(page, nre, codice_fiscale)

                # Filtraggio per provincia di Ancona
                filtered = filter_by_provincia(results, keywords)

                # Log riepilogo
                summary = format_results_summary(filtered)
                logger.info(f"Riepilogo risultati filtrati:\n{summary}")

                # Notifiche
                if filtered:
                    logger.info(f"🎯 Trovate {len(filtered)} disponibilità in provincia di Ancona!")
                    if not args.dry_run:
                        notifier.notify_match(filtered)
                    else:
                        logger.info("[Dry Run] Saltato invio notifica Telegram.")
                else:
                    logger.info("Nessuna disponibilità in provincia di Ancona.")
                    if send_no_match and not args.dry_run:
                        notifier.notify_no_match()

                # Aggiorna sessione (refresh timestamp)
                session_manager.save_session(context)

            finally:
                browser.close()

        logger.info("Esecuzione completata con successo.")
        return 0

    except KeyboardInterrupt:
        print("\nEsecuzione interrotta dall'utente.")
        return 0

    except FileNotFoundError as e:
        # Logger potrebbe non essere inizializzato
        print(str(e))
        return 1

    except Exception as e:
        # Errore imprevisto
        error_msg = f"{type(e).__name__}: {e}"
        tb = traceback.format_exc()

        if logger:
            logger.exception("Si è verificato un errore imprevisto.")
        else:
            print(f"ERRORE: {error_msg}\n{tb}")

        if notifier and not args.dry_run:
            try:
                notifier.notify_error(error_msg, tb[-500:] if len(tb) > 500 else tb)
            except Exception:
                pass  # Non propagare errori dalla notifica

        return 1


if __name__ == '__main__':
    sys.exit(main())
