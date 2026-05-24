# Setup Generatore Pro — Chromebook con Crostini

---

## Metodo rapido (consigliato)

1. Scarica `generatore_chromebook.zip` da Google Drive
2. Sul Chromebook apri **File** → trascina il ZIP su **File Linux**
   (oppure: **Clic destro → Copia in File Linux**)
3. Apri il **Terminale Linux** e digita:

```bash
cd ~/Downloads    # o la cartella dove hai messo il file
unzip generatore_chromebook.zip -d ~/generatore-dsa
cd ~/generatore-dsa
bash install.sh
```

4. Quando richiesto, incolla la tua chiave API Gemini
5. Al termine usa i comandi mostrati nel riepilogo finale

---

## Prerequisiti

Linux (Crostini) deve essere attivo sul tuo Chromebook.
Se non lo hai ancora: **Impostazioni → Avanzate → Sviluppatori → Ambiente Linux → Attiva**.

---

## Cosa fa install.sh

1. Installa le dipendenze di sistema (python3-venv, python3-tk) via `apt`
2. Crea un ambiente virtuale Python in `.venv/`
3. Installa le librerie Python da `app/requirements_pro.txt`
4. Chiede la chiave API Gemini e la salva in `.env`
5. Crea tre script di avvio:
   - `avvia.sh` — GUI desktop Tkinter
   - `avvia_web.sh` — interfaccia web (apri `http://localhost:8501`)
   - `avvia_cli.sh` — riga di comando
6. Crea un collegamento sul Desktop Crostini (se presente)

---

## Avviare il programma

Dalla cartella `~/generatore-dsa/`:

| Comando | Descrizione |
|---|---|
| `bash avvia_web.sh` | Interfaccia web — apri `http://localhost:8501` nel browser |
| `bash avvia.sh` | GUI desktop Tkinter |
| `bash avvia_cli.sh --studente mario --testo testi/esempio_investiture.txt` | Riga di comando |

---

## Ottenere la chiave API Gemini (gratuita)

1. Vai su **aistudio.google.com/apikey** dal browser
2. Accedi con il tuo account Google
3. Clic su "Create API key"
4. Copia la chiave (inizia con `AIza...`)

La chiave viene salvata in `.env` e non viene mai inclusa nel codice.

---

## Aprire i file generati

I file sono nella cartella `output/`:

- `.docx` → trascina su Drive per aprire con Google Docs, oppure `libreoffice --writer`
- `.pptx` → trascina su Drive per aprire con Google Slides, oppure `libreoffice --impress`
- `.txt` → apri con qualsiasi editor di testo

Dal **File Manager** del Chromebook trovi i file Linux in "File Linux".

---

## Installazione manuale (senza install.sh)

Se preferisci:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-tk
cd ~/generatore-dsa
python3 -m venv .venv
.venv/bin/pip install -r app/requirements_pro.txt
echo "GEMINI_API_KEY=AIza...la_tua_chiave" > .env
```

---

## Problemi comuni

**`bash install.sh` — permission denied**
```bash
chmod +x install.sh && bash install.sh
```

**`python3-venv` non disponibile**
```bash
sudo apt-get install python3-venv -y
```

**Errore Gemini 429 (quota superata)**
Il piano gratuito ha 15 richieste/minuto. Aspetta 1 minuto e riprova.

**Video: `ffmpeg not found`**
```bash
sudo apt-get install ffmpeg -y
```

**File .docx non si apre**
```bash
sudo apt-get install libreoffice -y
```

---

## Funzioni Pro opzionali

### Video esplicativo (F.5)

Richiede credenziali Google Cloud Text-to-Speech:

1. Vai su **console.cloud.google.com**
2. Abilita **Cloud Text-to-Speech API**
3. Crea credenziali → Service Account → scarica il file JSON
4. Nel terminale:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=~/generatore-dsa/tts-credentials.json
```
Aggiungi questa riga a `~/.bashrc` per renderla permanente.

### Google Classroom (F.3)

1. Vai su **console.cloud.google.com**
2. Abilita **Google Classroom API** e **Google Drive API**
3. Crea credenziali → OAuth 2.0 → Applicazione desktop
4. Scarica `credentials.json` nella cartella `~/generatore-dsa/`
5. Aggiungi l'ID corso nel profilo YAML:
```yaml
classroom_course_id: "123456789"  # da classroom.google.com → URL del corso
```

---

## Aggiornamento futura versione

Scarica il nuovo ZIP, estrailo nella stessa cartella:
```bash
unzip -o generatore_chromebook_vX.Y.zip -d ~/generatore-dsa
cd ~/generatore-dsa
bash install.sh
```
Il file `.env` con la chiave API non viene sovrascritto.
