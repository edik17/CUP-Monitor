"""Modulo per la configurazione del logging per il bot CUP Marche.

Configura un logger con output simultaneo su console (StreamHandler)
e su file con rotazione automatica (RotatingFileHandler).
"""

import logging
import io
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from typing import Union


import re

class SensitiveDataFilter(logging.Filter):
    """Filtro di sicurezza e privacy per oscurare Codici Fiscali, Token e numeri di telefono dai log."""

    CF_REGEX = re.compile(r'\b[A-Z]{6}[0-9LMNPQRSTUV]{2}[A-EHLMPR-T][0-9LMNPQRSTUV]{2}[A-Z][0-9LMNPQRSTUV]{3}[A-Z]\b', re.IGNORECASE)
    BOT_TOKEN_REGEX = re.compile(r'\b[0-9]{8,10}:[a-zA-Z0-9_-]{35}\b')
    PHONE_REGEX = re.compile(r'\b(?:\+39|0039)?3[0-9]{8,9}\b')

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.CF_REGEX.sub(lambda m: f"{m.group(0)[:6]}******{m.group(0)[-3:]}", record.msg)
            record.msg = self.BOT_TOKEN_REGEX.sub("[REDACTED_BOT_TOKEN]", record.msg)
            record.msg = self.PHONE_REGEX.sub(lambda m: f"{m.group(0)[:4]}****{m.group(0)[-2:]}", record.msg)
        return True


def setup_logger(
    log_file: str = "./logs/cup_monitor.log",
    level: Union[str, int] = "INFO",
    max_size_mb: int = 5,
    backup_count: int = 3,
) -> logging.Logger:
    """Configura e restituisce il logger principale dell'applicazione 'cup_monitor'.

    Args:
        log_file: Percorso del file di log (stringa o compatibile con Path).
            Default: './logs/cup_monitor.log'.
        level: Livello di logging come stringa (es. 'DEBUG', 'INFO', 'WARNING', 'ERROR')
            o costante numerica (es. logging.INFO). Default 'INFO'.
        max_size_mb: Dimensione massima del file di log in Megabyte prima della rotazione. Default 5.
        backup_count: Numero di file storici di backup da mantenere. Default 3.

    Returns:
        Istanza configurata di logging.Logger con nome 'cup_monitor'.
    """
    logger = logging.getLogger("cup_monitor")

    # Determina il livello numerico di logging in modo sicuro (stringa o intero)
    if isinstance(level, int):
        numeric_level = level
    elif isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), logging.INFO)
    else:
        numeric_level = logging.INFO

    logger.setLevel(numeric_level)

    # Rimuove eventuali handler preesistenti per evitare messaggi duplicati
    if logger.hasHandlers():
        logger.handlers.clear()

    # Evita la propagazione al root logger per evitare log duplicati su console
    logger.propagate = False

    # Formattazione uniforme per file e console
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
    privacy_filter = SensitiveDataFilter()

    # Risoluzione del percorso e creazione automatica della cartella logs se non esiste
    log_path = Path(log_file)
    if log_path.parent:
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Handler per file con rotazione automatica
    max_bytes = max_size_mb * 1024 * 1024
    file_handler = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(privacy_filter)
    logger.addHandler(file_handler)

    # Handler per console standard output (con gestione encoding Windows)
    console_handler = logging.StreamHandler(
        stream=io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    )
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(privacy_filter)
    logger.addHandler(console_handler)

    return logger
