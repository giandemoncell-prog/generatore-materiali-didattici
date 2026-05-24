"""Fixture condivise per la test suite.

Aggiunge ``app/`` al ``sys.path`` così i test possono importare ``from core...``.
Mocka l'accesso a Gemini: nessuna chiave API reale necessaria.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ── Rendi importabile il package core (sta in app/core) ──
_APP_DIR = Path(__file__).resolve().parent.parent / "app"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))


# ── Env: fake API key per tutti i test ──
@pytest.fixture(autouse=True)
def fake_gemini_api_key(monkeypatch):
    """Imposta una chiave API fittizia per ogni test (autouse)."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-tests")
    return "fake-key-for-tests"


# ── Profili (schema leggero, da PROFILI_DEFAULT) ──
@pytest.fixture
def profilo_mario() -> dict:
    return {
        "max_parole_frase": 20,
        "punti_per_blocco": 3,
        "note": (
            "Frasi brevi (max 20 parole). Un concetto per paragrafo. "
            "Parole chiave in grassetto (max 3 per paragrafo). "
            "Glossario finale con 5 termini difficili."
        ),
    }


@pytest.fixture
def profilo_sofia() -> dict:
    return {
        "max_parole_frase": 18,
        "punti_per_blocco": 3,
        "note": (
            "Usa analogie concrete della vita quotidiana per ogni concetto astratto. "
            "Evita metafore. Usa elenchi puntati invece di paragrafi. "
            "Glossario sempre presente. Frasi max 18 parole."
        ),
    }


@pytest.fixture
def profilo_yaml_completo() -> dict:
    """Profilo nello schema completo YAML (per testare costruisci_istruzioni)."""
    return {
        "presentazione": {
            "font": "Verdana",
            "max_punti_per_slide": 2,
            "max_righe_paragrafo": 3,
        },
        "profilo_cognitivo": {
            "aree_difficolta": {
                "lettura": "alta",
                "scrittura": "media",
                "memoria_di_lavoro": "alta",
            }
        },
        "note_osservazioni": ["Usa elenchi puntati.", "Esempi concreti."],
    }


# ── Testo di esempio (lotta delle investiture, streamlit_demo.py righe 56-63) ──
@pytest.fixture
def testo_storia() -> str:
    return (
        "La lotta per le investiture fu un lungo conflitto tra il papato e l'impero "
        "medievale riguardante il diritto di nominare i vescovi e gli abati. "
        "Il conflitto raggiunse il suo apice con lo scontro tra papa Gregorio VII "
        "e l'imperatore Enrico IV, culminando nell'umiliazione di Canossa nel 1077. "
        "La controversia si concluse con il Concordato di Worms nel 1122, "
        "che stabilì una distinzione tra investitura spirituale e temporale."
    )


# ── Mock del client Gemini (google.genai) ──
class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeModels:
    """Sostituto di client.models — registra i contents ricevuti."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate_content(self, model: str = "", contents: str = "", config=None) -> _FakeResponse:
        self.prompts.append(contents)
        return _FakeResponse("---TESTO ADATTATO---\nTesto finto.\n---GLOSSARIO---\nx: y")


class _FakeClient:
    """Sostituto di google.genai.Client."""

    def __init__(self, api_key: str = "", **kwargs) -> None:
        self.api_key = api_key
        self.models = _FakeModels()


@pytest.fixture
def fake_client() -> _FakeClient:
    return _FakeClient(api_key="fake-key-for-tests")


@pytest.fixture
def mock_genai(monkeypatch):
    """Mocka google.genai: Client -> _FakeClient."""
    from google import genai

    monkeypatch.setattr(genai, "Client", _FakeClient)
    return genai
