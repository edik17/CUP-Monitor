"""Modulo per la catalogazione territoriale e il filtraggio geografico dei risultati CUP.

Supporta la selezione di una o più province/regioni, espandendo automaticamente
le parole chiave comunali e dei presidi ospedalieri.
"""

import logging

logger = logging.getLogger("cup_monitor")

# Catalogo territoriale delle province e dei principali comuni/presidi per regione
TERRITORIAL_CATALOG: dict[str, dict[str, list[str]]] = {
    "Marche": {
        "Ancona": [
            "Ancona", "Torrette", "INRCA", "Jesi", "Fabriano", "Senigallia", "Osimo",
            "Chiaravalle", "Loreto", "Castelfidardo", "Falconara", "Camerano",
            "Agugliano", "Montemarciano", "Filottrano", "Cupramontana", "Arcevia",
            "Sassoferrato", "Serra San Quirico", "Genga", "Staffolo", "Mergo",
            "Cerreto d'Esi", "Polverigi", "Offagna", "Numana", "Sirolo", "Monte San Vito",
            "Belvedere Ostrense", "Barbara", "Ostra", "Ostra Vetere", "Trecastelli",
            "Corinaldo", "Castelleone di Suasa", "Serra de' Conti", "Monsano",
            "San Marcello", "Maiolati Spontini", "Castelplanio", "Poggio San Marcello",
            "Rosora", "Angeli di Rosora"
        ],
        "Pesaro e Urbino": [
            "Pesaro", "Fano", "Urbino", "Fossombrone", "Cagli", "Pergola", "Mondolfo",
            "Colli al Metauro", "Gabicce Mare", "Gradara", "Tavullia", "Vallefoglia",
            "Cartoceto", "Urbania", "Sant'Angelo in Vado", "Piobbico", "Acqualagna"
        ],
        "Macerata": [
            "Macerata", "Civitanova Marche", "Recanati", "Tolentino", "San Severino Marche",
            "Potenza Picena", "Porto Recanati", "Corridonia", "Morrovalle", "Matelica",
            "Camerino", "Treia", "Montecassiano", "Monte San Giusto", "Pollenza", "Cingoli"
        ],
        "Fermo": [
            "Fermo", "Porto San Giorgio", "Sant'Elpidio a Mare", "Porto Sant'Elpidio",
            "Montegranaro", "Amandola", "Monte Urano", "Grottazzolina", "Petritoli"
        ],
        "Ascoli Piceno": [
            "Ascoli Piceno", "San Benedetto del Tronto", "Grottammare", "Monteprandone",
            "Folignano", "Castel di Lama", "Spinetoli", "Offida", "Acquaviva Picena",
            "Comunanza", "Ripatransone"
        ]
    }
}


def get_keywords_for_selection(regione: str, province: list[str] | str, extra_keywords: list[str] | None = None) -> list[str]:
    """Genera l'elenco completo delle parole chiave in base alle province selezionate."""
    keywords: set[str] = set()
    
    if isinstance(province, str):
        province = [province]

    reg_data = TERRITORIAL_CATALOG.get(regione, {})
    all_selected = "Tutte" in province or "Tutta la Regione" in province or not province

    for prov_name, prov_kw in reg_data.items():
        if all_selected or prov_name in province:
            keywords.add(prov_name)
            keywords.update(prov_kw)

    if extra_keywords:
        keywords.update(extra_keywords)

    return sorted(list(keywords))


def filter_by_provincia(results: list[dict], keywords: list[str]) -> list[dict]:
    """Filtra i risultati verificando la corrispondenza con le parole chiave territoriali."""
    logger.debug("Risultati prima del filtraggio: %d", len(results))

    if not keywords:
        logger.info("Nessun filtro geografico impostato: restituisco tutte le %d disponibilità.", len(results))
        return results

    lower_keywords = [kw.lower() for kw in keywords if kw]
    filtered_results = []

    for result in results:
        struttura = result.get("struttura", "").lower()
        indirizzo = result.get("indirizzo", "").lower()
        combined_text = f"{struttura} {indirizzo}"

        if any(kw in combined_text for kw in lower_keywords):
            filtered_results.append(result)

    logger.info("Risultati dopo il filtraggio geografico: %d", len(filtered_results))
    return filtered_results


def format_results_summary(results: list[dict]) -> str:
    """Crea un riepilogo testuale formattato delle disponibilità trovate."""
    if not results:
        return "Nessun risultato trovato."

    summary_lines = []
    for res in results:
        struttura = res.get("struttura", "Sconosciuta")
        data = res.get("data", "Data non disponibile")
        ora = res.get("ora", "")
        ora_str = f" {ora}" if ora else ""
        summary_lines.append(f"- {struttura} | {data}{ora_str}")

    return "\n".join(summary_lines)
