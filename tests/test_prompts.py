"""Test per core.prompts.

Verificano i marker di sezione attesi dai parser/exporter e il rispetto dei
vincoli di profilo. Dove pertinente si mocka google.genai.Client.
"""

from __future__ import annotations

import pytest

from core.prompts import (
    prompt_glossario_pro,
    prompt_infografica,
    prompt_quiz,
    prompt_slide,
    prompt_testo,
)


# ── prompt_testo ──────────────────────────────────────────────────────────────

def test_prompt_testo_contiene_marker_testo_adattato(profilo_mario, testo_storia):
    p = prompt_testo(testo_storia, profilo_mario)
    assert "---TESTO ADATTATO---" in p


def test_prompt_testo_contiene_marker_glossario(profilo_mario, testo_storia):
    p = prompt_testo(testo_storia, profilo_mario)
    assert "---GLOSSARIO---" in p


def test_prompt_testo_include_testo_originale(profilo_mario, testo_storia):
    p = prompt_testo(testo_storia, profilo_mario)
    assert "lotta per le investiture" in p
    assert "Concordato di Worms" in p


def test_prompt_testo_include_istruzioni_profilo(profilo_mario, testo_storia):
    p = prompt_testo(testo_storia, profilo_mario)
    # Le note del profilo Mario finiscono nelle istruzioni.
    assert "Un concetto per paragrafo" in p


def test_prompt_testo_note_extra_appese(profilo_mario, testo_storia):
    p = prompt_testo(testo_storia, profilo_mario, note_extra="Aggiungi esempi di matematica")
    assert "Aggiungi esempi di matematica" in p


def test_prompt_testo_intestazione_esperto(profilo_sofia, testo_storia):
    p = prompt_testo(testo_storia, profilo_sofia)
    assert p.startswith("Sei un esperto di didattica inclusiva")


def test_prompt_testo_profilo_sofia_specifico(profilo_sofia, testo_storia):
    p = prompt_testo(testo_storia, profilo_sofia)
    assert "analogie concrete" in p


# ── prompt_infografica ──────────────────────────────────────────────────────

def test_prompt_infografica_marker_titolo_e_blocco(profilo_mario, testo_storia):
    p = prompt_infografica(testo_storia, profilo_mario)
    assert "---TITOLO---" in p
    assert "---BLOCCO 1---" in p


def test_prompt_infografica_ha_glossario(profilo_mario, testo_storia):
    p = prompt_infografica(testo_storia, profilo_mario)
    assert "---GLOSSARIO---" in p


def test_prompt_infografica_include_testo(profilo_sofia, testo_storia):
    p = prompt_infografica(testo_storia, profilo_sofia)
    assert "Canossa" in p


# ── prompt_slide ─────────────────────────────────────────────────────────────

def test_prompt_slide_marker_slide(profilo_mario, testo_storia):
    p = prompt_slide(testo_storia, profilo_mario)
    assert "---SLIDE 1---" in p
    assert "---SLIDE 2---" in p
    assert "---SLIDE N---" in p


def test_prompt_slide_cosa_impariamo_oggi(profilo_mario, testo_storia):
    p = prompt_slide(testo_storia, profilo_mario)
    assert "Cosa impariamo oggi" in p


def test_prompt_slide_include_testo(profilo_mario, testo_storia):
    p = prompt_slide(testo_storia, profilo_mario)
    assert "Gregorio VII" in p


# ── prompt_quiz ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("tipo", ["A", "B", "C"])
def test_prompt_quiz_dichiara_tipo(tipo):
    p = prompt_quiz("testo adattato finto", tipo)
    assert f"Tipo di quiz: {tipo}" in p


def test_prompt_quiz_contiene_soluzioni():
    p = prompt_quiz("testo adattato finto", "A")
    assert "SOLUZIONI" in p


def test_prompt_quiz_default_a():
    p = prompt_quiz("testo adattato finto")
    assert "Tipo di quiz: A" in p
    assert "scelta multipla" in p


def test_prompt_quiz_tipo_b_vero_falso():
    p = prompt_quiz("testo", "B")
    assert "Vero/Falso" in p


def test_prompt_quiz_tipo_c_scaffolding():
    p = prompt_quiz("testo", "C")
    assert "scaffolding" in p


def test_prompt_quiz_tipo_sconosciuto_fallback_a():
    p = prompt_quiz("testo", "Z")
    # Tipo sconosciuto -> usa le istruzioni di A (scelta multipla).
    assert "scelta multipla" in p


# ── prompt_glossario_pro ─────────────────────────────────────────────────────

def test_prompt_glossario_pro_campi():
    p = prompt_glossario_pro("testo adattato finto", {})
    for campo in ("TERMINE:", "DEFINIZIONE:", "ESEMPIO:", "IMMAGINE:"):
        assert campo in p


def test_prompt_glossario_pro_livello_da_profilo():
    profilo = {"profilo_cognitivo": {"aree_difficolta": {"lettura": "alta"}}}
    p = prompt_glossario_pro("testo finto", profilo)
    assert "(alta)" in p


def test_prompt_glossario_pro_livello_default_media():
    p = prompt_glossario_pro("testo finto", {})
    assert "(media)" in p


# ── Integrazione con il client mockato ───────────────────────────────────────

def test_genera_con_client_mockato(mock_genai, profilo_mario, testo_storia):
    from google import genai

    client = genai.Client(api_key="fake-key-for-tests")
    risposta = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_testo(testo_storia, profilo_mario),
    )
    assert risposta.text
    assert "---TESTO ADATTATO---" in client.models.prompts[0]


def test_client_mockato_non_usa_chiave_reale(mock_genai):
    from google import genai

    client = genai.Client(api_key="fake-key-for-tests")
    assert client.api_key == "fake-key-for-tests"
