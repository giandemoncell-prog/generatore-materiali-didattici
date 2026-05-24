# Deploy su Streamlit Community Cloud

## Prerequisiti

1. Account GitHub (gratuito): github.com
2. Account Streamlit Community Cloud (gratuito): share.streamlit.io
3. Chiave API Gemini (gratuita): aistudio.google.com → "Get API key"

---

## Passo 1 — Crea repo GitHub

1. Vai su github.com → **New repository**
2. Nome consigliato: `generatore-dsa`
3. Visibility: **Public** (obbligatorio per Streamlit Community Cloud gratuito)
4. Clicca **Create repository**

---

## Passo 2 — Carica i file

Carica su GitHub questi file (tramite drag-and-drop o GitHub Desktop):

```
generatore-dsa/
├── app/
│   ├── requirements.txt
│   ├── streamlit_demo.py
│   └── core/
│       ├── __init__.py
│       ├── config.py
│       ├── prompts.py
│       ├── profiles.py
│       └── exporters.py
```

**IMPORTANTE:** NON caricare `.streamlit/secrets.toml` — contiene la chiave API.

---

## Passo 3 — Deploy su Streamlit Cloud

1. Vai su **share.streamlit.io** → **New app**
2. Collega il tuo account GitHub
3. Seleziona il repository `generatore-dsa`
4. **Main file path:** `app/streamlit_demo.py`
5. Clicca **Advanced settings** → **Secrets**
6. Incolla:
   ```toml
   GEMINI_API_KEY = "la-tua-chiave-api-gemini"
   ```
7. Clicca **Deploy**

---

## URL risultante

Streamlit assegnerà automaticamente un URL tipo:
`https://generatore-dsa.streamlit.app`

Inserisci questo URL in:
- `04_contenuti/00_introduzione.md` (fondo introduzione)
- `04_contenuti/09_funzionalita_pro.md`
- `04_contenuti/11_appendici.md` (Appendice D)

---

## Note operative

- **Limite demo:** 5 generazioni per sessione (si azzera ricaricando)
- **Costo API Gemini:** il piano gratuito di Google AI Studio copre ~60 richieste/minuto — sufficiente per una demo
- **Se la chiave va in timeout:** genera una nuova chiave su aistudio.google.com e aggiornala nei Secrets di Streamlit Cloud (App settings → Secrets)

---

## Stato readiness 22/5

**Data verifica:** 2026-05-22
**Verificato da:** dsa-developer (claude-sonnet-4-6)

### Esito: PRONTO

| Componente | Stato | Note |
|---|---|---|
| `streamlit_demo.py` — import | OK | `streamlit`, `google.genai` (nuovo SDK) — nessun import mancante |
| `streamlit_demo.py` — path locali | OK | Nessun path hardcoded |
| `streamlit_demo.py` — API key | OK | `st.secrets["GEMINI_API_KEY"]` |
| `streamlit_demo.py` — rate limiting | OK | 5 generazioni/sessione via `session_state.contatore`; il limite per IP non e' implementabile su Streamlit Community Cloud senza backend persistente — il limite per sessione e' la soluzione corretta per questo stack |
| `streamlit_demo.py` — modello Gemini | OK | `gemini-2.5-flash` via `core.config.MODELLO_GEMINI` |
| `requirements.txt` — versioni | OK | `streamlit>=1.35.0` e `google-genai>=1.0.0` compatibili con Python 3.11 su Streamlit Community Cloud |
| `DEPLOY_STREAMLIT.md` — repo GitHub | OK | Nome `generatore-dsa`, visibility Public, istruzioni complete |
| `DEPLOY_STREAMLIT.md` — file da caricare | OK | `app/requirements.txt` e `app/streamlit_demo.py` + `app/core/` |
| `DEPLOY_STREAMLIT.md` — secret | OK | Istruzioni TOML presenti, avvertimento NO secrets.toml presente |

### Gap non bloccanti (da valutare post-lancio)

- **Profilo Giulia (ADHD)** non presente nella demo. Il profilo e' documentato in `04_contenuti/04_profilo_studente.md` sezione 4.6 e nel CLAUDE.md. Aggiungibile in una futura iterazione senza impatto sul deploy.

### Checklist pre-deploy per Gianluca

- [ ] Crea repo `generatore-dsa` su GitHub (Public)
- [ ] Carica la cartella `app/` con `requirements.txt`, `streamlit_demo.py` e la sottocartella `core/`
- [ ] Su share.streamlit.io: New app → main file path `app/streamlit_demo.py`
- [ ] Aggiungi secret `GEMINI_API_KEY = "la-tua-chiave"` in Advanced settings → Secrets
- [ ] Verifica che l'URL assegnato sia `generatore-dsa.streamlit.app`
- [ ] Aggiorna i riferimenti URL nel manoscritto (introduzione, cap.9, App.D)
