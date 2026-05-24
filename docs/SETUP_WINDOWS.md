# Setup Generatore Pro — Windows 10 / 11

---

## Metodo rapido (consigliato)

1. Scarica `generatore_windows.zip` da Google Drive
2. Estrai la cartella dove vuoi (es. `C:\Users\TuoNome\generatore-dsa\`)
3. Apri la cartella estratta
4. Doppio clic su **`install.bat`**
5. Quando richiesto, incolla la tua chiave API Gemini
6. Al termine usa i lanciatori nella stessa cartella

---

## Prerequisiti

### Python 3.9 o superiore

Verifica se è già installato — apri **PowerShell** o **cmd** e digita:

```
python --version
```

Se non è installato o la versione è troppo vecchia:

1. Vai su **python.org/downloads**
2. Scarica l'installer Windows (`.exe`)
3. Durante l'installazione spunta **"Add Python to PATH"** — obbligatorio
4. Clicca "Install Now"

---

## Installazione manuale (alternativa al .bat)

Se preferisci controllare ogni passo:

```cmd
REM Apri cmd nella cartella estratta (tasto destro → "Apri nel terminale")

python -m venv .venv
.venv\Scripts\pip install -r app\requirements_pro.txt
```

Crea il file `.env` con la chiave API:

```cmd
echo GEMINI_API_KEY=AIza...la_tua_chiave> .env
```

---

## Avviare il programma

Dopo l'installazione hai tre modi:

| Lanciatore | Descrizione |
|---|---|
| `avvia_web.bat` | Apre il browser su `http://localhost:8501` — interfaccia web completa |
| `avvia_gui.bat` | Avvia la GUI desktop Tkinter |
| `avvia_cli.bat` | Interfaccia da riga di comando |

Doppio clic sul file `.bat` scelto. Per l'interfaccia web, apri il browser
su `http://localhost:8501` quando il terminale mostra "You can now view...".

---

## Ottenere la chiave API Gemini (gratuita)

1. Vai su **aistudio.google.com/apikey**
2. Accedi con il tuo account Google
3. Clic su "Create API key"
4. Copia la chiave (inizia con `AIza...`)

La chiave viene salvata in `.env` e non viene mai inclusa nel codice.

---

## Aprire i file generati

I file sono nella cartella `output\`:

- `.docx` → apri con **Word** o **Google Docs** (carica su Drive)
- `.pptx` → apri con **PowerPoint** o **Google Slides**
- `.txt` → apri con Blocco Note o qualsiasi editor

---

## Problemi comuni

**`python` non riconosciuto**
Reinstalla Python spuntando "Add Python to PATH". Poi riapri cmd.

**`ModuleNotFoundError`**
Il venv non è attivo. Usa sempre i file `.bat` che lo attivano automaticamente.

**Errore Gemini 429 (quota superata)**
Il piano gratuito ha 15 richieste/minuto. Aspetta 1 minuto e riprova.

**`pip install` lento o bloccato**
Può capitare con connessioni lente. Aggiungi `--timeout 120` al comando pip.

**Antivirus blocca il .bat**
I file `.bat` da fonti sconosciute possono essere bloccati. Clic destro →
"Proprietà" → "Sblocca", poi riesegui.

---

## Aggiornamento futura versione

Scarica il nuovo ZIP, estrailo nella stessa cartella (sovrascrivendo i file),
poi riesegui `install.bat`. Il file `.env` con la chiave API non viene toccato.
