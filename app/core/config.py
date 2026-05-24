# core/config.py — Costanti condivise del Generatore di Materiali Didattici Inclusivi.
#
# Modulo foglia: NON importa nulla dal package `core`.

MODELLO_GEMINI: str = "gemini-2.5-flash"  # aggiorna se obsoleto: aistudio.google.com/models
MAX_CHARS: int = 5000                      # limite caratteri testo input
MAX_RICHIESTE: int = 5                     # generazioni per sessione (demo Streamlit)
MAX_PAROLE_FRASE_DEFAULT: int = 20         # default frasi brevi
