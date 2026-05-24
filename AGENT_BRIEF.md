# AGENT_BRIEF — Refactoring Generatore Materiali Didattici Inclusivi

> Documento di kickoff prodotto dall'orchestratore (Wave 0).
> Tutti gli agenti DEVONO conformarsi alle firme e ai vincoli qui definiti.
> Percorsi sempre assoluti dove possibile. Encoding file: UTF-8.

---

## 1. Obiettivo del refactoring

Estrarre la logica condivisa (prompt, profili, exporters, config) in un package
`app/core/` riusabile da tutte e tre le interfacce (CLI, Streamlit, GUI), eliminando
la duplicazione di codice fra `generatore_pro.py` e `streamlit_demo.py`, unificando
il modello Gemini, e introducendo una test suite.

**Stack:** Python 3.11 · Streamlit 1.35+ · google-generativeai · python-docx · python-pptx · pyyaml

---

## 2. Unificazione modello Gemini

- Attuale: `generatore_pro.py` usa `"gemini-2.0-flash"`, `streamlit_demo.py` usa `"gemini-2.5-flash"`.
- **Decisione:** valore unico `MODELLO_GEMINI = "gemini-2.5-flash"` definito in `app/core/config.py`.
- Tutte le interfacce devono leggere la costante dal core (con fallback locale = stesso valore).
- Obiettivo finale: ZERO occorrenze di `"gemini-2.0-flash"` in `app/`.

---

## 3. Struttura target `app/core/`

```
app/core/
├── __init__.py        # espone l'interfaccia pubblica
├── config.py          # costanti
├── prompts.py         # costruzione prompt (consolidati)
├── profiles.py        # caricamento / costruzione istruzioni profilo
└── exporters.py       # generazione DOCX / PPTX (file e bytes)
```

Regola anti-dipendenze-circolari:
- `config.py` non importa nulla dal package.
- `prompts.py` può importare da `config`.
- `profiles.py` può importare da `config`.
- `exporters.py` può importare da `config`.
- `__init__.py` importa dai moduli foglia. Nessun modulo foglia importa `__init__`.

---

## 4. FIRME ESATTE (signature Python complete)

### 4.1 `app/core/config.py`
Solo costanti (nessuna funzione):

```python
MODELLO_GEMINI: str = "gemini-2.5-flash"
MAX_CHARS: int = 5000
MAX_RICHIESTE: int = 5
MAX_PAROLE_FRASE_DEFAULT: int = 20
```

### 4.2 `app/core/prompts.py`

```python
def prompt_testo(testo: str, profilo: dict, note_extra: str = "") -> str: ...
def prompt_infografica(testo: str, profilo: dict) -> str: ...
def prompt_slide(testo: str, profilo: dict) -> str: ...
def prompt_quiz(testo_adattato: str, tipo: str = "A") -> str: ...
def prompt_glossario_pro(testo_adattato: str, profilo: dict) -> str: ...
```

**Note di consolidamento prompt:**
- Le funzioni `prompt_*` devono accettare un `profilo: dict` e funzionare con DUE schemi:
  1. schema "leggero" Streamlit: chiavi `note`, `max_parole_frase`, `punti_per_blocco`.
  2. schema "completo" YAML: chiavi `presentazione`, `profilo_cognitivo.aree_difficolta`, `note_osservazioni`.
- Strategia: derivare un blocco istruzioni testuale tramite `profiles.costruisci_istruzioni(profilo)`
  e usarlo nei prompt. `prompt_testo` accetta `note_extra` che viene appeso alle istruzioni.
- I prompt DEVONO contenere i marker di sezione attesi dai parser e dai test:
  - `prompt_testo`: stringhe `---TESTO ADATTATO---` e `---GLOSSARIO---`,
    intestazione `Sei un esperto di didattica inclusiva`, e il testo originale in coda.
  - `prompt_infografica`: marker tipo `---TITOLO`, `---BLOCCO 1---`, sezione glossario/parole chiave.
  - `prompt_slide`: marker `---SLIDE 1---`, `---SLIDE 2---`, `Cosa impariamo oggi`, `---SLIDE N---`.
  - `prompt_quiz`: deve includere `Tipo di quiz: {tipo}`, la sezione `SOLUZIONI`,
    e differenziare A (scelta multipla) / B (Vero/Falso) / C (domande aperte con scaffolding).
    Default `tipo="A"`; tipo sconosciuto -> fallback alle istruzioni di A.
  - `prompt_glossario_pro`: deve includere i campi `TERMINE:`, `DEFINIZIONE:`, `ESEMPIO:`, `IMMAGINE:`
    e riferimento al livello di difficoltà di lettura del profilo.

### 4.3 `app/core/profiles.py`

```python
PROFILI_DEFAULT: dict  # migrato da streamlit_demo.py righe 12-54 (var. PROFILI)

def carica_profilo(nome_studente: str) -> dict: ...
def carica_profilo_da_bytes(yaml_bytes: bytes) -> dict: ...
def costruisci_istruzioni(profilo: dict) -> str: ...
```

**Dettagli:**
- `carica_profilo(nome_studente)`: replica la logica di `generatore_pro.py` (legge
  `profili/profilo_<nome>.yaml`). Per riuso in libreria/test, in caso di file mancante
  sollevare `FileNotFoundError` invece di `sys.exit` (la CLI gestirà l'errore al chiamante).
- `carica_profilo_da_bytes(yaml_bytes)`: per upload Streamlit. Fa `yaml.safe_load(yaml_bytes)`.
  - YAML vuoto / `None` -> ritorna `{}`.
  - YAML malformato -> solleva `yaml.YAMLError` (i test verificano questo comportamento).
- `costruisci_istruzioni(profilo)`: deve gestire ENTRAMBI gli schemi (leggero Streamlit e
  completo YAML). Restituisce una stringa di bullet (`- ...`). Logica base dalla versione
  `generatore_pro.py` (righe 74-96), estesa per leggere `profilo["note"]`/`max_parole_frase`/
  `punti_per_blocco` quando presenti (schema Streamlit).

### 4.4 `app/core/exporters.py`

```python
def salva_testo_docx(contenuto: str, profilo: dict, percorso: str) -> None: ...
def salva_slide_pptx(contenuto: str, profilo: dict, percorso: str) -> None: ...
def export_docx_bytes(testo: str, profilo: dict) -> bytes: ...
def export_pptx_bytes(slide_testo: str, profilo: dict) -> bytes: ...
```

**Dettagli:**
- `salva_testo_docx` / `salva_slide_pptx`: estratti TALI E QUALI da `generatore_pro.py`
  (righe 246-289 e 292-343). Firma con annotazione di ritorno `-> None`.
- `export_docx_bytes(testo, profilo)`: costruisce lo stesso `Document` di `salva_testo_docx`
  ma salva su `io.BytesIO`, ritorna `bytes` (`buffer.getvalue()`). NON scrive su disco.
- `export_pptx_bytes(slide_testo, profilo)`: idem per `Presentation` -> `io.BytesIO` -> `bytes`.
- Refactoring consigliato: estrarre helper privati `_costruisci_documento(...)` /
  `_costruisci_presentazione(...)` e farli usare sia dalle versioni "salva su file" sia da
  quelle "bytes", per evitare duplicazione interna.
- Output garantito non vuoto: `len(...) > 0`. DOCX deve contenere paragrafi; PPTX >= 1 slide
  (per input di slide ben formato con almeno un blocco `---SLIDE`).

### 4.5 `app/core/__init__.py`
Espone l'interfaccia pubblica via re-export:

```python
from .config import MODELLO_GEMINI, MAX_CHARS, MAX_RICHIESTE, MAX_PAROLE_FRASE_DEFAULT
from .prompts import (
    prompt_testo, prompt_infografica, prompt_slide, prompt_quiz, prompt_glossario_pro,
)
from .profiles import (
    PROFILI_DEFAULT, carica_profilo, carica_profilo_da_bytes, costruisci_istruzioni,
)
from .exporters import (
    salva_testo_docx, salva_slide_pptx, export_docx_bytes, export_pptx_bytes,
)

__all__ = [
    "MODELLO_GEMINI", "MAX_CHARS", "MAX_RICHIESTE", "MAX_PAROLE_FRASE_DEFAULT",
    "prompt_testo", "prompt_infografica", "prompt_slide", "prompt_quiz", "prompt_glossario_pro",
    "PROFILI_DEFAULT", "carica_profilo", "carica_profilo_da_bytes", "costruisci_istruzioni",
    "salva_testo_docx", "salva_slide_pptx", "export_docx_bytes", "export_pptx_bytes",
]
```

---

## 5. VINCOLO CRITICO di retrocompatibilità (`generatore_pro.py`)

**NON riscrivere la logica di `generatore_pro.py`.** Aggiungere SOLO, in cima al file (dopo
gli import esistenti), il blocco try/except che preferisce il core quando disponibile, e
mantenere le definizioni locali come fallback. Le definizioni locali NON vanno cancellate;
servono se il package `core` non è importabile (es. esecuzione fuori da `app/`).

Blocco da inserire in `generatore_pro.py`:

```python
try:
    from core.config import MODELLO_GEMINI
    from core.prompts import prompt_testo, prompt_infografica, prompt_slide, prompt_quiz
    from core.exporters import salva_testo_docx, salva_slide_pptx
    from core.profiles import carica_profilo, costruisci_istruzioni
    _CORE_AVAILABLE = True
except ImportError:
    _CORE_AVAILABLE = False
```

**Nota di naming (importante per il refactor del CLI):** in `generatore_pro.py` le funzioni
prompt locali si chiamano `costruisci_prompt_testo`, `costruisci_prompt_infografica`,
`costruisci_prompt_slide`, `costruisci_prompt_glossario_pro`, `costruisci_prompt_quiz`,
mentre nel core si chiamano `prompt_testo`, `prompt_infografica`, ecc.
- Firma differente: il core riceve `profilo: dict` (deriva le istruzioni internamente),
  mentre le locali ricevono `istruzioni: str`.
- Per Wave 1 NON è richiesto cablare le chiamate del `main()` sul core: è SUFFICIENTE inserire
  il blocco try/except sopra (criterio di successo #3). Il fallback locale resta autoritativo.
- Per Wave 2/3 NON modificare il `main()` del CLI: il vincolo è solo "il blocco import esiste".
  La condizione #1 (`def prompt_testo` solo nel core) è soddisfatta perché nel CLI la funzione
  locale si chiama `costruisci_prompt_testo`, non `prompt_testo`.

---

## 6. Schema profilo YAML (riferimento per Agent-Docs e profiles.py)

Il codice CLI/GUI legge questo schema. Le chiavi usate dal codice sono:

```yaml
identificativo:
  nome: Giulia
  classroom_course_id: ""        # opzionale, usato da F.3
presentazione:
  font: "OpenDyslexic"           # .split()[0] usato come font name
  max_punti_per_slide: 3
  max_righe_paragrafo: 4
profilo_cognitivo:
  aree_difficolta:
    lettura: media               # valori liberi: bassa/media/alta
    scrittura: media
    calcolo: bassa
    memoria_di_lavoro: alta
    attenzione: alta
  aree_forza:
    ragionamento_visivo: alta
strumenti_compensativi:
  mappe_concettuali: true
  sintesi_vocale: true
note_osservazioni:
  - "Una nota per riga, appesa alle istruzioni del prompt."
```

`costruisci_istruzioni` usa: `presentazione.max_punti_per_slide`, `presentazione.max_righe_paragrafo`,
`profilo_cognitivo.aree_difficolta.{lettura,scrittura,memoria_di_lavoro}`, `note_osservazioni`.

---

## 7. PROFILI_DEFAULT (da migrare in profiles.py)

Migrare integralmente il dict `PROFILI` da `streamlit_demo.py` righe 12-54. Chiavi attese
(verificate dai test): `"Mario — DSA (dislessia + disgrafia)"`, `"Sofia — BES (attenzione + italiano L2)"`,
`"Lorenzo — ASD Level 2 + CAA"`, `"Profilo base (generico)"`, `"Profilo personalizzato..."`.
Ogni valore ha le chiavi `max_parole_frase`, `punti_per_blocco`, `note`.

---

## 8. Test suite (riferimento per Agent-QA)

```
tests/
├── conftest.py          # fixture condivise
├── test_prompts.py      # Wave 1
├── test_exporters.py    # Wave 2
└── test_profiles.py     # Wave 2
```

**Fixture richieste in `conftest.py`:**
- `profilo_mario` -> dict (schema leggero, da PROFILI_DEFAULT "Mario — DSA").
- `profilo_sofia` -> dict (schema leggero, da PROFILI_DEFAULT "Sofia — BES").
- `testo_storia` -> str = il testo della lotta delle investiture (`TESTO_ESEMPIO`,
  `streamlit_demo.py` righe 56-63).
- Env `GEMINI_API_KEY=fake-key-for-tests` (via `monkeypatch`/`autouse` fixture).
- Mock di `google.generativeai.GenerativeModel` per i test che simulano la generazione.

**Import path nei test:** i moduli sono in `app/core/`. I test devono poter fare
`from core.prompts import ...`. Aggiungere in `conftest.py` l'inserimento di
`app/` nel `sys.path` (es. `sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))`).

---

## 9. Firme con type hints (riferimento per Agent-Types su CLI/GUI)

Funzioni chiave già presenti in `generatore_pro.py` da annotare/confermare:

```python
def carica_api_key() -> str: ...
def carica_profilo(nome_studente: str) -> dict: ...
def carica_testo(percorso_testo: str) -> str: ...
def costruisci_istruzioni(profilo: dict) -> str: ...
def genera_contenuto(prompt: str, model: Any) -> str: ...        # model = genai.GenerativeModel
def salva_testo_docx(contenuto: str, profilo: dict, percorso: str) -> None: ...
def salva_slide_pptx(contenuto: str, profilo: dict, percorso: str) -> None: ...
def salva_testo_txt(contenuto: str, percorso: str) -> None: ...
def aggiorna_registro(studente: str, testo: str, cartella_out: str) -> None: ...
```

In `gui_generatore.py`:

```python
def ottieni_studenti() -> list[str]: ...
def leggi_profilo(nome_studente: str) -> dict: ...
def riassumi_profilo(profilo: dict) -> str: ...
def apri_cartella(percorso: str) -> None: ...
```

`Any` richiede `from typing import Any`. NON modificare `streamlit_demo.py` (lo fa Agent-Streamlit in Wave 2).

---

## 10. Stato attuale repository (rilevato in Wave 0)

- I profili YAML reali NON esistono ancora: `profili/profilo_*.yaml` è solo referenziato dal codice.
  I file in `campioni/profili/*.md` sono descrizioni testuali, NON YAML.
- Agent-Docs deve creare `campioni/profili/profilo_giulia_adhd.yaml` conforme allo schema §6.
- requirements esistenti:
  - `app/requirements.txt`: streamlit, google-generativeai, python-docx
  - `app/requirements_pro.txt`: + python-pptx, pyyaml, google-api-*, video deps
  - `app/requirements_streamlit.txt`: streamlit, google-generativeai, python-docx
- README.md è alla root del repo.
- Esistono `docs/SETUP_CHROMEBOOK.md` e `docs/DEPLOY_STREAMLIT.md`.

---

## 11. Criteri di successo finali (Wave 3)

1. `def prompt_testo` esiste SOLO in `app/core/prompts.py` (CLI usa `costruisci_prompt_testo`).
2. `tests/` contiene `conftest.py`, `test_prompts.py`, `test_exporters.py`, `test_profiles.py`.
3. `app/generatore_pro.py` contiene il blocco try/except import da `core`.
4. ZERO occorrenze di `"gemini-2.0-flash"` in `app/`.
5. `streamlit_demo.py` ha `st.download_button` per DOCX.
