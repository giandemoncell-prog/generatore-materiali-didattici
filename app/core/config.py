# core/config.py — Costanti condivise del Generatore di Materiali Didattici Inclusivi.
#
# Modulo foglia: NON importa nulla dal package `core`.

import os

MODELLO_GEMINI: str = "gemini-2.5-flash"  # aggiorna se obsoleto: aistudio.google.com/models
MAX_CHARS: int = 5000                      # limite caratteri testo input
MAX_RICHIESTE: int = int(os.environ.get("MAX_RICHIESTE", "5"))  # generazioni per sessione; 0 = illimitato
MAX_PAROLE_FRASE_DEFAULT: int = 20         # default frasi brevi
