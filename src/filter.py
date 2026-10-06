"""Modulo per la catalogazione territoriale e il filtraggio geografico dei risultati CUP.

Supporta la selezione di tutte le 20 Regioni Italiane e delle relative province,
espandendo automaticamente le parole chiave territoriali dei presidi ospedalieri e ASL.
"""

import logging

logger = logging.getLogger("cup_monitor")

# Portali CUP regionali ufficiali
REGIONAL_CUP_PORTALS: dict[str, dict[str, str]] = {
    "Abruzzo": {"name": "Sanità Regione Abruzzo", "url": "https://sanita.regione.abruzzo.it"},
    "Basilicata": {"name": "CUP Basilicata", "url": "https://portale.aslbasilicata.it"},
    "Calabria": {"name": "RCUP Calabria", "url": "https://rcup.regione.calabria.it"},
    "Campania": {"name": "Sinfonia Campania", "url": "https://sinfonia.regione.campania.it"},
    "Emilia-Romagna": {"name": "CUPWeb Emilia-Romagna", "url": "https://www.cupweb.it"},
    "Friuli-Venezia Giulia": {"name": "Sesamo FVG", "url": "https://sesamo.sanita.fvg.it"},
    "Lazio": {"name": "ReCUP Lazio", "url": "https://prenotasanita.regione.lazio.it"},
    "Liguria": {"name": "Prenoto Sanità Liguria", "url": "https://prenotosanita.regione.liguria.it"},
    "Lombardia": {"name": "Prenota Salute Lombardia", "url": "https://prenotasalute.regione.lombardia.it"},
    "Marche": {"name": "MyCup Marche", "url": "https://mycupmarche.it/prenotazionecittadino/web/search/nre"},
    "Molise": {"name": "CUP Molise ASReM", "url": "https://www.asrem.gov.it"},
    "Piemonte": {"name": "Salute Piemonte CUP", "url": "https://www.salutepiemonte.it"},
    "Puglia": {"name": "Puglia Salute", "url": "https://www.sanita.puglia.it"},
    "Sardegna": {"name": "CUPWeb Sardegna", "url": "https://cupweb.sardegnasalute.it"},
    "Sicilia": {"name": "Sicilia in Salute SovraCUP", "url": "https://siciliainsalute.it"},
    "Toscana": {"name": "Prenota Sanità Toscana", "url": "https://prenota.sanita.toscana.it"},
    "Trentino-Alto Adige": {"name": "CUP Trentino / Alto Adige", "url": "https://www.apss.tn.it"},
    "Umbria": {"name": "CUP Umbria", "url": "https://cupumbria.it"},
    "Valle d'Aosta": {"name": "CUP Valle d'Aosta", "url": "https://www.ausl.vda.it"},
    "Veneto": {"name": "Sanità Regione Veneto", "url": "https://www.azero.veneto.it"}
}

# Catalogo territoriale delle province per tutte le 20 regioni italiane
TERRITORIAL_CATALOG: dict[str, dict[str, list[str]]] = {
    "Abruzzo": {
        "L'Aquila": ["L'Aquila", "Avezzano", "Sulmona", "Castel di Sangro"],
        "Chieti": ["Chieti", "Vasto", "Lanciano", "Ortona", "Atessa"],
        "Pescara": ["Pescara", "Penne", "Popoli", "Montesilvano"],
        "Teramo": ["Teramo", "Giulianova", "Atri", "Sant'Omero"]
    },
    "Basilicata": {
        "Potenza": ["Potenza", "Melfi", "Venosa", "Villa d'Agri", "Lagonegro"],
        "Matera": ["Matera", "Policoro", "Tinchi", "Stigliano", "Pisticci"]
    },
    "Calabria": {
        "Catanzaro": ["Catanzaro", "Lamezia Terme", "Soverato", "Chiaravalle Centrale"],
        "Cosenza": ["Cosenza", "Rende", "Rossano", "Corigliano", "Castrovillari", "Paola", "Acri"],
        "Crotone": ["Crotone", "Cirò Marina", "Mesoraca"],
        "Reggio Calabria": ["Reggio Calabria", "Gioia Tauro", "Locri", "Polistena", "Melito Porto Salvo"],
        "Vibo Valentia": ["Vibo Valentia", "Tropea", "Serra San Bruno", "Soriano Calabro"]
    },
    "Campania": {
        "Napoli": ["Napoli", "Cardarelli", "Policlinico", "Pozzuoli", "Giugliano", "Castellammare di Stabia", "Nola", "Torre del Greco"],
        "Salerno": ["Salerno", "Ruggi d'Aragona", "Battipaglia", "Nocera Inferiore", "Cava de' Tirreni", "Vallo della Lucania", "Eboli"],
        "Caserta": ["Caserta", "Aversa", "Marcianise", "Santa Maria Capua Vetere", "Sessa Aurunca", "Maddaloni"],
        "Avellino": ["Avellino", "Moscati", "Ariano Irpino", "Solofra", "Sant'Angelo dei Lombardi"],
        "Benevento": ["Benevento", "San Pio", "Rummo", "Sant'Agata de' Goti"]
    },
    "Emilia-Romagna": {
        "Bologna": ["Bologna", "Sant'Orsola", "Maggiore", "Rizzoli", "Bellaria", "Imola", "San Giovanni in Persiceto"],
        "Modena": ["Modena", "Policlinico", "Baggiovara", "Carpi", "Sassuolo", "Mirandola", "Vignola"],
        "Reggio Emilia": ["Reggio Emilia", "Santa Maria Nuova", "Guastalla", "Montecchio", "Castelnovo ne' Monti", "Scandiano"],
        "Parma": ["Parma", "Maggiore", "Fidenza", "Vaio", "Borgotaro"],
        "Ferrara": ["Ferrara", "Cona", "Cento", "Lagosanto", "Comacchio"],
        "Forlì-Cesena": ["Forlì", "Cesena", "Bufalini", "Morgagni-Pierantoni"],
        "Ravenna": ["Ravenna", "Faenza", "Lugo"],
        "Rimini": ["Rimini", "Riccione", "Santarcangelo di Romagna", "Novafeltria"],
        "Piacenza": ["Piacenza", "Castel San Giovanni", "Fiorenzuola d'Arda"]
    },
    "Friuli-Venezia Giulia": {
        "Trieste": ["Trieste", "Cattinara", "Maggiore", "Burlo Garofolo"],
        "Udine": ["Udine", "Santa Maria della Misericordia", "Tolmezzo", "San Daniele del Friuli", "Palmanova", "Latisana"],
        "Pordenone": ["Pordenone", "Santa Maria degli Angeli", "San Vito al Tagliamento", "Spilimbergo", "Maniago"],
        "Gorizia": ["Gorizia", "Monfalcone"]
    },
    "Lazio": {
        "Roma": ["Roma", "Umberto I", "Gemelli", "Sant'Andrea", "San Camillo", "Tor Vergata", "San Giovanni", "Tivoli", "Civitavecchia", "Frascati", "Anzio"],
        "Latina": ["Latina", "Santa Maria Goretti", "Aprilia", "Terracina", "Formia", "Fondi"],
        "Frosinone": ["Frosinone", "Spaziani", "Cassino", "Sora", "Alatri"],
        "Viterbo": ["Viterbo", "Belcolle", "Tarquinia", "Civita Castellana"],
        "Rieti": ["Rieti", "San Camillo de Lellis"]
    },
    "Liguria": {
        "Genova": ["Genova", "San Martino", "Galliera", "Gaslini", "Villa Scassi", "Lavagna", "Rapallo", "Sestri Levante"],
        "La Spezia": ["La Spezia", "Sant'Andrea", "Sarzana"],
        "Savona": ["Savona", "San Paolo", "Pietra Ligure", "Santa Corona", "Cairo Montenotte", "Albenga"],
        "Imperia": ["Imperia", "Sanremo", "Bordighera"]
    },
    "Lombardia": {
        "Milano": ["Milano", "Niguarda", "Policlinico", "San Raffaele", "Humanitas", "San Carlo", "San Paolo", "Fatebenefratelli", "Sesto San Giovanni", "Legnano", "Rho"],
        "Brescia": ["Brescia", "Spedali Civili", "Poliambulanza", "Desenzano del Garda", "Chiari", "Montichiari", "Gavardo", "Manerbio"],
        "Bergamo": ["Bergamo", "Papa Giovanni XXIII", "Treviglio", "Seriate", "Romano di Lombardia", "Piario"],
        "Monza e Brianza": ["Monza", "San Gerardo", "Desio", "Vimercate", "Carate Brianza"],
        "Como": ["Como", "Sant'Anna", "Cantù", "Menaggio", "Erba"],
        "Varese": ["Varese", "Circolo", "Busto Arsizio", "Gallarate", "Saronno", "Luino", "Tradate"],
        "Pavia": ["Pavia", "San Matteo", "Vigevano", "Voghera", "Stradella"],
        "Cremona": ["Cremona", "Crema", "Casalmaggiore", "Oglio Po"],
        "Mantova": ["Mantova", "Carlo Poma", "Castiglione delle Stiviere", "Pieve di Coriano", "Asola"],
        "Lecco": ["Lecco", "Manzoni", "Merate", "Bellano"],
        "Lodi": ["Lodi", "Maggiore", "Codogno", "Sant'Angelo Lodigiano"],
        "Sondrio": ["Sondrio", "Morbegno", "Chiavenna", "Tirano", "Sondalo"]
    },
    "Marche": {
        "Ancona": [
            "Ancona", "Torrette", "INRCA", "Jesi", "Fabriano", "Senigallia", "Osimo",
            "Chiaravalle", "Loreto", "Castelfidardo", "Falconara", "Camerano",
            "Agugliano", "Montemarciano", "Filottrano", "Cupramontana", "Arcevia",
            "Sassoferrato", "Serra San Quirico", "Genga", "Staffolo", "Mergo",
            "Cerreto d'Esi", "Polverigi", "Offagna", "Numana", "Sirolo", "Monte San Vito"
        ],
        "Pesaro e Urbino": [
            "Pesaro", "Fano", "Urbino", "Fossombrone", "Cagli", "Pergola", "Mondolfo",
            "Colli al Metauro", "Gabicce Mare", "Gradara", "Tavullia", "Vallefoglia"
        ],
        "Macerata": [
            "Macerata", "Civitanova Marche", "Recanati", "Tolentino", "San Severino Marche",
            "Potenza Picena", "Porto Recanati", "Corridonia", "Morrovalle", "Matelica", "Camerino"
        ],
        "Fermo": [
            "Fermo", "Porto San Giorgio", "Sant'Elpidio a Mare", "Porto Sant'Elpidio",
            "Montegranaro", "Amandola", "Monte Urano"
        ],
        "Ascoli Piceno": [
            "Ascoli Piceno", "San Benedetto del Tronto", "Grottammare", "Monteprandone",
            "Folignano", "Castel di Lama", "Spinetoli", "Offida"
        ]
    },
    "Molise": {
        "Campobasso": ["Campobasso", "Cardarelli", "Termoli", "San Timoteo", "Larino"],
        "Isernia": ["Isernia", "Veneziale", "Venafro", "Agnone"]
    },
    "Piemonte": {
        "Torino": ["Torino", "Molinette", "Cto", "Mauriziano", "San Luigi", "Rivoli", "Moncalieri", "Chivasso", "Ivrea", "Pinerolo"],
        "Cuneo": ["Cuneo", "Santa Croce e Carle", "Alba", "Bra", "Mondovì", "Savigliano", "Saluzzo"],
        "Alessandria": ["Alessandria", "Santi Antonio e Biagio", "Casale Monferrato", "Novi Ligure", "Tortona", "Acqui Terme"],
        "Novara": ["Novara", "Maggiore della Carità", "Borgomanero", "Arona"],
        "Asti": ["Asti", "Cardinal Massaia", "Nizza Monferrato"],
        "Biella": ["Biella", "Degli Infermi"],
        "Vercelli": ["Vercelli", "Sant'Andrea", "Borgosesia"],
        "Verbano-Cusio-Ossola": ["Verbania", "Castelli", "Domodossola", "Omegna"]
    },
    "Puglia": {
        "Bari": ["Bari", "Policlinico", "Di Venere", "San Paolo", "Altamura", "Monopoli", "Molfetta", "Corato"],
        "Lecce": ["Lecce", "Vito Fazzi", "Gallipoli", "Casarano", "Copertino", "Scorrano", "Galatina"],
        "Taranto": ["Taranto", "Santissima Annunziata", "Castellaneta", "Manduria", "Martina Franca", "Grottaglie"],
        "Foggia": ["Foggia", "Policlinico Riuniti", "San Severo", "Cerignola", "Manfredonia", "Lucera"],
        "Brindisi": ["Brindisi", "Perrino", "Francavilla Fontana", "Ostuni", "Fasano"],
        "Barletta-Andria-Trani": ["Barletta", "Andria", "Trani", "Bisceglie", "Canosa di Puglia"]
    },
    "Sardegna": {
        "Cagliari": ["Cagliari", "Brotzu", "Policlinico Monserrato", "Santissima Trinità", "Quartu Sant'Elena"],
        "Sassari": ["Sassari", "Santissima Annunziata", "Alghero", "Ozieri"],
        "Nuoro": ["Nuoro", "San Francesco", "Sorgono"],
        "Oristano": ["Oristano", "San Martino", "Bosa", "Ghilarza"],
        "Sud Sardegna": ["Carbonia", "Sirai", "Iglesias", "San Gavino Monreale"]
    },
    "Sicilia": {
        "Palermo": ["Palermo", "Civico", "Policlinico", "Villa Sofia", "Cervello", "Termini Imerese", "Partinico", "Cefalù"],
        "Catania": ["Catania", "Garibaldi", "Cannizzaro", "Policlinico", "Acireale", "Giarre", "Caltagirone", "Paternò"],
        "Messina": ["Messina", "Policlinico", "Papardo", "Piemonte", "Taormina", "Milazzo", "Barcellona Pozzo di Gotto", "Patti"],
        "Agrigento": ["Agrigento", "San Giovanni di Dio", "Sciacca", "Canicattì", "Licata", "Ribera"],
        "Trapani": ["Trapani", "Sant'Antonio Abate", "Marsala", "Mazara del Vallo", "Castelvetrano", "Alcamo"],
        "Siracusa": ["Siracusa", "Umberto I", "Avola", "Noto", "Lentini", "Augusta"],
        "Ragusa": ["Ragusa", "Giovanni Paolo II", "Modica", "Vittoria", "Comiso"],
        "Caltanissetta": ["Caltanissetta", "Sant'Elia", "Gela", "Mazzarino"],
        "Enna": ["Enna", "Umberto I", "Piazza Armerina", "Nicosia", "Leonforte"]
    },
    "Toscana": {
        "Firenze": ["Firenze", "Careggi", "Meyer", "Santa Maria Nuova", "San Giovanni di Dio", "Torregalli", "Bagno a Ripoli", "Empoli"],
        "Pisa": ["Pisa", "Cisanello", "Santa Chiara", "Pontedera", "Volterra"],
        "Livorno": ["Livorno", "Spedali Riuniti", "Cecina", "Piombino", "Portoferraio"],
        "Arezzo": ["Arezzo", "San Donato", "Montevarchi", "Bibbiena", "Sansepolcro"],
        "Pistoia": ["Pistoia", "San Jacopo", "Pescia", "Montecatini Terme"],
        "Lucca": ["Lucca", "San Luca", "Viareggio", "Versilia", "Castelnuovo di Garfagnana"],
        "Prato": ["Prato", "Santo Stefano"],
        "Grosseto": ["Grosseto", "Misericordia", "Massa Marittima", "Orbetello"],
        "Siena": ["Siena", "Le Scotte", "Poggibonsi", "Campostaggia", "Nottola", "Montepulciano", "Abbadia San Salvatore"],
        "Massa-Carrara": ["Massa", "Carrara", "Pontremoli", "Fivizzano"]
    },
    "Trentino-Alto Adige": {
        "Trento": ["Trento", "Santa Chiara", "Rovereto", "Cles", "Borgo Valsugana", "Cavalese", "Arco", "Tione"],
        "Bolzano": ["Bolzano", "Merano", "Bressanone", "Brunico", "Vipiteno", "San Candido", "Silandro"]
    },
    "Umbria": {
        "Perugia": ["Perugia", "Santa Maria della Misericordia", "Foligno", "Città di Castello", "Gubbio", "Spoleto", "Assisi", "Castiglione del Lago"],
        "Terni": ["Terni", "Santa Maria", "Orvieto", "Narni", "Amelia"]
    },
    "Valle d'Aosta": {
        "Aosta": ["Aosta", "Parini", "Beauregard"]
    },
    "Veneto": {
        "Venezia": ["Venezia", "Dell'Angelo Mestre", "Dolo", "Mirano", "Chioggia", "San Donà di Piave", "Portogruaro", "Jesolo"],
        "Verona": ["Verona", "Borgo Trento", "Borgo Roma", "San Bonifacio", "Legnago", "Villafranca di Verona", "Bussolengo", "Negrar"],
        "Padova": ["Padova", "Azienda Ospedaliera", "Sant'Antonio", "Schiavonia", "Camposampiero", "Cittadella", "Piove di Sacco"],
        "Vicenza": ["Vicenza", "San Bortolo", "Bassano del Grappa", "Arzignano", "Valdagno", "Santorso", "Asiago"],
        "Treviso": ["Treviso", "Ca' Foncello", "Conegliano", "Montebelluna", "Castelfranco Veneto", "Oderzo", "Vittorio Veneto"],
        "Rovigo": ["Rovigo", "Santa Maria della Misericordia", "Adria", "Trecenta"],
        "Belluno": ["Belluno", "San Martino", "Feltre", "Pieve di Cadore", "Agordo"]
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
        raw_text = result.get("raw_text", "").lower()
        combined_text = f"{struttura} {indirizzo} {raw_text}"

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
