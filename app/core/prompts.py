# core/prompts.py — Costruzione dei prompt per Gemini (consolidata).
#
# Consolida le funzioni prompt prima duplicate in generatore_pro.py e
# streamlit_demo.py. Ogni funzione accetta un `profilo: dict` e deriva il blocco
# istruzioni tramite core.profiles.costruisci_istruzioni.
#
# Modulo foglia: importa solo da core.profiles (che a sua volta importa da config).

from __future__ import annotations

from .profiles import costruisci_istruzioni


def prompt_testo(testo: str, profilo: dict, note_extra: str = "") -> str:
    """Prompt per il testo adattato + glossario.

    Contiene i marker ``---TESTO ADATTATO---`` e ``---GLOSSARIO---``.
    """
    istruzioni = costruisci_istruzioni(profilo)
    if note_extra:
        istruzioni += f"\n- {note_extra}"
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


def prompt_infografica(testo: str, profilo: dict) -> str:
    """Prompt per l'infografica testuale.

    Contiene i marker ``---TITOLO---``, ``---BLOCCO 1---`` e una sezione glossario.
    """
    istruzioni = costruisci_istruzioni(profilo)
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


def prompt_slide(testo: str, profilo: dict) -> str:
    """Prompt per la struttura della presentazione.

    Contiene i marker ``---SLIDE 1---``, ``---SLIDE 2---``, ``---SLIDE N---`` e
    la sezione "Cosa impariamo oggi".
    """
    istruzioni = costruisci_istruzioni(profilo)
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


def prompt_quiz(testo_adattato: str, tipo: str = "A") -> str:
    """Prompt per il quiz di verifica.

    Args:
        testo_adattato: testo già semplificato su cui basare il quiz.
        tipo: "A" (scelta multipla), "B" (Vero/Falso), "C" (domande aperte).
              Tipo sconosciuto -> fallback alle istruzioni di "A".

    Contiene ``Tipo di quiz: {tipo}`` e la sezione ``SOLUZIONI``.
    """
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


def prompt_glossario_pro(testo_adattato: str, profilo: dict) -> str:
    """Prompt per il glossario PRO calibrato sul profilo.

    Contiene i campi ``TERMINE:``, ``DEFINIZIONE:``, ``ESEMPIO:``, ``IMMAGINE:``
    e fa riferimento al livello di difficoltà di lettura del profilo.
    """
    profilo = profilo or {}
    livello = (
        profilo.get("profilo_cognitivo", {})
        .get("aree_difficolta", {})
        .get("lettura", "media")
    )
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
