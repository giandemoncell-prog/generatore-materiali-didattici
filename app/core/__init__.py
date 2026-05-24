# core/__init__.py — Interfaccia pubblica del package core.

from .config import (
    MAX_CHARS,
    MAX_PAROLE_FRASE_DEFAULT,
    MAX_RICHIESTE,
    MODELLO_GEMINI,
)
from .exporters import (
    export_docx_bytes,
    export_pptx_bytes,
    salva_slide_pptx,
    salva_testo_docx,
)
from .profiles import (
    PROFILI_DEFAULT,
    carica_profilo,
    carica_profilo_da_bytes,
    costruisci_istruzioni,
)
from .prompts import (
    prompt_glossario_pro,
    prompt_infografica,
    prompt_quiz,
    prompt_slide,
    prompt_testo,
)

__all__ = [
    "MODELLO_GEMINI",
    "MAX_CHARS",
    "MAX_RICHIESTE",
    "MAX_PAROLE_FRASE_DEFAULT",
    "prompt_testo",
    "prompt_infografica",
    "prompt_slide",
    "prompt_quiz",
    "prompt_glossario_pro",
    "PROFILI_DEFAULT",
    "carica_profilo",
    "carica_profilo_da_bytes",
    "costruisci_istruzioni",
    "salva_testo_docx",
    "salva_slide_pptx",
    "export_docx_bytes",
    "export_pptx_bytes",
]
