# Generatore di Materiali Didattici Inclusivi

App estratta dal progetto "AI e DSA" — Gianluca Demontis

## Struttura

```
GENERATORE_MATERIALI_DIDATTICI\
├── app\
│   ├── core\                    ← Package condiviso (vedi "Architettura moduli")
│   │   ├── config.py            ← Costanti (MODELLO_GEMINI, MAX_CHARS, ...)
│   │   ├── prompts.py           ← Costruzione prompt consolidata
│   │   ├── profiles.py          ← Caricamento profili + istruzioni
│   │   └── exporters.py         ← Export DOCX/PPTX (file e bytes)
│   ├── streamlit_demo.py        ← Web app (Streamlit) — da deployare su Streamlit Cloud
│   ├── generatore_pro.py        ← CLI Python completa (testo+infografica+slide+quiz)
│   ├── gui_generatore.py        ← Interfaccia desktop Tkinter
│   ├── requirements.txt         ← Dipendenze per Streamlit (streamlit + google-generativeai)
│   ├── requirements_pro.txt     ← Dipendenze complete (+ docx, pptx, Classroom, TTS)
│   ├── requirements_streamlit.txt
│   └── requirements_full.txt    ← Merge dei requirements + toolchain di test
├── tests\                       ← Test suite pytest (conftest + test_*.py)
├── docs\
│   ├── DEPLOY_STREAMLIT.md      ← Guida deploy su Streamlit Community Cloud
│   └── SETUP_CHROMEBOOK.md      ← Setup su Chromebook/Linux
├── campioni\
│   ├── profili\                 ← Profili studente di esempio (markdown)
│   └── testi\                   ← Testi originali e versioni adattate di esempio
├── profili\                     ← Metti qui i profili YAML degli studenti (profilo_nome.yaml)
├── testi\                       ← Metti qui i file .txt da adattare
└── output\                      ← L'app salva qui i materiali generati
```

## Avvio rapido

### Web (Streamlit)
```bash
pip install -r app/requirements.txt
streamlit run app/streamlit_demo.py
```
Richiede chiave API Gemini in `GEMINI_API_KEY` (env var o `.env`).

### CLI
```bash
pip install -r app/requirements_pro.txt
python app/generatore_pro.py --studente mario --testo testi/mio_testo.txt
```
Output in `output/mario/YYYY-MM-DD/`

### GUI Desktop
```bash
python app/gui_generatore.py
```

## Profili studente (YAML)

Crea un file `profili/profilo_nomestudente.yaml` con questa struttura:

```yaml
presentazione:
  font: Arial
  max_punti_per_slide: 3
  max_righe_paragrafo: 4

profilo_cognitivo:
  aree_difficolta:
    lettura: alta
    memoria_di_lavoro: media
    scrittura: alta
  aree_forza:
    comprensione_orale: alta

strumenti_compensativi:
  sintesi_vocale: true
  mappe_concettuali: true

note_osservazioni:
  - Usare elenchi puntati invece di paragrafi continui
  - Evidenziare i concetti chiave in grassetto

identificativo:
  classroom_course_id: ""  # opzionale, per integrazione Google Classroom
```

Vedi esempi in `campioni/profili/`.

## Architettura moduli

La logica condivisa dalle tre interfacce (CLI, Web, Desktop) vive nel package
`app/core/`, così da eliminare la duplicazione di codice e centralizzare le scelte
di configurazione (es. il modello Gemini).

```
app/core/
├── config.py     → MODELLO_GEMINI = "gemini-2.5-flash", MAX_CHARS, MAX_RICHIESTE, ...
├── prompts.py    → prompt_testo, prompt_infografica, prompt_slide, prompt_quiz, prompt_glossario_pro
├── profiles.py   → carica_profilo, carica_profilo_da_bytes, costruisci_istruzioni, PROFILI_DEFAULT
├── exporters.py  → salva_testo_docx/salva_slide_pptx (su file) + export_docx_bytes/export_pptx_bytes (bytes)
└── __init__.py   → interfaccia pubblica del package
```

Dipendenze interne (nessun ciclo): `config` è una foglia; `prompts`, `profiles` ed
`exporters` importano solo da `config` (e `prompts` da `profiles`); `__init__`
ri-esporta i moduli foglia.

Il modello Gemini è unificato a **`gemini-2.5-flash`** tramite la costante
`core.config.MODELLO_GEMINI`. La CLI (`generatore_pro.py`) importa il core con un
blocco `try/except ImportError` e mantiene definizioni locali come fallback, restando
retrocompatibile anche se il package `core` non è importabile.

Per usare il core come libreria (i moduli sono in `app/core/`):

```python
import sys
sys.path.insert(0, "app")
from core.prompts import prompt_testo
from core.exporters import export_docx_bytes
```

## Running Tests

La test suite usa **pytest** e mocka le chiamate a Gemini (nessuna chiave API reale
necessaria). Installa la toolchain completa ed esegui i test dalla root del repo:

```bash
pip install -r app/requirements_full.txt
pytest tests/ -v
```

I test sono organizzati così:

| File                     | Copertura                                                        |
|--------------------------|------------------------------------------------------------------|
| `tests/conftest.py`      | Fixture condivise (profili, testo di esempio, fake API key)      |
| `tests/test_prompts.py`  | Marker di sezione e vincoli di profilo nei prompt                |
| `tests/test_exporters.py`| `export_docx_bytes` / `export_pptx_bytes` (bytes non vuoti, ecc.) |
| `tests/test_profiles.py` | `carica_profilo_da_bytes`, `costruisci_istruzioni`, `PROFILI_DEFAULT` |

Il `conftest.py` aggiunge `app/` al `sys.path`, quindi i test importano i moduli
con `from core.prompts import ...`.

## Chiave API Gemini

Ottieni la chiave gratuita su: https://aistudio.google.com/apikey

Crea un file `.env` nella cartella dove esegui lo script:
```
GEMINI_API_KEY=la_tua_chiave_qui
```
