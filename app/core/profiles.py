# core/profiles.py — Caricamento profili e costruzione delle istruzioni di adattamento.
#
# Supporta DUE schemi di profilo:
#   1. Schema "leggero" (Streamlit / PROFILI_DEFAULT):
#      chiavi: note, max_parole_frase, punti_per_blocco
#   2. Schema "completo" (YAML CLI/GUI):
#      chiavi: presentazione, profilo_cognitivo.aree_difficolta, note_osservazioni
#
# Modulo foglia: importa solo da `core.config`.

from __future__ import annotations

from pathlib import Path

import yaml

from .config import MAX_PAROLE_FRASE_DEFAULT


# ─── PROFILI DEFAULT (migrati da streamlit_demo.py righe 12-54) ────────────────

PROFILI_DEFAULT: dict = {
    "Mario — DSA (dislessia + disgrafia)": {
        "max_parole_frase": 20,
        "punti_per_blocco": 3,
        "note": (
            "Frasi brevi (max 20 parole). Un concetto per paragrafo. "
            "Parole chiave in grassetto (max 3 per paragrafo). "
            "Glossario finale con 5 termini difficili."
        ),
    },
    "Sofia — BES (attenzione + italiano L2)": {
        "max_parole_frase": 18,
        "punti_per_blocco": 3,
        "note": (
            "Usa analogie concrete della vita quotidiana per ogni concetto astratto. "
            "Evita metafore. Usa elenchi puntati invece di paragrafi. "
            "Glossario sempre presente. Frasi max 18 parole."
        ),
    },
    "Lorenzo — ASD Level 2 + CAA": {
        "max_parole_frase": 12,
        "punti_per_blocco": 2,
        "note": (
            "Una sola informazione per frase. Frasi max 12 parole. "
            "Struttura rigida e prevedibile. "
            "Per ogni concetto chiave suggerisci un simbolo visivo descrittivo tra parentesi quadre: [SIMBOLO: descrizione]. "
            "Niente metafore, niente ironia."
        ),
    },
    "Profilo base (generico)": {
        "max_parole_frase": 20,
        "punti_per_blocco": 3,
        "note": (
            "Adattamento standard per difficoltà di apprendimento generiche. "
            "Frasi brevi, struttura chiara, glossario finale."
        ),
    },
    "Profilo personalizzato...": {
        "max_parole_frase": 20,
        "punti_per_blocco": 3,
        "note": "",
    },
}


# ─── CARICAMENTO ───────────────────────────────────────────────────────────────

def carica_profilo(nome_studente: str) -> dict:
    """Carica un profilo YAML da ``profili/profilo_<nome>.yaml``.

    A differenza della vecchia versione CLI (che faceva ``sys.exit``), qui viene
    sollevata ``FileNotFoundError`` per essere riusabile come libreria e nei test.
    Il chiamante (CLI) gestisce l'errore come preferisce.

    Args:
        nome_studente: nome dello studente (case-insensitive, spazi -> underscore).

    Returns:
        Il profilo come dizionario.

    Raises:
        FileNotFoundError: se il file profilo non esiste.
    """
    chiave = nome_studente.lower().replace(" ", "_")
    percorso = Path(f"profili/profilo_{chiave}.yaml")
    with open(percorso, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def carica_profilo_da_bytes(yaml_bytes: bytes) -> dict:
    """Carica un profilo da contenuto YAML in bytes (upload Streamlit).

    Args:
        yaml_bytes: contenuto YAML grezzo.

    Returns:
        Il profilo come dizionario; ``{}`` se il contenuto è vuoto.

    Raises:
        yaml.YAMLError: se il contenuto YAML è malformato.
    """
    dati = yaml.safe_load(yaml_bytes)
    if dati is None:
        return {}
    if not isinstance(dati, dict):
        raise yaml.YAMLError("Il profilo YAML deve essere una mappa chiave: valore.")
    return dati


# ─── COSTRUZIONE ISTRUZIONI ──────────────────────────────────────────────────

def costruisci_istruzioni(profilo: dict) -> str:
    """Costruisce il blocco di istruzioni testuali per i prompt.

    Gestisce sia lo schema leggero (``note``/``max_parole_frase``/``punti_per_blocco``)
    sia lo schema completo YAML (``presentazione``/``profilo_cognitivo``/``note_osservazioni``).

    Args:
        profilo: profilo studente (uno dei due schemi supportati).

    Returns:
        Stringa di bullet point, una istruzione per riga (prefisso ``- ``).
    """
    profilo = profilo or {}
    istruzioni: list[str] = []

    # ── Schema completo YAML ──
    presentazione = profilo.get("presentazione", {}) or {}
    difficolta = (
        profilo.get("profilo_cognitivo", {}).get("aree_difficolta", {}) or {}
    )
    note_oss = profilo.get("note_osservazioni", []) or []

    max_parole = profilo.get("max_parole_frase", MAX_PAROLE_FRASE_DEFAULT)

    if difficolta.get("lettura"):
        istruzioni.append(
            f"Usa frasi brevi (max {max_parole} parole). Evita subordinate complesse."
        )
    if difficolta.get("memoria_di_lavoro"):
        istruzioni.append(
            "Un concetto per paragrafo. Non unire più idee nello stesso blocco."
        )
    if difficolta.get("scrittura"):
        istruzioni.append(
            "Usa elenchi puntati invece di paragrafi continui dove possibile."
        )

    if presentazione or difficolta or note_oss:
        istruzioni.append(
            f"Ogni blocco: massimo {presentazione.get('max_punti_per_slide', 3)} punti elenco."
        )
        istruzioni.append(
            f"Ogni paragrafo: massimo {presentazione.get('max_righe_paragrafo', 4)} righe."
        )
        istruzioni.append(
            "Evidenzia in grassetto le parole chiave (max 3 per paragrafo)."
        )
        istruzioni.append("Usa corsivo per i termini tecnici alla prima occorrenza.")

    for nota in note_oss:
        if nota:
            istruzioni.append(str(nota))

    # ── Schema leggero (Streamlit): la chiave `note` è già un testo di istruzioni ──
    note_leggere = profilo.get("note")
    if note_leggere:
        istruzioni.append(str(note_leggere))

    # Fallback: nessuna informazione utile nel profilo.
    if not istruzioni:
        istruzioni.append(
            f"Adattamento standard. Frasi brevi (max {max_parole} parole), "
            "struttura chiara, glossario finale."
        )

    return "\n".join(f"- {i}" for i in istruzioni)
