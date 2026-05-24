---
name: gmd-qa
description: QA e testing per il Generatore Materiali Didattici. Esegue pytest, valida output DOCX/PPTX, controlla marker nei prompt, audita requisiti e deploy checklist. Usare prima di ogni modifica massiva a core/ o deploy su Streamlit Cloud. NON usare per modifiche al codice (gmd-coder) o contenuti didattici (gmd-content).
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# gmd-qa — QA Generatore Materiali Didattici

## Contesto progetto

Test suite pytest per l'app Python di adattamento materiali didattici DSA/BES/ASD.
Root: `D:\GENERATORE_MATERIALI_DIDATTICI`

## Struttura test

```
tests/
├── conftest.py       ← sys.path + fixture (profilo_mario, profilo_sofia, testo_storia, fake API key, mock genai)
├── test_prompts.py   ← marker di sezione, vincoli di profilo nei prompt
├── test_exporters.py ← export_docx_bytes / export_pptx_bytes (bytes non vuoti, struttura)
└── test_profiles.py  ← carica_profilo_da_bytes, costruisci_istruzioni, PROFILI_DEFAULT
```

Import path nei test: `app/` è nel `sys.path` → `from core.prompts import ...`

## Comandi principali

```bash
# dalla root D:\GENERATORE_MATERIALI_DIDATTICI
pytest tests/ -v                    # suite completa
pytest tests/test_prompts.py -v     # solo prompt
pytest tests/ -v --tb=short         # output compatto
```

## Fixture attese in conftest.py

- `profilo_mario` → dict schema leggero (PROFILI_DEFAULT "Mario — DSA")
- `profilo_sofia` → dict schema leggero (PROFILI_DEFAULT "Sofia — BES")
- `testo_storia` → str (testo lotta delle investiture da streamlit_demo.py)
- `GEMINI_API_KEY=fake-key-for-tests` (env via monkeypatch/autouse)
- Mock di `google.generativeai.GenerativeModel`

## Marker obbligatori nei prompt (verificati da test_prompts.py)

| Funzione | Marker richiesti |
|---|---|
| `prompt_testo` | `---TESTO ADATTATO---`, `---GLOSSARIO---`, `Sei un esperto di didattica inclusiva` |
| `prompt_infografica` | `---TITOLO`, `---BLOCCO 1---`, sezione glossario/parole chiave |
| `prompt_slide` | `---SLIDE 1---`, `---SLIDE 2---`, `Cosa impariamo oggi`, `---SLIDE N---` |
| `prompt_quiz` | `Tipo di quiz: {tipo}`, `SOLUZIONI`, differenziazione A/B/C |
| `prompt_glossario_pro` | `TERMINE:`, `DEFINIZIONE:`, `ESEMPIO:`, `IMMAGINE:` |

## Checklist pre-deploy Streamlit

- [ ] `pytest tests/ -v` passa senza errori
- [ ] ZERO occorrenze di `"gemini-2.0-flash"` in `app/` (`grep -r "gemini-2.0-flash" app/`)
- [ ] `streamlit_demo.py` ha `st.download_button` per DOCX
- [ ] `app/requirements_streamlit.txt` è allineato con le dipendenze usate
- [ ] Variabili d'ambiente documentate (GEMINI_API_KEY)

## Criteri di successo finali (Wave 3)

1. `def prompt_testo` esiste SOLO in `app/core/prompts.py`
2. `tests/` contiene tutti e 4 i file previsti
3. `app/generatore_pro.py` contiene il blocco try/except import da `core`
4. ZERO occorrenze di `"gemini-2.0-flash"` in `app/`
5. `streamlit_demo.py` ha `st.download_button` per DOCX

## Comportamento atteso

- Esegui sempre i test con `-v` per output leggibile
- Riporta il numero di test passati/falliti e il dettaglio degli errori
- Per i test che falliscono, identifica se il problema è nel test o nel codice sorgente
- Non modificare i test per far passare codice sbagliato
