# Deploy su Streamlit Community Cloud

## Prerequisiti

1. Account GitHub (già attivo): github.com/giandemoncell-prog
2. Account Streamlit Community Cloud (gratuito): share.streamlit.io
3. Chiave API Gemini (gratuita): aistudio.google.com → "Get API key"

---

## Passo 1 — Push del repo su GitHub

Il repo è già configurato con il remote corretto. Esegui da terminale in `D:\GENERATORE_MATERIALI_DIDATTICI`:

```
git push origin master
```

Repository GitHub: **https://github.com/giandemoncell-prog/generatore-materiali-didattici**

---

## Passo 2 — Deploy su Streamlit Cloud

1. Vai su **share.streamlit.io** → **New app**
2. Collega (o usa) il tuo account GitHub `giandemoncell-prog`
3. Seleziona il repository **`generatore-materiali-didattici`**
4. **Main file path:** `app/streamlit_demo.py`
5. Clicca **Advanced settings** → **Secrets**
6. Incolla:
   ```toml
   GEMINI_API_KEY = "la-tua-chiave-api-gemini"
   ```
7. Clicca **Deploy**

**IMPORTANTE:** NON caricare `.streamlit/secrets.toml` — contiene la chiave API.

---

## URL risultante

Streamlit assegnerà un URL automatico. Puoi personalizzarlo in **App settings** dopo il deploy.

Una volta ottenuto l'URL reale, comunica a Claude di aggiornare questi file:
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
| `requirements.txt` — versioni | OK | `streamlit>=1.35.0` e `google-genai>=2.5.0` compatibili con Python 3.11 su Streamlit Community Cloud |
| `DEPLOY_STREAMLIT.md` — repo GitHub | OK | Nome `generatore-dsa`, visibility Public, istruzioni complete |
| `DEPLOY_STREAMLIT.md` — file da caricare | OK | `app/requirements.txt` e `app/streamlit_demo.py` + `app/core/` |
| `DEPLOY_STREAMLIT.md` — secret | OK | Istruzioni TOML presenti, avvertimento NO secrets.toml presente |

### Gap non bloccanti (da valutare post-lancio)

- **Profilo Giulia (ADHD)** non presente nella demo. Il profilo e' documentato in `04_contenuti/04_profilo_studente.md` sezione 4.6 e nel CLAUDE.md. Aggiungibile in una futura iterazione senza impatto sul deploy.

### Checklist pre-deploy per Gianluca (28/5)

- [ ] `git push origin master` da `D:\GENERATORE_MATERIALI_DIDATTICI`
- [ ] Su share.streamlit.io: New app → repo `generatore-materiali-didattici` → main file `app/streamlit_demo.py`
- [ ] Aggiungi secret `GEMINI_API_KEY = "la-tua-chiave"` in Advanced settings → Secrets
- [ ] Copia l'URL assegnato da Streamlit
- [ ] Manda l'URL a Claude → aggiorna manoscritto (introduzione, cap.9, App.D)
