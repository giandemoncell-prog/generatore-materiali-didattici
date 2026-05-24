"""Test per core.profiles (caricamento profili e costruzione istruzioni)."""

from __future__ import annotations

import pytest
import yaml

from core.profiles import (
    PROFILI_DEFAULT,
    carica_profilo_da_bytes,
    costruisci_istruzioni,
)


# ── carica_profilo_da_bytes ───────────────────────────────────────────────────

def test_carica_profilo_da_bytes_valido():
    yaml_bytes = b"presentazione:\n  font: Arial\n  max_punti_per_slide: 3\n"
    profilo = carica_profilo_da_bytes(yaml_bytes)
    assert isinstance(profilo, dict)
    assert profilo["presentazione"]["font"] == "Arial"


def test_carica_profilo_da_bytes_vuoto_ritorna_dict_vuoto():
    assert carica_profilo_da_bytes(b"") == {}


def test_carica_profilo_da_bytes_solo_commenti_ritorna_dict_vuoto():
    assert carica_profilo_da_bytes(b"# solo un commento\n") == {}


def test_carica_profilo_da_bytes_malformato_solleva():
    # Indentazione/struttura non valida -> errore YAML.
    yaml_bytes = b"presentazione:\n  font: Arial\n - elemento fuori posto\n"
    with pytest.raises(yaml.YAMLError):
        carica_profilo_da_bytes(yaml_bytes)


def test_carica_profilo_da_bytes_scalare_non_mappa_solleva():
    # Un documento YAML che non è una mappa non è un profilo valido.
    with pytest.raises(yaml.YAMLError):
        carica_profilo_da_bytes(b"solo una stringa")


def test_carica_profilo_da_bytes_completo():
    yaml_bytes = (
        b"profilo_cognitivo:\n"
        b"  aree_difficolta:\n"
        b"    lettura: alta\n"
        b"note_osservazioni:\n"
        b"  - Usa elenchi puntati\n"
    )
    profilo = carica_profilo_da_bytes(yaml_bytes)
    assert profilo["profilo_cognitivo"]["aree_difficolta"]["lettura"] == "alta"
    assert profilo["note_osservazioni"] == ["Usa elenchi puntati"]


# ── costruisci_istruzioni ─────────────────────────────────────────────────────

def test_costruisci_istruzioni_schema_leggero(profilo_mario):
    istr = costruisci_istruzioni(profilo_mario)
    assert istr.strip().startswith("-")
    assert "Un concetto per paragrafo" in istr  # dalle note di Mario


def test_costruisci_istruzioni_schema_completo(profilo_yaml_completo):
    istr = costruisci_istruzioni(profilo_yaml_completo)
    # Difficoltà di lettura -> frasi brevi.
    assert "frasi brevi" in istr.lower()
    # Difficoltà di memoria di lavoro -> un concetto per paragrafo.
    assert "Un concetto per paragrafo" in istr
    # Le note_osservazioni finiscono nelle istruzioni.
    assert "Esempi concreti." in istr


def test_costruisci_istruzioni_profilo_vuoto_ha_fallback():
    istr = costruisci_istruzioni({})
    assert istr.strip().startswith("-")
    assert "standard" in istr.lower()


def test_costruisci_istruzioni_none_non_crasha():
    istr = costruisci_istruzioni(None)
    assert isinstance(istr, str) and istr


def test_costruisci_istruzioni_rispetta_max_parole():
    profilo = {
        "max_parole_frase": 12,
        "profilo_cognitivo": {"aree_difficolta": {"lettura": "alta"}},
    }
    istr = costruisci_istruzioni(profilo)
    assert "max 12 parole" in istr


# ── PROFILI_DEFAULT ───────────────────────────────────────────────────────────

def test_profili_default_chiavi_attese():
    attese = {
        "Mario — DSA (dislessia + disgrafia)",
        "Sofia — BES (attenzione + italiano L2)",
        "Lorenzo — ASD Level 2 + CAA",
        "Profilo base (generico)",
        "Profilo personalizzato...",
    }
    assert attese.issubset(set(PROFILI_DEFAULT.keys()))


def test_profili_default_struttura_valori():
    for nome, profilo in PROFILI_DEFAULT.items():
        assert "max_parole_frase" in profilo, nome
        assert "punti_per_blocco" in profilo, nome
        assert "note" in profilo, nome


def test_profili_default_valori_numerici():
    p = PROFILI_DEFAULT["Lorenzo — ASD Level 2 + CAA"]
    assert isinstance(p["max_parole_frase"], int)
    assert p["max_parole_frase"] == 12
