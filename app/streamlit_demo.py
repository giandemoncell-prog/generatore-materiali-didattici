import concurrent.futures
import os
import sys

import streamlit as st
from google import genai
from google.genai import types as _genai_types

_GENERA_CONFIG = _genai_types.GenerateContentConfig(temperature=0.7, max_output_tokens=8192)

# ── RETROCOMPATIBILITÀ CORE ───────────────────────────────────────────────────
# Preferisci i moduli condivisi in core/ quando importabili. Le definizioni locali
# più sotto (prompt_*, ecc.) restano come fallback se core/ non è disponibile.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from core.config import MODELLO_GEMINI as _CORE_MODELLO, MAX_CHARS as _CORE_MAX_CHARS, MAX_RICHIESTE as _CORE_MAX_RICHIESTE
    from core.prompts import (
        prompt_testo as _core_prompt_testo,
        prompt_infografica as _core_prompt_infografica,
        prompt_slide as _core_prompt_slide,
        prompt_quiz as _core_prompt_quiz,
        prompt_glossario_pro as _core_prompt_glossario_pro,
    )
    from core.profiles import carica_profilo_da_bytes as _core_carica_profilo_da_bytes, PROFILI_DEFAULT as _CORE_PROFILI_DEFAULT
    from core.exporters import export_docx_bytes as _core_export_docx_bytes, export_pptx_bytes as _core_export_pptx_bytes
    _CORE_AVAILABLE = True
except ImportError:
    _CORE_AVAILABLE = False

# ── CONFIGURAZIONE ────────────────────────────────────────────────────────────

if _CORE_AVAILABLE:
    MODELLO = _CORE_MODELLO
    MAX_RICHIESTE = _CORE_MAX_RICHIESTE
    MAX_CHARS = _CORE_MAX_CHARS
else:
    MODELLO = "gemini-2.5-flash"
    MAX_RICHIESTE = 5   # per sessione — si azzera ricaricando la pagina
    MAX_CHARS = 5000    # fix 5: limite caratteri testo input

PROFILI = _CORE_PROFILI_DEFAULT if _CORE_AVAILABLE else {
    "Mario — DSA (dislessia + disgrafia)": {
        "max_parole_frase": 20,
        "punti_per_blocco": 3,
        "note": (
            "Frasi brevi (max 20 parole). Un concetto per paragrafo. "
            "Parole chiave in grassetto (max 3 per paragrafo). "
            "Glossario finale con 5 termini difficili."
        ),
    },
    "Sofia — BES (attenzione + italiano L2)": {
        "max_parole_frase": 18,
        "punti_per_blocco": 3,
        "note": (
            "Usa analogie concrete della vita quotidiana per ogni concetto astratto. "
            "Evita metafore. Usa elenchi puntati invece di paragrafi. "
            "Glossario sempre presente. Frasi max 18 parole."
        ),
    },
    "Lorenzo — ASD Level 2 + CAA": {
        "max_parole_frase": 12,
        "punti_per_blocco": 2,
        "note": (
            "Una sola informazione per frase. Frasi max 12 parole. "
            "Struttura rigida e prevedibile. "
            "Per ogni concetto chiave suggerisci un simbolo visivo descrittivo tra parentesi quadre: [SIMBOLO: descrizione]. "
            "Niente metafore, niente ironia."
        ),
    },
    "Profilo base (generico)": {
        "max_parole_frase": 20,
        "punti_per_blocco": 3,
        "note": (
            "Adattamento standard per difficoltà di apprendimento generiche. "
            "Frasi brevi, struttura chiara, glossario finale."
        ),
    },
    "Profilo personalizzato...": {
        "max_parole_frase": 20,
        "punti_per_blocco": 3,
        "note": "",
    },
}

TESTO_ESEMPIO = (
    "La lotta per le investiture fu un lungo conflitto tra il papato e l'impero "
    "medievale riguardante il diritto di nominare i vescovi e gli abati. "
    "Il conflitto raggiunse il suo apice con lo scontro tra papa Gregorio VII "
    "e l'imperatore Enrico IV, culminando nell'umiliazione di Canossa nel 1077. "
    "La controversia si concluse con il Concordato di Worms nel 1122, "
    "che stabilì una distinzione tra investitura spirituale e temporale."
)

# ── PROMPT ────────────────────────────────────────────────────────────────────

def prompt_testo(testo: str, profilo: dict, note_extra: str) -> str:
    note = profilo["note"]
    if note_extra:
        note += f" {note_extra}"
    return f"""Sei un esperto di didattica inclusiva per studenti con DSA e BES.
Adatta il testo seguente rispettando TUTTE queste regole:
{note}

Produci:
1. Testo adattato (mantieni tutti i concetti, cambia solo la forma)
2. Glossario con 5-6 parole difficili e definizione semplice

Formato:
---TESTO ADATTATO---
[testo qui]
---GLOSSARIO---
termine: definizione semplice

TESTO ORIGINALE:
{testo}"""


def prompt_infografica(testo: str, profilo: dict) -> str:
    return f"""Crea un'infografica testuale dal testo seguente per uno studente con DSA.
Regole: max {profilo['punti_per_blocco']} punti per blocco, frasi max {profilo['max_parole_frase']} parole.

Identifica 3-4 concetti principali. Per ogni concetto:
- Titolo breve (max 5 parole)
- 2-3 punti elenco
- Suggerimento immagine descrittiva (10 parole)

Formato:
---TITOLO GENERALE---
[titolo]
---BLOCCO 1---
TITOLO: ...
IMMAGINE: ...
• punto 1
• punto 2
[ripeti per ogni blocco]
---PAROLE CHIAVE---
termine: definizione breve

TESTO:
{testo}"""


def prompt_slide(testo: str, profilo: dict) -> str:
    return f"""Crea una struttura di presentazione dal testo seguente per studenti con DSA.
Regole: max {profilo['punti_per_blocco']} punti per slide, frasi max {profilo['max_parole_frase']} parole.

Struttura:
- Slide 1: titolo + materia
- Slide 2: "Cosa impariamo oggi" — 3 obiettivi
- Slide 3-N: un concetto per slide (titolo + punti + descrizione immagine)
- Ultima slide: parole chiave con definizione

Formato:
---SLIDE 1---
TITOLO: ...
SOTTOTITOLO: ...
---SLIDE 2---
TITOLO: Cosa impariamo oggi
• obiettivo 1
• obiettivo 2
• obiettivo 3
---SLIDE N---
TITOLO: ...
IMMAGINE: ...
• punto 1
• punto 2

TESTO:
{testo}"""


def prompt_quiz(testo_adattato: str, tipo: str) -> str:
    istruzioni_tipo = {
        "A": (
            "Crea 5 domande a scelta multipla con 3 opzioni (A, B, C). "
            "Una sola risposta corretta per domanda. "
            "Domande brevi (max 15 parole)."
        ),
        "B": (
            "Crea 6 affermazioni Vero/Falso. "
            "3 vere e 3 false, nell'ordine mescolato. "
            "Per le false, lascia uno spazio 'Correzione: ___'."
        ),
        "C": (
            "Crea 4 domande aperte con scaffolding. "
            "Ogni domanda deve contenere una struttura parziale da completare. "
            "Esempio: 'La lotta per le investiture fu un conflitto tra ___ e ___ che durò ___.' "
            "Evita domande che richiedono più di 2 righe di risposta."
        ),
    }
    return f"""Crea un quiz di verifica per studenti con DSA basato su questo testo adattato.

Tipo di quiz: {tipo}
{istruzioni_tipo.get(tipo, istruzioni_tipo['A'])}

Regole generali:
- Usa il lessico del testo adattato, non dell'originale
- Non usare domande trabocchetto
- Includi la risposta corretta in fondo (sezione SOLUZIONI)
- Il quiz deve poter essere completato in 10-15 minuti

TESTO ADATTATO:
{testo_adattato}"""


# ── OVERRIDE / EXTRA DAL CORE ─────────────────────────────────────────────────
# Se il core è disponibile, usa le sue implementazioni (consolidate) e abilita le
# funzioni aggiuntive non presenti nelle definizioni locali.
if _CORE_AVAILABLE:
    prompt_testo = _core_prompt_testo            # noqa: F811
    prompt_infografica = _core_prompt_infografica  # noqa: F811
    prompt_slide = _core_prompt_slide            # noqa: F811
    prompt_quiz = _core_prompt_quiz              # noqa: F811
    prompt_glossario_pro = _core_prompt_glossario_pro
    carica_profilo_da_bytes = _core_carica_profilo_da_bytes
    export_docx_bytes = _core_export_docx_bytes
    export_pptx_bytes = _core_export_pptx_bytes
else:
    # Fallback minimi se il package core non è importabile.
    def prompt_glossario_pro(testo_adattato: str, profilo: dict) -> str:
        return (
            "Crea un glossario calibrato. Per ogni parola difficile fornisci "
            "TERMINE, DEFINIZIONE, ESEMPIO, IMMAGINE.\n\nTESTO:\n" + testo_adattato
        )

    def carica_profilo_da_bytes(yaml_bytes: bytes) -> dict:
        import yaml
        dati = yaml.safe_load(yaml_bytes)
        return dati if isinstance(dati, dict) else {}

    export_docx_bytes = None  # type: ignore[assignment]
    export_pptx_bytes = None  # type: ignore[assignment]


# ── GENERAZIONE ───────────────────────────────────────────────────────────────

@st.cache_resource
def _init_model():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        return None
    return genai.Client(api_key=api_key)


def genera(prompt: str) -> str:
    client = _init_model()
    if client is None:
        st.error("Chiave API non trovata. Configura GEMINI_API_KEY nei secrets di Streamlit.")
        return ""
    try:
        risposta = client.models.generate_content(model=MODELLO, contents=prompt, config=_GENERA_CONFIG)
        return risposta.text
    except Exception as e:
        st.error(f"Errore API Gemini: {e}")
        return ""


# ── UI ────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Generatore DSA — AI per la Didattica Inclusiva",
    page_icon="📚",
    layout="wide",
)

st.markdown(
    """
    <style>
    .titolo { color: #2B5EA7; font-size: 2rem; font-weight: 800; }
    .sottotitolo { color: #E87722; font-size: 1rem; margin-bottom: 1.5rem; }
    .footer { color: #888; font-size: 0.8rem; margin-top: 3rem; border-top: 1px solid #eee; padding-top: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="titolo">📚 Generatore di Materiali Inclusivi</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sottotitolo">Demo gratuita — <em>Intelligenza Artificiale per la Didattica Inclusiva</em> di Gianluca Demontis</div>',
    unsafe_allow_html=True,
)

# ── SESSION STATE INIT ────────────────────────────────────────────────────────

if "contatore" not in st.session_state:
    st.session_state.contatore = 0
# fix 1: traccia identità file per evitare reset del text_area ad ogni rerun
if "file_id" not in st.session_state:
    st.session_state.file_id = None
if "testo_da_file" not in st.session_state:
    st.session_state.testo_da_file = ""

# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Profilo studente")
    st.markdown(
        "**Passo 1:** crea il profilo nel [Generatore Profili](https://generatore-profili-dsa.streamlit.app)  \n"
        "**Passo 2 di 2:** carica il .yaml qui sotto o seleziona un profilo esempio"
    )
    st.divider()
    nome_profilo = st.selectbox("Seleziona il profilo", list(PROFILI.keys()))
    profilo = PROFILI[nome_profilo].copy()

    if nome_profilo == "Profilo personalizzato...":
        max_parole = st.slider("Max parole per frase", 8, 30, 20)
        punti_blocco = st.slider("Punti per blocco", 2, 5, 3)
        istruzioni_custom = st.text_area(
            "Istruzioni specifiche",
            placeholder="Es. usa vocabolario di scuola media, aggiungi esempi pratici...",
            height=80,
        )
        profilo["max_parole_frase"] = max_parole
        profilo["punti_per_blocco"] = punti_blocco
        profilo["note"] = (
            f"Frasi brevi (max {max_parole} parole). "
            f"Max {punti_blocco} punti per blocco. "
            + (istruzioni_custom if istruzioni_custom else "Struttura chiara, glossario finale.")
        )

    note_extra = st.text_area(
        "Note aggiuntive (opzionale)",
        placeholder="Es. usa vocabolario di scuola media, aggiungi esempi di matematica...",
        height=80,
    )

    # ── Upload profilo personalizzato (.yaml) ──
    profilo_file = st.file_uploader(
        "Carica profilo personalizzato (.yaml)",
        type=["yaml", "yml"],
        help="Sovrascrive il profilo selezionato sopra con uno schema YAML completo.",
    )
    if profilo_file is not None:
        try:
            profilo_caricato = carica_profilo_da_bytes(profilo_file.read())
            if profilo_caricato:
                profilo = profilo_caricato
                nome_profilo = profilo_file.name
                st.success(f"Profilo caricato: {profilo_file.name}")
            else:
                st.warning("Il file YAML è vuoto: uso il profilo selezionato.")
        except Exception as e:
            st.error(f"YAML non valido: {e}")

    st.divider()

    tipo_quiz = st.selectbox(
        "Tipo quiz",
        ["A — Scelta multipla", "B — Vero/Falso", "C — Domande aperte"],
    )

    st.divider()
    rimanenti = MAX_RICHIESTE - st.session_state.contatore
    st.caption(f"Generazioni disponibili: {rimanenti}/{MAX_RICHIESTE}")
    if rimanenti == 0:
        st.warning("Limite demo raggiunto. Ricarica la pagina per ricominciare.")

# ── UPLOAD FILE ───────────────────────────────────────────────────────────────

file_caricato = st.file_uploader(
    "Carica un file da adattare (opzionale)",
    type=["txt", "docx"],
    help="Carica un file .txt o .docx oppure incolla il testo sotto.",
)

if file_caricato is not None:
    # fix 1: aggiorna session_state solo se è un file diverso dall'ultimo caricato
    file_id_corrente = (file_caricato.name, file_caricato.size)
    if file_id_corrente != st.session_state.file_id:
        st.session_state.file_id = file_id_corrente
        if file_caricato.name.endswith(".txt"):
            st.session_state.testo_da_file = file_caricato.read().decode("utf-8-sig")
        elif file_caricato.name.endswith(".docx"):
            try:
                from docx import Document
                doc = Document(file_caricato)
                st.session_state.testo_da_file = "\n".join(
                    p.text for p in doc.paragraphs if p.text.strip()
                )
            except ImportError:
                st.error("python-docx non installato. Aggiungi 'python-docx' ai requirements.")
                st.session_state.testo_da_file = ""
else:
    st.session_state.file_id = None
    st.session_state.testo_da_file = ""

testo_input = st.text_area(
    "Incolla qui il testo da adattare",
    value=st.session_state.testo_da_file,
    placeholder=TESTO_ESEMPIO,
    height=200,
)

# fix 5: warning e blocco se testo troppo lungo
n_chars = len(testo_input)
if n_chars > MAX_CHARS:
    st.warning(f"Testo troppo lungo ({n_chars:,} caratteri). Limite: {MAX_CHARS:,}. Accorcia il testo.")

col1, col2 = st.columns([1, 4])
with col1:
    genera_btn = st.button(
        "Genera materiale",
        type="primary",
        disabled=(
            st.session_state.contatore >= MAX_RICHIESTE
            or not testo_input.strip()
            or n_chars > MAX_CHARS
        ),
    )

# ── GENERAZIONE ───────────────────────────────────────────────────────────────

if genera_btn and testo_input.strip() and n_chars <= MAX_CHARS:
    if st.session_state.contatore >= MAX_RICHIESTE:
        st.warning("Limite demo raggiunto.")
    else:
        tipo_lettera = tipo_quiz[0]

        # fix 6: progress step-by-step
        progress = st.progress(0, text="Avvio generazione...")
        progress.progress(10, text="Generando testo adattato, infografica e slide (1-3/4)...")

        # fix 4: testo, infografica e slide in parallelo (sono indipendenti)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            fut_testo = executor.submit(genera, prompt_testo(testo_input, profilo, note_extra))
            fut_infografica = executor.submit(genera, prompt_infografica(testo_input, profilo))
            fut_slide = executor.submit(genera, prompt_slide(testo_input, profilo))
            testo_out = fut_testo.result()
            infografica_out = fut_infografica.result()
            slide_out = fut_slide.result()

        progress.progress(70, text="Generando quiz (4/5)...")
        # quiz dipende da testo_out, rimane sequenziale
        quiz_out = genera(prompt_quiz(testo_out, tipo_lettera)) if testo_out else ""

        progress.progress(88, text="Generando glossario PRO (5/5)...")
        # glossario PRO calibrato sul profilo, dipende dal testo adattato
        glossario_pro_out = (
            genera(prompt_glossario_pro(testo_out, profilo)) if testo_out else ""
        )

        progress.progress(100, text="Completato!")
        progress.empty()

        # fix 2: incrementa contatore solo se la generazione principale ha avuto successo
        if testo_out:
            st.session_state.contatore += 1
            st.session_state.risultati = {
                "testo": testo_out,
                "infografica": infografica_out,
                "slide": slide_out,
                "quiz": quiz_out,
                "glossario_pro": glossario_pro_out,
                "tipo_quiz": tipo_lettera,
                "profilo_nome": nome_profilo,  # fix 3: salva il profilo usato
                "profilo": profilo,            # serve per gli export DOCX/PPTX
            }
        else:
            st.error("Generazione fallita. Verifica la chiave API e riprova.")

# ── RISULTATI ─────────────────────────────────────────────────────────────────

if "risultati" in st.session_state and st.session_state.risultati.get("testo"):
    r = st.session_state.risultati
    profilo_export = r.get("profilo", {})
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Testo adattato", "Infografica", "Struttura slide", "Quiz", "Glossario PRO"]
    )

    with tab1:
        # fix 3: usa il profilo salvato al momento della generazione, non quello attuale
        st.subheader(f"Testo adattato — {r['profilo_nome']}")
        st.markdown(r["testo"])
        st.download_button(
            label="Scarica testo (.txt)",
            data=r["testo"],
            file_name="testo_adattato.txt",
            mime="text/plain",
        )
        if export_docx_bytes is not None:
            st.download_button(
                label="Scarica testo (.docx)",
                data=export_docx_bytes(r["testo"], profilo_export),
                file_name="testo_adattato.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

    with tab2:
        st.subheader("Struttura infografica")
        if r["infografica"]:
            st.markdown(r["infografica"])
            st.download_button(
                label="Scarica infografica (.txt)",
                data=r["infografica"],
                file_name="infografica.txt",
                mime="text/plain",
            )
        else:
            # fix 7: fallback output vuoto
            st.info("Infografica non disponibile per questa generazione.")

    with tab3:
        st.subheader("Struttura slide")
        if r["slide"]:
            st.markdown(r["slide"])
            st.download_button(
                label="Scarica slide (.txt)",
                data=r["slide"],
                file_name="slide.txt",
                mime="text/plain",
            )
            if export_pptx_bytes is not None:
                st.download_button(
                    label="Scarica slide (.pptx)",
                    data=export_pptx_bytes(r["slide"], profilo_export),
                    file_name="presentazione.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                )
        else:
            st.info("Struttura slide non disponibile per questa generazione.")

    with tab4:
        tipo_label = {"A": "Scelta multipla", "B": "Vero/Falso", "C": "Domande aperte"}
        st.subheader(f"Quiz — Tipo {r['tipo_quiz']} ({tipo_label.get(r['tipo_quiz'], '')})")
        if r["quiz"]:
            st.markdown(r["quiz"])
            st.download_button(
                label="Scarica quiz (.txt)",
                data=r["quiz"],
                file_name=f"quiz_tipo{r['tipo_quiz']}.txt",
                mime="text/plain",
            )
        else:
            # fix 7: fallback tab quiz vuota
            st.info("Quiz non disponibile. Verifica la chiave API e riprova la generazione.")

    with tab5:
        st.subheader("Glossario PRO — calibrato sul profilo")
        glossario_pro = r.get("glossario_pro", "")
        if glossario_pro:
            st.markdown(glossario_pro)
            st.download_button(
                label="Scarica glossario PRO (.txt)",
                data=glossario_pro,
                file_name="glossario_pro.txt",
                mime="text/plain",
            )
        else:
            st.info("Glossario PRO non disponibile per questa generazione.")

st.divider()
col_cta, col_profili = st.columns(2)
with col_cta:
    st.markdown(
        "📖 **Vuoi il sistema completo?** Il libro include tutti i prompt, i casi pratici "
        "Mario/Sofia/Lorenzo e il workflow settimanale.\n\n"
        "[→ Acquista su Amazon (9,99€)](https://amzn.to/434R6aA)",
    )
with col_profili:
    st.markdown(
        "👤 **Non hai ancora un profilo YAML?** Usa il Generatore Profili per creare "
        "il profilo operativo del tuo studente in 5 minuti.\n\n"
        "[→ Generatore Profili Studente](https://generatore-profili-dsa.streamlit.app)",
    )

st.markdown(
    '<div class="footer">'
    "Demo gratuita di <strong>Intelligenza Artificiale per la Didattica Inclusiva</strong> "
    "— <a href='https://gianlucademontis.xyz' target='_blank'>gianlucademontis.xyz</a> | "
    "<a href='https://amzn.to/434R6aA' target='_blank'>Acquista su Amazon</a>"
    "</div>",
    unsafe_allow_html=True,
)
