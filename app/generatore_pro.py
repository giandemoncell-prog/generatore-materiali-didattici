# generatore_pro.py — Generatore di materiali didattici inclusivi (versione Pro)
# Include: testo adattato, infografica, slide, glossario calibrato,
#          quiz (A/B/C), registro qualità, integrazione Classroom, video
#
# Uso base (Gemini, richiede API key):
#   python generatore_pro.py --studente mario --testo testi/storia.txt
#
# Uso con modello locale Ollama (gratis, offline, nessuna chiave API):
#   python generatore_pro.py --studente mario --testo testi/storia.txt --backend ollama
#   python generatore_pro.py --studente mario --testo testi/storia.txt --backend ollama --modello-ollama glm-4.7-flash
#
# Con feature Pro:
#   python generatore_pro.py --studente mario --testo testi/storia.txt --glossario-pro
#   python generatore_pro.py --studente mario --testo testi/storia.txt --quiz
#   python generatore_pro.py --studente mario --testo testi/storia.txt --quiz=B
#   python generatore_pro.py --studente mario --testo testi/storia.txt --classroom
#   python generatore_pro.py --studente mario --testo testi/storia.txt --video
#
# Verifica il modello attivo su: aistudio.google.com/models
# Modelli locali disponibili: ollama list

import os
import sys
import csv
import yaml
import argparse
import concurrent.futures
import requests
from typing import Any
from google import genai
from google.genai import types as _genai_types
from docx import Document
from docx.shared import Pt
from pptx import Presentation
from pptx.util import Inches, Pt as PptPt
from datetime import datetime
from pathlib import Path

_GENERA_CONFIG = _genai_types.GenerateContentConfig(temperature=0.7, max_output_tokens=8192)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELLO_OLLAMA_DEFAULT = "qwen3.6:27b"  # alternative locali: glm-4.7-flash, ministral-3:8b, qwen3.5:4b


class _RispostaOllama:
    """Imita l'oggetto risposta di google-genai (.text) per riuso di genera_contenuto()."""
    def __init__(self, text: str):
        self.text = text


class _OllamaModelsNamespace:
    """Imita l'attributo .models di genai.Client, stessa firma di generate_content()."""
    def __init__(self, nome_modello: str):
        self.nome_modello = nome_modello

    def generate_content(self, model=None, contents=None, config=None) -> _RispostaOllama:
        # "model"/"config" arrivano dalla firma Gemini e vengono ignorati: il modello
        # locale è quello scelto con --modello-ollama.
        risposta = requests.post(
            OLLAMA_URL,
            json={"model": self.nome_modello, "prompt": contents, "stream": False},
            timeout=600,
        )
        risposta.raise_for_status()
        return _RispostaOllama(risposta.json().get("response", ""))


class ModelloOllama:
    """Backend locale via Ollama — stessa interfaccia di genai.Client (.models.generate_content).

    I dati degli studenti (profili PDP/PEI) restano in locale, senza inviarli a
    un'API esterna: privacy migliore rispetto a Gemini per contenuti sensibili.
    Richiede Ollama attivo in locale.
    """
    def __init__(self, nome_modello: str = MODELLO_OLLAMA_DEFAULT):
        self.models = _OllamaModelsNamespace(nome_modello)

# ─── RETROCOMPATIBILITÀ CORE ──────────────────────────────────────────────────
# Preferisci i moduli condivisi in core/ quando importabili (es. eseguendo da app/).
# Le definizioni locali più sotto restano come fallback se core/ non è disponibile.
# Nota: le funzioni del core vengono ri-associate in fondo al modulo (vedi blocco
# "OVERRIDE CORE"), così le firme locali fanno comunque da fallback statico.
try:
    from core.config import MODELLO_GEMINI as _CORE_MODELLO_GEMINI
    from core.prompts import prompt_testo, prompt_infografica, prompt_slide, prompt_quiz  # noqa: F401
    from core.exporters import (
        salva_testo_docx as _core_salva_testo_docx,
        salva_slide_pptx as _core_salva_slide_pptx,
    )
    from core.profiles import (
        carica_profilo as _core_carica_profilo,
        costruisci_istruzioni,
    )
    _CORE_AVAILABLE = True
except ImportError:
    _CORE_AVAILABLE = False


# ─── CONFIGURAZIONE ───────────────────────────────────────────────────────────

if _CORE_AVAILABLE:
    MODELLO_GEMINI = _CORE_MODELLO_GEMINI
else:
    MODELLO_GEMINI = "gemini-2.5-flash"  # aggiorna se obsoleto: aistudio.google.com/models

    def costruisci_istruzioni(profilo: dict) -> str:  # type: ignore[misc]
        from core.config import MAX_PAROLE_FRASE_DEFAULT
        p = profilo.get("presentazione", {}) or {}
        difficolta = profilo.get("profilo_cognitivo", {}).get("aree_difficolta", {}) or {}
        note = profilo.get("note_osservazioni", []) or []
        max_p = profilo.get("max_parole_frase", MAX_PAROLE_FRASE_DEFAULT)
        istr = []
        if difficolta.get("lettura"):
            istr.append(f"Usa frasi brevi (max {max_p} parole). Evita subordinate complesse.")
        if difficolta.get("memoria_di_lavoro"):
            istr.append("Un concetto per paragrafo.")
        if difficolta.get("scrittura"):
            istr.append("Usa elenchi puntati invece di paragrafi continui.")
        istr += [
            f"Ogni blocco: massimo {p.get('max_punti_per_slide', 3)} punti elenco.",
            f"Ogni paragrafo: massimo {p.get('max_righe_paragrafo', 4)} righe.",
            "Evidenzia in grassetto le parole chiave (max 3 per paragrafo).",
            "Usa corsivo per i termini tecnici alla prima occorrenza.",
        ]
        for nota in note:
            if nota:
                istr.append(str(nota))
        if not istr:
            istr.append(f"Adattamento standard. Frasi brevi (max {max_p} parole), struttura chiara.")
        return "\n".join(f"- {i}" for i in istr)


def carica_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        try:
            with open(".env") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        key = line.split("=", 1)[1].strip()
        except FileNotFoundError:
            pass
    if not key:
        sys.exit(
            "Errore: chiave API Gemini non trovata.\n"
            "Crea un file .env con: GEMINI_API_KEY=la_tua_chiave\n"
            "Ottieni la chiave su: aistudio.google.com/apikey"
        )
    return key


def carica_profilo(nome_studente: str) -> dict:
    percorso = f"profili/profilo_{nome_studente.lower().replace(' ', '_')}.yaml"
    try:
        with open(percorso, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        sys.exit(f"Errore: profilo non trovato in {percorso}")


def carica_testo(percorso_testo: str) -> str:
    try:
        with open(percorso_testo, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        sys.exit(f"Errore: file testo non trovato: {percorso_testo}")


# ─── COSTRUZIONE PROMPT ───────────────────────────────────────────────────────

def costruisci_prompt_testo(testo: str, istruzioni: str) -> str:
    return f"""Sei un esperto di didattica inclusiva per studenti con DSA e BES.
Adatta il seguente testo didattico rispettando TUTTE queste regole:

{istruzioni}

Produci:
1. Una versione adattata del testo (mantieni TUTTI i concetti, cambia solo la forma)
2. Un glossario con le 6-8 parole più difficili, con definizione semplice

Formato risposta:
---TESTO ADATTATO---
[testo qui]
---GLOSSARIO---
termine: definizione
termine: definizione

TESTO ORIGINALE DA ADATTARE:
{testo}"""


def costruisci_prompt_infografica(testo: str, istruzioni: str) -> str:
    return f"""Sei un esperto di didattica inclusiva. Crea un'infografica testuale dal testo seguente.

Regole:
{istruzioni}
- Identifica 3-5 concetti principali
- Per ogni concetto: titolo breve (max 5 parole) + 2-3 punti elenco
- Suggerisci un'immagine descrittiva per ogni blocco
- Aggiungi titolo generale e glossario finale con 6 termini chiave

Formato risposta:
---TITOLO---
[titolo infografica]
---BLOCCO 1---
TITOLO: [titolo]
IMMAGINE: [descrizione immagine]
• punto 1
• punto 2
[ripeti per ogni blocco]
---GLOSSARIO---
termine: definizione breve

TESTO:
{testo}"""


def costruisci_prompt_slide(testo: str, istruzioni: str) -> str:
    return f"""Crea una presentazione didattica dal testo seguente per studenti con DSA.

Regole:
{istruzioni}
- Slide 1: titolo + materia
- Slide 2: "Cosa impariamo oggi" con 3 obiettivi
- Slide 3-N: una slide per concetto (titolo + max 3 punti + descrizione immagine)
- Penultima slide: mappa concettuale testuale
- Ultima slide: 5-8 parole chiave con definizione

Formato risposta:
---SLIDE 1---
TITOLO: [titolo]
SOTTOTITOLO: [materia e classe]
---SLIDE 2---
TITOLO: Cosa impariamo oggi
• obiettivo 1
• obiettivo 2
• obiettivo 3
---SLIDE N---
TITOLO: [titolo]
IMMAGINE: [descrizione]
• punto 1
• punto 2
• punto 3
[continua]

TESTO:
{testo}"""


# ─── PROMPT PRO ───────────────────────────────────────────────────────────────

def costruisci_prompt_glossario_pro(testo_adattato: str, profilo: dict) -> str:
    livello = profilo.get("profilo_cognitivo", {}).get(
        "aree_difficolta", {}
    ).get("lettura", "media")
    return f"""Analizza questo testo già semplificato per uno studente con difficoltà di lettura ({livello}).

Identifica le 8 parole o espressioni che questo studente potrebbe ancora trovare difficili.
Non solo i termini tecnici — anche parole comuni che richiedono un vocabolario medio-alto.

Per ogni parola restituisci:
TERMINE: [parola]
DEFINIZIONE: [spiegazione in massimo 15 parole, livello elementare]
ESEMPIO: [frase breve che usa la parola in contesto]
IMMAGINE: [descrizione di un'immagine che aiuta a ricordare il significato]

TESTO:
{testo_adattato}"""


def costruisci_prompt_quiz(testo_adattato: str, tipo: str = "A") -> str:
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


# ─── GENERAZIONE ──────────────────────────────────────────────────────────────

def genera_contenuto(prompt: str, model: Any) -> str:
    try:
        risposta = model.models.generate_content(
            model=MODELLO_GEMINI, contents=prompt, config=_GENERA_CONFIG
        )
        return risposta.text
    except Exception as e:
        print(f"Errore generazione contenuto: {e}")
        return ""


# ─── SALVATAGGIO OUTPUT ───────────────────────────────────────────────────────

def salva_testo_docx(contenuto: str, profilo: dict, percorso: str) -> None:
    doc = Document()
    p = profilo.get("presentazione", {})
    font_nome = p.get("font", "Arial").split()[0]
    stile = doc.styles["Normal"]
    stile.font.name = font_nome
    stile.font.size = Pt(12)

    sezioni = contenuto.split("---")
    testo_corrente = ""
    glossario_corrente = ""
    in_glossario = False

    for sezione in sezioni:
        s = sezione.strip()
        if s == "TESTO ADATTATO":
            in_glossario = False
        elif s == "GLOSSARIO":
            in_glossario = True
        elif s:
            if in_glossario:
                glossario_corrente = s
            else:
                testo_corrente = s

    for riga in testo_corrente.split("\n"):
        if riga.strip():
            para = doc.add_paragraph(riga)
            para.paragraph_format.space_after = Pt(6)

    if glossario_corrente:
        doc.add_paragraph()
        heading = doc.add_paragraph("Parole chiave")
        heading.style = doc.styles["Heading 2"]
        for voce in glossario_corrente.split("\n"):
            if ":" in voce:
                termine, defin = voce.split(":", 1)
                para = doc.add_paragraph()
                run_t = para.add_run(termine.strip() + ": ")
                run_t.bold = True
                para.add_run(defin.strip())

    doc.save(percorso)
    print(f"  Salvato: {percorso}")


def salva_slide_pptx(contenuto: str, profilo: dict, percorso: str) -> None:
    prs = Presentation()
    p = profilo.get("presentazione", {})
    font_nome = p.get("font", "Arial").split()[0]
    layout_vuoto = prs.slide_layouts[6]

    for blocco in contenuto.split("---SLIDE"):
        blocco = blocco.strip()
        if not blocco or blocco.isdigit():
            continue

        linee = [riga.strip() for riga in blocco.split("\n") if riga.strip()]
        titolo = ""
        punti = []

        for linea in linee:
            if linea.startswith("TITOLO:"):
                titolo = linea.replace("TITOLO:", "").strip()
            elif linea.startswith("IMMAGINE:"):
                pass
            elif linea.startswith(("•", "-")):
                punti.append(linea.lstrip("•- ").strip())
            elif linea.startswith("SOTTOTITOLO:"):
                punti.insert(0, linea.replace("SOTTOTITOLO:", "").strip())

        if not titolo:
            continue

        slide = prs.slides.add_slide(layout_vuoto)
        tb = slide.shapes.add_textbox(Inches(0.3), Inches(0.2), Inches(9), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p_titolo = tf.paragraphs[0]
        p_titolo.text = titolo
        if p_titolo.runs:
            p_titolo.runs[0].font.size = PptPt(28)
            p_titolo.runs[0].font.bold = True
            p_titolo.runs[0].font.name = font_nome

        if punti:
            tb2 = slide.shapes.add_textbox(Inches(0.3), Inches(1.5), Inches(9), Inches(5))
            tf2 = tb2.text_frame
            tf2.word_wrap = True
            for i, punto in enumerate(punti[:3]):
                para = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
                para.text = f"• {punto}"
                if para.runs:
                    para.runs[0].font.size = PptPt(18)
                    para.runs[0].font.name = font_nome

    prs.save(percorso)
    print(f"  Salvato: {percorso}")


def salva_testo_txt(contenuto: str, percorso: str) -> None:
    with open(percorso, "w", encoding="utf-8") as f:
        f.write(contenuto)
    print(f"  Salvato: {percorso}")


# ─── REGISTRO QUALITÀ (F.4) ───────────────────────────────────────────────────

def aggiorna_registro(studente: str, testo: str, cartella_out: str) -> None:
    registro = Path("output/registro_qualita.csv")
    registro.parent.mkdir(exist_ok=True)
    intestazione = [
        "data", "studente", "file_testo", "cartella_output",
        "testo_ok", "infografica_ok", "slide_ok", "note"
    ]
    esiste = registro.exists()
    with open(registro, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not esiste:
            writer.writerow(intestazione)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            studente, testo, cartella_out,
            "", "", "", ""
        ])
    print(f"  Registro aggiornato: {registro}")


# ─── GOOGLE CLASSROOM (F.3) ───────────────────────────────────────────────────

def _autentica_google():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        sys.exit(
            "Librerie Classroom mancanti. Esegui:\n"
            "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        )

    SCOPES = [
        "https://www.googleapis.com/auth/classroom.coursework.students",
        "https://www.googleapis.com/auth/classroom.materials",
        "https://www.googleapis.com/auth/drive.file",
    ]

    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if not os.path.exists("credentials.json"):
            sys.exit(
                "File credentials.json non trovato.\n"
                "Scaricalo da: console.cloud.google.com → API → Credenziali → OAuth 2.0"
            )
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        # Su Chromebook: apre il browser per l'autenticazione OAuth
        try:
            creds = flow.run_local_server(port=0)
        except Exception:
            # Fallback console per ambienti senza browser locale
            creds = flow.run_console()
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def pubblica_su_classroom(cartella_out: str, titolo: str, course_id: str):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    print("  Autenticazione Google...")
    creds = _autentica_google()
    drive = build("drive", "v3", credentials=creds)
    classroom = build("classroom", "v1", credentials=creds)

    file_ids = []
    for nome_file in ["testo_adattato.docx", "presentazione.pptx"]:
        percorso = os.path.join(cartella_out, nome_file)
        if os.path.exists(percorso):
            print(f"  Carico su Drive: {nome_file}...")
            metadata = {"name": nome_file}
            media = MediaFileUpload(percorso, resumable=True)
            file_drive = drive.files().create(
                body=metadata, media_body=media, fields="id"
            ).execute()
            file_ids.append(file_drive.get("id"))

    if file_ids:
        materiali = [
            {"driveFile": {"driveFile": {"id": fid}, "shareMode": "VIEW"}}
            for fid in file_ids
        ]
        corpo = {"title": titolo, "materials": materiali, "state": "PUBLISHED"}
        classroom.courses().courseWorkMaterials().create(
            courseId=course_id, body=corpo
        ).execute()
        print(f"  Pubblicato su Classroom: '{titolo}'")


# ─── VIDEO (F.5) ──────────────────────────────────────────────────────────────

def genera_video(testo_adattato: str, cartella_out: str):
    try:
        from google.cloud import texttospeech
        from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print(
            "  Librerie video mancanti. Esegui:\n"
            "  pip install google-cloud-texttospeech moviepy pillow\n"
            "  sudo apt-get install ffmpeg  (Linux/Chromebook)"
        )
        return

    print("  Genero audio con Text-to-Speech...")
    percorso_audio = os.path.join(cartella_out, "narrazione.mp3")
    client = texttospeech.TextToSpeechClient()
    input_tts = texttospeech.SynthesisInput(text=testo_adattato[:5000])
    voce = texttospeech.VoiceSelectionParams(
        language_code="it-IT",
        name="it-IT-Standard-A",
    )
    config_audio = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    risposta = client.synthesize_speech(
        input=input_tts, voice=voce, audio_config=config_audio
    )
    with open(percorso_audio, "wb") as f:
        f.write(risposta.audio_content)

    # Crea slide immagini da paragrafi del testo
    print("  Genero slide immagini...")
    cartella_slide = os.path.join(cartella_out, "slide_video")
    os.makedirs(cartella_slide, exist_ok=True)

    paragrafi = [p.strip() for p in testo_adattato.split("\n\n") if p.strip()][:8]
    for i, para in enumerate(paragrafi):
        img = Image.new("RGB", (1280, 720), color="#FFFFFF")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        except Exception:
            font = ImageFont.load_default()
        # Testo con wrap manuale
        parole = para.split()
        righe = []
        riga = ""
        for parola in parole:
            if len(riga + parola) < 45:
                riga += parola + " "
            else:
                righe.append(riga.strip())
                riga = parola + " "
        if riga:
            righe.append(riga.strip())
        y = 200
        for r in righe[:8]:
            draw.text((80, y), r, fill="#1a1a1a", font=font)
            y += 55
        img.save(os.path.join(cartella_slide, f"slide_{i:02d}.png"))

    print("  Compongo il video...")
    audio = AudioFileClip(percorso_audio)
    nomi_slide = sorted(
        f for f in os.listdir(cartella_slide) if f.endswith(".png")
    )
    if not nomi_slide:
        print("  Errore: nessuna slide generata.")
        return

    durata = audio.duration / len(nomi_slide)
    clips = [
        ImageClip(os.path.join(cartella_slide, s)).with_duration(durata)
        for s in nomi_slide
    ]
    video = concatenate_videoclips(clips).with_audio(audio)
    percorso_video = os.path.join(cartella_out, "video_esplicativo.mp4")
    video.write_videofile(percorso_video, fps=1, logger=None)
    print(f"  Salvato: {percorso_video}")


# ─── OVERRIDE CORE ─────────────────────────────────────────────────────────────
# Se il package core è disponibile, le sue implementazioni sostituiscono quelle
# locali (che restano definite sopra come fallback statico per ambienti senza core).
if _CORE_AVAILABLE:
    carica_profilo = _core_carica_profilo            # noqa: F811
    salva_testo_docx = _core_salva_testo_docx        # noqa: F811
    salva_slide_pptx = _core_salva_slide_pptx        # noqa: F811


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generatore di materiali didattici inclusivi — versione Pro"
    )
    parser.add_argument("--studente", required=True,
                        help="Nome del profilo studente (es. 'mario')")
    parser.add_argument("--testo", required=True,
                        help="Percorso del file testo da adattare")
    parser.add_argument("--nota", default="",
                        help="Istruzione aggiuntiva per questa elaborazione")
    parser.add_argument("--tag", default="",
                        help="Etichetta per i file di output (es. 'lotta-investiture')")
    parser.add_argument("--glossario-pro", action="store_true",
                        help="Genera glossario calibrato sul profilo (F.1)")
    parser.add_argument("--quiz", nargs="?", const="A",
                        help="Genera quiz: A (multipla), B (vero/falso), C (aperte)")
    parser.add_argument("--classroom", action="store_true",
                        help="Pubblica su Google Classroom (F.3)")
    parser.add_argument("--video", action="store_true",
                        help="Genera video con voce narrante (F.5)")
    parser.add_argument("--backend", choices=["gemini", "ollama"], default="gemini",
                        help="Motore AI: 'gemini' (API, default) o 'ollama' (locale, gratis, offline)")
    parser.add_argument("--modello-ollama", default=MODELLO_OLLAMA_DEFAULT,
                        help=f"Modello Ollama da usare con --backend ollama (default: {MODELLO_OLLAMA_DEFAULT})")
    args = parser.parse_args()

    print(f"\n=== Generatore da Profili AI — studente: {args.studente} ===\n")

    try:
        profilo = carica_profilo(args.studente)
    except FileNotFoundError:
        sys.exit(
            f"Errore: profilo non trovato in "
            f"profili/profilo_{args.studente.lower().replace(' ', '_')}.yaml"
        )
    testo = carica_testo(args.testo)

    if args.backend == "ollama":
        print(f"Backend: Ollama locale ({args.modello_ollama}) — nessuna chiave API richiesta\n")
        model = ModelloOllama(args.modello_ollama)
    else:
        api_key = carica_api_key()
        model = genai.Client(api_key=api_key)

    istruzioni = costruisci_istruzioni(profilo)
    if args.nota:
        istruzioni += f"\n- {args.nota}"

    data_oggi = datetime.now().strftime("%Y-%m-%d")
    nome_studente = args.studente.lower().replace(" ", "_")
    suffisso = f"_{args.tag}" if args.tag else ""
    cartella_out = f"output/{nome_studente}/{data_oggi}{suffisso}"
    os.makedirs(cartella_out, exist_ok=True)

    # BASE: testo, infografica e slide in parallelo
    print("Genero testo adattato, infografica e slide in parallelo...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        fut_testo = executor.submit(genera_contenuto, costruisci_prompt_testo(testo, istruzioni), model)
        fut_infografica = executor.submit(genera_contenuto, costruisci_prompt_infografica(testo, istruzioni), model)
        fut_slide = executor.submit(genera_contenuto, costruisci_prompt_slide(testo, istruzioni), model)
        testo_adattato_raw = fut_testo.result()
        infografica = fut_infografica.result()
        slide_content = fut_slide.result()

    salva_testo_docx(testo_adattato_raw, profilo, f"{cartella_out}/testo_adattato.docx")
    salva_testo_txt(infografica, f"{cartella_out}/infografica.txt")
    salva_slide_pptx(slide_content, profilo, f"{cartella_out}/presentazione.pptx")

    # PRO F.1: glossario calibrato
    if args.glossario_pro:
        print("\n[Pro] Genero il glossario calibrato...")
        glossario_pro = genera_contenuto(
            costruisci_prompt_glossario_pro(testo_adattato_raw, profilo), model
        )
        salva_testo_txt(glossario_pro, f"{cartella_out}/glossario_pro.txt")

    # PRO F.2: quiz
    if args.quiz:
        tipo_quiz = args.quiz.upper() if args.quiz else "A"
        print(f"\n[Pro] Genero il quiz tipo {tipo_quiz}...")
        quiz = genera_contenuto(costruisci_prompt_quiz(testo_adattato_raw, tipo_quiz), model)
        salva_testo_txt(quiz, f"{cartella_out}/quiz_tipo{tipo_quiz}.txt")

    # PRO F.4: registro qualità (sempre attivo)
    aggiorna_registro(args.studente, args.testo, cartella_out)

    # PRO F.3: Google Classroom
    if args.classroom:
        course_id = profilo.get("identificativo", {}).get("classroom_course_id", "")
        if not course_id:
            print("\n[Pro] Classroom: aggiungi classroom_course_id al profilo YAML.")
        else:
            titolo = f"Materiali {args.studente} — {args.tag or data_oggi}"
            print(f"\n[Pro] Pubblico su Classroom (corso {course_id})...")
            pubblica_su_classroom(cartella_out, titolo, course_id)

    # PRO F.5: video
    if args.video:
        print("\n[Pro] Genero il video esplicativo...")
        testo_pulito = "\n\n".join(
            r for r in testo_adattato_raw.split("\n")
            if r.strip() and not r.startswith("---")
        )
        genera_video(testo_pulito, cartella_out)

    print(f"\n✓ Completato. File in: {cartella_out}/")
    files = list(Path(cartella_out).glob("*"))
    for f in sorted(files):
        if f.name != "slide_video":
            print(f"  • {f.name}")


if __name__ == "__main__":
    main()
